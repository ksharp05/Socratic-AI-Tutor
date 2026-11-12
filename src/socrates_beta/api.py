from __future__ import annotations
import hashlib,hmac,json,secrets,time,uuid,os,re
from pathlib import Path
from typing import Literal
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel,ConfigDict,Field
from . import __version__
from .bootstrap import bootstrap
from .repository import Repository,BetaBusy
from .ports import Scope
from .dialogue import DialogueService
from .safety import clean_text,redact_personal_data
from .maths import CheckedMaths,AssessmentService
from .study import StudyService
from .transport import BrowserTransport

ROOT=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path(__file__).resolve().parents[2])).resolve()


class Closed(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class SessionIn(Closed):
    grade:int=Field(ge=8,le=12);subject:str=Field(min_length=1,max_length=80)
    dataset_id:str|None=None;book:str|None=None;unit:int|None=Field(default=None,ge=1,le=99)
    title:str=Field(default='A new idea',max_length=140)
class ChatIn(Closed):
    session_id:str=Field(min_length=20,max_length=64);text:str=Field(min_length=1,max_length=2000)
    request_id:str=Field(min_length=8,max_length=80)
class StartIn(Closed):
    session_id:str;mode:Literal['practice','diagnostic','quiz']='practice';concept:str|None=None;question_id:str|None=None
class SubmitIn(Closed):
    answer:str=Field(min_length=1,max_length=512);request_id:str=Field(min_length=8,max_length=80)
class CardIn(Closed):session_id:str;passage_id:str
class ReviewIn(Closed):rating:Literal['again','hard','good','easy']
class PrefsIn(Closed):
    grade:int=Field(ge=8,le=12);subject:str=Field(min_length=1,max_length=80)
    goal:str=Field(default='Understand the topic',max_length=160);minutes:int=Field(default=25,ge=10,le=120)
    model_consent:bool=False


def create_app(config: Path|dict|None=None,*,live=False,language=None,registry=None,repository=None,maths=None,testing=False,tutor_provider=None,browser_secret=None):
    settings=json.loads(Path(config or ROOT/'config/beta/local.json').read_text(encoding='utf-8-sig')) if not isinstance(config,dict) else config
    transport=BrowserTransport.configured(settings.get('public_origin'),testing=testing,additional_origins=settings.get('additional_origins',()))
    if settings.get('assessment_policy') not in (None,'reference_checked_beta'):
        raise ValueError('Unknown beta assessment policy')
    data=Path(settings.get('data_directory','Directions/beta_data'))
    if not data.is_absolute():data=ROOT/data
    data.mkdir(parents=True,exist_ok=True)
    app_root=Path(settings.get('app_root',ROOT.with_name('Socratic Tutor Main')))
    if not app_root.is_absolute():app_root=(Path(__file__).resolve().parents[2]/app_root).resolve()
    registry=registry or bootstrap(ROOT,app_root,data)
    if settings.get('assessment_policy')=='reference_checked_beta':
        from .reference_notes import SupplementedRegistry
        registry=SupplementedRegistry(registry,app_root)
    repo=repository or Repository(data/'beta.sqlite')
    if live and language is None:
        from .language import TeamLanguage
        language=TeamLanguage(app_root,settings.get('max_live_calls',60),audit_directory=settings.get('audit_directory'))
    maths=maths or CheckedMaths(app_root)
    def check_consent(profile_owner):
        if not repo.profile(profile_owner)['preferences'].get('model_consent'):
            raise HTTPException(403,{'code':'model_consent_required','message':'Confirm live model use in Learning preferences before sending this message.'})

    consent_check=check_consent if settings.get('require_live_consent') and language else None
    dialogue=DialogueService(repo,registry,language,check_consent=consent_check)
    if settings.get('assessment_policy')=='reference_checked_beta':
        if tutor_provider is not None:raise ValueError('Reference beta publication does not imply graph teacher approval')
        from .reference_policy import ReferenceCheckedAssessmentService
        assess=ReferenceCheckedAssessmentService(repo,maths)
    elif tutor_provider is not None:
        from .approval import ApprovedAssessmentService,ApprovalUnavailable
        assess=ApprovedAssessmentService(repo,maths,tutor_provider)
    else:
        assess=AssessmentService(repo,maths)
    study=StudyService(repo,registry)
    app=FastAPI(title='Socrates beta',version=__version__,docs_url='/api/docs' if testing else None,redoc_url=None)
    app.state.services={'repo':repo,'registry':registry,'dialogue':dialogue,'assessment':assess,'study':study,'language':language,'maths':maths}
    if browser_secret is not None:
        secret=browser_secret
    else:
        secret_path=data/'browser.secret'
        if not secret_path.exists():
            try:
                with secret_path.open('xb') as f:f.write(secrets.token_bytes(32))
            except FileExistsError:pass
        secret=secret_path.read_bytes()
    if not isinstance(secret,bytes) or len(secret)!=32:raise ValueError('Invalid browser ownership secret')
    def sign(owner):return owner+'.'+hmac.new(secret,owner.encode(),hashlib.sha256).hexdigest()
    def owner(request):return request.state.owner
    def session_public(s):return {k:s[k] for k in ('id','dataset','scope','title','created','updated')}
    def scoped(grade,subject,book=None,unit=None):
        if not 8<=grade<=12 or not subject.strip():raise ValueError('Choose a class and subject')
        return Scope(grade,subject,book,unit)
    @app.middleware('http')
    async def browser_boundary(request,call_next):
        if request.method in ('POST','PUT','DELETE','PATCH'):
            if request.headers.get('content-type','').split(';')[0]!='application/json' or request.headers.get('x-socrates-request')!='1':
                return JSONResponse({'detail':'Expected a same-origin JSON request'},status_code=403)
            origin=request.headers.get('origin')
            if origin and (origin not in transport.origins if transport.origin else origin!=f'{request.url.scheme}://{request.url.netloc}'):
                return JSONResponse({'detail':'Origin mismatch'},status_code=403)
        cookie=request.cookies.get('socrates_beta_profile','');parts=cookie.split('.')
        valid=len(parts)==2 and bool(re.fullmatch('[0-9a-f]{32}',parts[0])) and bool(re.fullmatch('[0-9a-f]{64}',parts[1])) and hmac.compare_digest(sign(parts[0]),cookie)
        request.state.owner=parts[0] if valid else uuid.uuid4().hex
        try:response=await call_next(request)
        except Exception:return JSONResponse({'detail':'The beta could not complete this request. Please try again.'},status_code=500)
        if not valid:response.set_cookie('socrates_beta_profile',sign(request.state.owner),httponly=True,samesite='strict',secure=transport.secure_cookie,max_age=30*86400)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        if transport.secure_cookie:response.headers['Strict-Transport-Security']='max-age=31536000'
        return response
    if tutor_provider is not None:
        @app.exception_handler(ApprovalUnavailable)
        async def approval_unavailable(request,exc):return JSONResponse({'detail':str(exc)},status_code=503)
    @app.exception_handler(BetaBusy)
    async def beta_busy(request,exc):return JSONResponse({'detail':str(exc)},status_code=503)
    @app.exception_handler(KeyError)
    async def missing(request,exc):return JSONResponse({'detail':'The requested item is not available for this browser profile.'},status_code=404)
    @app.exception_handler(ValueError)
    async def invalid(request,exc):return JSONResponse({'detail':str(exc)[:220]},status_code=400)
    @app.get('/')
    def index():return FileResponse(Path(__file__).with_name('static')/'index.html')
    @app.get('/api/health')
    def health():
        entry=registry.entries();k=registry.knowledge()
        return {'status':'ok','version':__version__,'dataset':entry['active'],'dataset_integrity':'verified',
           'language':language.health() if language and hasattr(language,'health') else {'mode':'live' if language else 'offline'},
           'beta':True,'graph_journey':tutor_provider is not None,'maths_practice_items':sum('practice' in q.get('mode_policy',{}).get('allowed_modes',[]) and (not hasattr(assess,'qualified') or q['question_id'] in assess.qualified) for q in maths.items.values()),
           'assessment_policy':getattr(assess,'POLICY',None) or ('teacher_published' if tutor_provider is not None else 'development_unapproved'),
           'reference_checked_items':len(getattr(assess,'qualified',{}))}
    @app.get('/api/bootstrap')
    def initial(request:Request):
        entry=registry.public();k=registry.knowledge()
        current_health=health()
        return {'version':__version__,'library':entry,'catalogue':k.catalogue(),'profile':repo.profile(owner(request))['preferences'],
          'dashboard':study.dashboard(owner(request)),'language':current_health['language'],
          'assessment_policy':current_health['assessment_policy'],'graph_journey':current_health['graph_journey'],
          'model_consent_required':bool(settings.get('require_live_consent') and language),'beta':True}
    @app.get('/api/library/{dataset_id}')
    def library(dataset_id:str):return {'dataset_id':dataset_id,'catalogue':registry.knowledge(dataset_id).catalogue()}
    @app.post('/api/preferences')
    def preferences(body:PrefsIn,request:Request):
        prefs=body.model_dump();prefs['goal']=redact_personal_data(clean_text(prefs['goal']))
        repo.preferences(owner(request),prefs);return {'saved':True}
    @app.post('/api/sessions')
    def new_session(body:SessionIn,request:Request):
        k=registry.knowledge(body.dataset_id);scope=Scope(body.grade,body.subject,body.book,body.unit)
        supported=[s for s in k.catalogue() if s['grade']==scope.grade and s['subject'].casefold()==scope.subject.casefold() and (not scope.book or s['book']==scope.book)]
        if not supported:raise ValueError('This dataset does not contain that class/subject/book combination')
        return session_public(repo.create_session(owner(request),k.dataset_id,body.model_dump(include={'grade','subject','book','unit'}),redact_personal_data(clean_text(body.title))))
    @app.get('/api/sessions')
    def sessions(request:Request):return [session_public(s) for s in repo.sessions(owner(request))]
    @app.get('/api/sessions/{sid}')
    def session(sid:str,request:Request):
        with repo.owner_guard(owner(request)):
            s=repo.session(sid,owner(request));active=repo.active_assessment(sid,owner(request))
            check=repo.open_check(owner(request))
            paused=bool(check and (not active or active['id']!=check['id']))
            return {**session_public(s),'turns':[{'user':t['user_text'],'result':t['result'],'created':t['created']} for t in repo.history(sid)],
                    'assessment':assess.public(active) if active and not paused else None,'assessment_paused':paused}
    @app.post('/api/chat')
    def chat(body:ChatIn,request:Request):
        return dialogue.turn(owner(request),body.session_id,body.text,body.request_id)
    @app.post('/api/practice')
    def practice(body:StartIn,request:Request):
        s=repo.session(body.session_id,owner(request))
        return assess.start(s,body.mode,body.concept,body.question_id)
    @app.post('/api/practice/{aid}/submit')
    def submit(aid:str,body:SubmitIn,request:Request):
        return assess.submit(owner(request),aid,body.answer,body.request_id)
    @app.post('/api/practice/{aid}/hint')
    def hint(aid:str,request:Request):return assess.hint(owner(request),aid)
    @app.post('/api/practice/{aid}/leave')
    def leave(aid:str,request:Request):return assess.leave(owner(request),aid)
    @app.get('/api/map')
    def learning_map(request:Request,grade:int,subject:str,dataset_id:str|None=None,book:str|None=None,unit:int|None=None):
        return study.map(owner(request),scoped(grade,subject,book,unit),dataset_id)
    @app.get('/api/plan')
    def plan(request:Request,grade:int,subject:str,dataset_id:str|None=None,book:str|None=None,minutes:int=25):
        if not 10<=minutes<=120:raise ValueError('Choose 10–120 study minutes')
        return study.plan(owner(request),scoped(grade,subject,book),dataset_id,minutes)
    @app.get('/api/dashboard')
    def dashboard(request:Request):return study.dashboard(owner(request))
    @app.get('/api/cards')
    def cards(request:Request):
        with repo.owner_guard(owner(request)):
            if repo.open_check(owner(request)):raise ValueError('Finish or leave the current check before reviewing cards')
            return repo.cards(owner(request))
    @app.get('/api/source')
    def source(request:Request,session_id:str,passage_id:str):
        with repo.owner_guard(owner(request)):
            s=repo.session(session_id,owner(request))
            if repo.open_check(owner(request)):raise ValueError('Finish or leave the current check before opening source help')
            allowed={c['id'] for t in repo.history(s['id']) for c in t['result']['citations']}
            if passage_id not in allowed:raise KeyError('Source not cited in this session')
            p=registry.knowledge(s['dataset']).passage(passage_id)
            if not p:raise KeyError('Source not found')
            return {**dialogue.citation(p),'text':p['text']}
    @app.post('/api/cards')
    def card(body:CardIn,request:Request):
        with repo.owner_guard(owner(request)):
            if repo.open_check(owner(request)):raise ValueError('Finish or leave the current check before saving source cards')
            s=repo.session(body.session_id,owner(request));allowed={c['id'] for t in repo.history(s['id']) for c in t['result']['citations']}
            if body.passage_id not in allowed:raise ValueError('Save a source cited in this conversation first')
            p=registry.knowledge(s['dataset']).passage(body.passage_id)
            if not p:raise KeyError('Source not found')
            return repo.add_card(owner(request),s['dataset'],p)
    @app.post('/api/cards/{cid}/review')
    def review(cid:str,body:ReviewIn,request:Request):
        with repo.owner_guard(owner(request)):
            if repo.open_check(owner(request)):raise ValueError('Finish or leave the current check before reviewing cards')
            return repo.review_card(owner(request),cid,body.rating)
    @app.get('/api/evidence')
    def evidence(request:Request):
        with repo.owner_guard(owner(request)):
            if repo.open_check(owner(request)):raise ValueError('Finish or leave the current check before viewing development results')
            path=ROOT/'Docs/beta/EVALUATION_RESULTS.json'
            return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'available':False}
    @app.post('/api/forget')
    def forget(request:Request):
        with repo.owner_guard(owner(request)):
            repo.forget(owner(request));return {'deleted':True}
    app.mount('/assets',StaticFiles(directory=Path(__file__).with_name('static')),name='assets')
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=list(transport.hosts))
    return app
