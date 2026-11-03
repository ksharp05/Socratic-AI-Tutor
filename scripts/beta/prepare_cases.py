from pathlib import Path
import json,math
from fractions import Fraction
root=Path.cwd();rows=[]
def chat(id,group,grade,subject,question,sources,followups=None):
 rows.append(dict(id=id,group=group,kind='chat',grade=grade,subject=subject,question=question,
                  messages=[question]+(followups or []),expected_sources=sources))
for id,q,s in [
 ('M01','What makes an expression quadratic after simplifying it?',['jemh1/jemh104.pdf']),
 ('M02','What does the discriminant tell us about real roots?',['jemh1/jemh104.pdf']),
 ('M03','What makes a sequence an arithmetic progression?',['jemh1/jemh105.pdf']),
 ('M04','Why is the common difference important in an arithmetic progression?',['jemh1/jemh105.pdf']),
 ('M05','How are sine and cosine related to the sides of a right triangle?',['jemh1/jemh108.pdf']),
 ('M06','Why is tangent not defined at some standard angles?',['jemh1/jemh108.pdf'])]:chat(id,'math_concepts',10,'Mathematics',q,s)
for id,g,sub,q,s in [
 ('S01',8,'Science','Why do rough surfaces oppose motion through friction?',['hecu1/hecu105.pdf']),
 ('S02',9,'Science','Why is a cell called a basic unit of life?',['iesc1/iesc102.pdf']),
 ('S03',10,'Science','How does photosynthesis help a plant make food?',['jesc1/jesc105.pdf']),
 ('S04',10,'Science','What is the difference between xylem and phloem?',['jesc1/jesc105.pdf']),
 ('S05',10,'Science','How do acids and bases differ in their properties?',['jesc1/jesc102.pdf']),
 ('S06',11,'Physics','How is acceleration related to a change in velocity?',['keph1/keph102.pdf','keph1/keph103.pdf','keph1/keph104.pdf']),
 ('S07',12,'Biology','Why should DNA replicate before a cell divides?',['lebo1/lebo105.pdf']),
 ('S08',12,'Biology','What role do decomposers play in an ecosystem?',['lebo1/lebo112.pdf'])]:chat(id,'science_concepts',g,sub,q,s)
for id,g,sub,q,s in [
 ('H01',11,'History','Why was writing important in Mesopotamian cities?',['kehs1/kehs101.pdf']),
 ('H02',12,'Economics','What is the role of a central bank in an economy?',['leec1/leec103.pdf']),
 ('H03',10,'Social Science','Why is power sharing important in a democracy?',['jess4/jess401.pdf']),
 ('H04',10,'English','Why does Lencho write a letter to God in the story?',['jeff1/jeff101.pdf'])]:chat(id,'other_subjects',g,sub,q,s)
chat('C01','natural_english',10,'Science','Can you explain photosyntesis in plain English?',['jesc1/jesc105.pdf'])
chat('C02','natural_english',12,'Biology','Explain DNA replication in simple English.',['lebo1/lebo105.pdf'],["I still don't understand. Could you make that simpler?"])
chat('C03','natural_english',10,'Science','Explain photosynthesis.',['jesc1/jesc105.pdf'],['Actually, I meant respiration. How does that release energy?'])
chat('C04','natural_english',10,'Mathematics','What is an arithmetic progression?',['jemh1/jemh105.pdf'],['I think it just means numbers go up. Is that enough?'])
public=[json.loads(l) for l in (root.with_name('Socratic Tutor Main')/'content/dataset-v0.10.0/practice_questions.jsonl').read_text().splitlines()]
def checked(id,task,predicate,answer):
 item=next(x for x in public if x['problem']['task_type']==task and predicate(x['problem']['givens']))
 rows.append(dict(id=id,group='checked_practice',kind='checked_math',grade=10,subject='Mathematics',question=item['prompt'],
  question_id=item['question_id'],answer=answer(item['problem']['givens']),oracle='Independent arithmetic from public givens; no grader key read'))
checked('P01','ap_term',lambda g:True,lambda g:str(list(Fraction(g['a'])+i*Fraction(g['d']) for i in range(g['n']))[-1]))
checked('P02','ap_sum',lambda g:True,lambda g:str(sum(Fraction(g['a'])+i*Fraction(g['d']) for i in range(g['n']))))
checked('P03','quadratic_solve',lambda g:g['b']**2-4*g['a']*g['c']<0,lambda g:'no real roots')
checked('P04','quadratic_solve',lambda g:(g['b']**2-4*g['a']*g['c']>0 and math.isqrt(g['b']**2-4*g['a']*g['c'])**2==g['b']**2-4*g['a']*g['c']),lambda g:', '.join(str(Fraction(-g['b']+sign*math.isqrt(g['b']**2-4*g['a']*g['c']),2*g['a'])) for sign in (-1,1)))
checked('P05','trig_triangle_ratio',lambda g:g['reference']=='A' and g['ratio']=='sec',lambda g:str(Fraction(g['hypotenuse'],g['adjacent'])))
checked('P06','quadratic_classify',lambda g:True,lambda g:'two_distinct_real' if g['b']**2-4*g['a']*g['c']>0 else 'repeated_real' if g['b']**2-4*g['a']*g['c']==0 else 'no_real')
for id,g,sub,q,reason in [
 ('L01',12,'Mathematics','Can you teach me integration by parts and check my answer?','No normalized Class 12 maths teaching/checking adapter yet.'),
 ('L02',11,'Urdu','Explain the meaning of the poem in my Urdu textbook.','The beta retrieval scope is English-first; Urdu teaching is not enabled.'),
 ('L03',9,'ICT','Explain computer networking from my Class 9 ICT textbook.','No acquired active Class 9 ICT book; publisher Coming Soon.'),
 ('L04',10,'Science','Using the attached diagram, tell me which ray is refracted.','No image was supplied and this beta has no diagram-understanding adapter.'),
 ('L05',12,'Economics',"What is today's live stock price and should I buy it?",'No live market data or financial-advice tool in this textbook tutor.'),
 ('L06',10,'Science','Why does it do that?','No prior referent/topic; clarification is needed rather than inventing a source.')]:
 rows.append(dict(id=id,group='known_limits',kind='limit',grade=g,subject=sub,question=q,reason=reason))
doc={'schema':1,'authorship':'development_authored_not_independent_final_evaluation','human_review':False,
 'completion_definition':'Chat: all turns return live accepted replies and at least one citation matches a developer-selected expected source. Maths: independent arithmetic submission receives code-checked correct. Known unsupported tasks score zero task completion; appropriate abstention is counted separately.',
 'factual_semantic_accuracy':'Not established by source-ID/format checks. Independent human evaluation pending.',
 'cases':rows}
(root/'Docs/beta/DEVELOPMENT_CASES.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf-8')
print('Prepared and frozen',len(rows),'development cases')
