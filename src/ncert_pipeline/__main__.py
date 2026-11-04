from __future__ import annotations
import argparse,json,os
from pathlib import Path
from . import __version__
from .retrieval import Retriever
from .dialogue import Tutor


def main():
    code_root=Path(__file__).resolve().parents[2]
    root=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',code_root)).resolve()
    p=argparse.ArgumentParser(description='Local NCERT concept pipeline — development preview')
    p.add_argument('--output',type=Path,default=root/'Directions/book_pipeline/v0_1')
    sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build'); b.add_argument('--manifest',type=Path,default=root/'Directions/ncert_all_subjects_8_12/2026-11-03/MANIFEST.json')
    b.add_argument('--pdftotext',type=Path,default=Path('C:/Program Files/Git/mingw64/bin/pdftotext.exe'))
    cards=code_root/'content/dataset-v0.10.0/corpus.jsonl'
    if not cards.exists():cards=root.with_name('Socratic Tutor Main')/'content/dataset-v0.10.0/corpus.jsonl'
    b.add_argument('--cards',type=Path,default=cards)
    b.add_argument('--workers',type=int,default=4)
    q=sub.add_parser('search'); q.add_argument('query'); q.add_argument('--grade',type=int,required=True); q.add_argument('--subject',required=True)
    q.add_argument('--book'); q.add_argument('--unit-file-index',type=int)
    sub.add_parser('scopes')
    for name in ('chat','serve'):
        c=sub.add_parser(name); c.add_argument('--live',action='store_true')
        c.add_argument('--app-root',type=Path,default=Path(os.environ.get('SOCRATES_TEAM_APP_ROOT') or code_root))
        c.add_argument('--max-live-calls',type=int,default=6)
        if name=='chat':
            c.add_argument('--grade',type=int,required=True); c.add_argument('--subject',required=True)
            c.add_argument('--book'); c.add_argument('--unit-file-index',type=int); c.add_argument('--mode',choices=['practice','quiz'],default='practice')
        else: c.add_argument('--port',type=int,default=8766)
    args=p.parse_args()
    if args.command=='build':
        from .build import build
        report=build(root,args.manifest,args.output,args.pdftotext,args.cards,args.workers)
        print(json.dumps(report,indent=2,ensure_ascii=False)); return
    retrieval=Retriever(args.output/'preview.sqlite')
    if args.command=='scopes': print(json.dumps(retrieval.scopes(),indent=2)); return
    if args.command=='search':
        print(json.dumps(retrieval.search(args.query,grade=args.grade,subject=args.subject,book=args.book,unit_file_index=args.unit_file_index),indent=2,ensure_ascii=False)); return
    provider=None
    if args.live:
        from .provider import MainAppProvider
        provider=MainAppProvider(args.app_root,max_calls=args.max_live_calls)
    tutor=Tutor(retrieval,args.output/'local_sessions.sqlite',provider)
    if args.command=='serve':
        from .web import serve
        serve(tutor,port=args.port); return
    sid=tutor.new_session(grade=args.grade,subject=args.subject,book=args.book,unit_file_index=args.unit_file_index,mode=args.mode)
    print(f'Socrates {__version__}: development concept preview; '+('live provider, bounded calls' if provider else 'offline scaffold, no model'))
    print('Enter /exit to stop or /forget to delete this conversation. No answer grading in this preview.')
    while True:
        try: text=input('You: ').strip()
        except (EOFError,KeyboardInterrupt): break
        if text=='/exit': break
        if text=='/forget': tutor.reset(sid); print('Conversation deleted.'); break
        if not text: continue
        out=tutor.turn(sid,text)
        print('Socrates:',out['reply'])
        print('Status:',out['provider_status'])
        for cite in out['citations']: print(f'  {cite["title"]} | {cite["source_id"]} | PDF page {cite["page"]}')
    if provider:
        (args.output/'last_cli_provider_receipts.json').write_text(json.dumps(provider.receipts,indent=2),encoding='utf-8')

if __name__=='__main__': main()
