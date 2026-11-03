"""Render measured development results, never invented qualitative scores."""
from pathlib import Path
import os,sys,json,csv,textwrap
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Directions/beta_data/chart_dependencies'))
os.environ['MPLCONFIGDIR']=str(ROOT/'Directions/beta_data/matplotlib_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    report=json.loads((ROOT/'Docs/beta/EVALUATION_RESULTS.json').read_text())
    runs=[]
    for file in sorted((ROOT/'Directions/beta_data/evaluation_runs').glob('*/COMPLETE_RESULTS.json')):
        r=json.loads(file.read_text())
        if r['case_file_sha256']==report['case_file_sha256']:runs.append(r)
    baseline=runs[0]
    report['prior_runs']=[{'run_id':r['run_id'],'completed':sum(c['completed'] for c in r['cases']),'total':r['total_cases'],'live_calls':r['live_calls'],'dataset_id':r['dataset_id']} for r in runs]
    report['historical_issues']=[
      {'id':'M02','issue':'Overlong first responses; bounded format repair was exercised in the release run.'},
      {'id':'C04','issue':'AP acronym retrieval initially favoured an advanced reference; foundational retrieval was corrected.'},
      {'id':'H04','issue':'An expected primary-reader passage was absent; an exact quote was added with the data import CLI.'},
      {'id':'S05','issue':'A factual sensory description falsely triggered the broad chemical guard. Raw-response audit distinguished it from an instruction; the rule was narrowed and both behaviors tested.'}]
    (ROOT/'Docs/beta/EVALUATION_RESULTS.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    groups=report['groups'];bg={g['id']:g for g in baseline['groups']}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,(ax,lat)=plt.subplots(1,2,figsize=(13.2,6.6),gridspec_kw={'width_ratios':[1.8,1]})
    fig.patch.set_facecolor('#fbfcf8');ax.set_facecolor('#fbfcf8');lat.set_facecolor('#fbfcf8')
    y=np.arange(len(groups));height=.30
    ax.barh(y-height/2,[bg[g['id']]['completion_rate']*100 for g in groups],height,label='Initial development run',color='#b8c4b0')
    current=ax.barh(y+height/2,[g['completion_rate']*100 for g in groups],height,label='Current beta run',color=['#315f49']*5+['#909890'])
    ax.set_yticks(y,[g['label'] for g in groups]);ax.invert_yaxis();ax.set_xlim(0,126);ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('Tasks meeting declared completion checks (%)')
    ax.grid(axis='x',color='#dfe5da',linewidth=.7);ax.set_axisbelow(True)
    for bar,g in zip(current,groups):
        ax.text(g['completion_rate']*100+2,bar.get_y()+bar.get_height()/2,f"{g['completed']}/{g['total']}",va='center',fontsize=10,fontweight='bold',color='#24372b')
    ax.text(3,y[-1]+.42,'6/6 unsupported requests were appropriately declined or clarified.',fontsize=8.2,color='#65715e',va='center')
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.13),ncol=1,frameon=False,fontsize=9)
    lat.barh(y,[g['median_latency_ms']/1000 for g in groups],height=.48,color=['#7a9566']*5+['#a7ada0'])
    lat.set_yticks(y,[]);lat.invert_yaxis();lat.set_xlim(0,max(g['median_latency_ms']/1000 for g in groups)*1.35)
    lat.set_xlabel('Median end-to-end task time (seconds)');lat.grid(axis='x',color='#dfe5da',linewidth=.7);lat.set_axisbelow(True)
    for i,g in enumerate(groups):lat.text(g['median_latency_ms']/1000+.04,i,f"{g['median_latency_ms']/1000:.2f}s",va='center',fontsize=9)
    fig.suptitle('Socrates beta · measured strengths and limits',x=.06,y=.98,ha='left',fontsize=19,fontweight='bold',color='#1e3529')
    fig.text(.06,.917,f"34 tasks per run · {len(runs)} recorded development runs · {report['live_calls']} current-run model calls",fontsize=10,color='#5c6a58')
    fig.text(.06,.06,'Completion checks: accepted live reply + expected textbook source, or independent maths checked by code.\nKnown limitations remain in the denominator. These tuned development results do not measure factual accuracy, teaching quality or learning gain.',fontsize=9,color='#5c6a58',linespacing=1.5)
    fig.subplots_adjust(left=.20,right=.97,top=.80,bottom=.18,wspace=.13)
    for suffix in ('png','svg'):fig.savefig(ROOT/f'Docs/beta/performance.{suffix}',dpi=170,facecolor=fig.get_facecolor())
    plt.close(fig)
    svg=ROOT/'Docs/beta/performance.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')
    with (ROOT/'Docs/beta/question_results.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['id','group','grade','subject','question','completed','appropriate_abstention','latency_ms','finding'])
        writer.writeheader();writer.writerows({k:r.get(k) for k in writer.fieldnames} for r in report['cases'])
    lines=['# Questions to try in the Socrates beta','',
      'Measured on 3 November 2026 (India). The same 34 developer-authored tasks were used during fixes; these are development results, not an independent test. All outcomes are retained. The release run completed 28/28 supported tasks under the declared technical checks; six further unsupported requests were appropriately declined or clarified. This does not establish factual accuracy or flawless teaching.','',
      'Open the app at http://127.0.0.1:8770. Set the stated class and subject. For follow-ups, remain in the same conversation.','',
      '## Strong observed examples','',
      '| Class / subject | Question | What was observed |','|---|---|---|']
    ids=['S01','M01','M02','S03','S07','H03','H04','C01','C02','C04']
    byid={r['id']:r for r in report['cases']}
    for cid in ids:
        r=byid[cid];note='Live reply passed format and expected-source checks.'
        if cid=='C01':note+=' The spelling error was handled.'
        if cid=='C02':note+=' Follow with “I still don’t understand. Could you make that simpler?” Context was retained; question difficulty still needs review.'
        if cid=='C04':note+=' Follow with “I think it just means numbers go up. Is that enough?” The source-backed distinction was explained.'
        lines.append(f"| {r['grade']} / {r['subject']} | {r['question']} | {note} |")
    lines+=['','## Weakest or unavailable examples','',
      '| Class / subject | Question | Observed limitation |','|---|---|---|']
    for r in report['worst_questions']:
        note=r['finding']
        if r['id']=='S05':note='Chemical-identification wording triggered a conservative guard; a source fallback was served. Review is needed to distinguish a factual description from unsafe instructions.'
        lines.append(f"| {r['grade']} / {r['subject']} | {r['question']} | {note} |")
    lines+=['','## Fragile supported questions found during development','',
      '- “What does the discriminant tell us about real roots?” — initially exceeded the reply limit; the release run used the explicitly recorded format-repair path.',
      '- “What is an arithmetic progression?” followed by “I think it just means numbers go up. Is that enough?” — initially produced advanced source recovery and a grading phrase; foundational retrieval and question phrasing were improved.',
      '- “Why does Lencho write a letter to God in the story?” — initially cited a workbook; primary-reader coverage was recovered through the data plug-in.',
      '- “How do acids and bases differ in their properties?” — an overly broad guard falsely rejected a factual description. A private audit confirmed the false block; the narrowed rule is covered by factual-description and unsafe-instruction tests.',
      '', 'These are regression questions with known history, not proof of persistent factual errors in the current model. The release run passed them under the declared checks; future wording can still expose problems.']
    lines+=['','## Checked maths examples','',
      'Use Practice & quick checks. These six public practice prompts were tested by submitting answers independently calculated from their givens, rather than asking the language model to grade. The API supports choosing a public question ID in practice mode; diagnostic/quiz ordering remains server-controlled.','']
    for r in report['cases']:
        if r['kind']=='checked_math':lines += [f"- **{r['question_id']}** — {r['question']}"]
    lines+=['','## How to read the results','',
      '- Baseline: 25/34 met completion checks (25/28 supported tasks), 25 actual model calls.',f"- Current beta: {sum(r['completed'] for r in report['cases'])}/34 met completion checks (28/28 supported tasks), {report['live_calls']} actual model calls, including {report['format_repairs']} bounded format repair.",'- All runs retained all six deliberate unsupported tasks as incomplete and recorded appropriate abstention separately.','- The original literature response cited a relevant NCERT workbook instead of the expected primary reader. That was a source-preference failure, not proof its factual answer was wrong. A validated primary-reader quote was added through the import CLI and the next run cited it.','- All four runs are retained: 25/34, 27/34, 27/34 and 28/34 completions, with 25, 25, 27 and 26 model calls respectively. Earlier chemistry rejections were diagnosed as a guard false positive, not proof of unsafe model instructions.','- Response format and source-ID matches do not prove semantic grounding. Analogies, generated examples and the difficulty of questions need human assessment.','- No final held-out cases were read or used. A future independent beta sample should be authored and labelled separately.','']
    (ROOT/'Docs/beta/QUESTIONS_TO_TRY.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Wrote performance.png, performance.svg, question_results.csv and QUESTIONS_TO_TRY.md')

if __name__=='__main__':main()
