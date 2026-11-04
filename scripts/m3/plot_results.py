"""Publication-style development figures from saved JSON; no provider calls."""
import json,os,sys
from pathlib import Path
CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',CODE)).resolve()
os.environ.setdefault('MPLCONFIGDIR',str(SOURCE/'Directions/m3_runs/v2/matplotlib_cache'))
sys.path.insert(0,str(SOURCE/'Directions/m3_runs/v2/plot_deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    out=CODE/'Docs/m4';data=json.loads((out/'RESULTS.json').read_text(encoding='utf-8'))
    comparisons=[('E1_C2_minus_C1','C2 minus C1 (E1, n=16)'),('E1_C2_minus_C0','C2 minus C0 (E1, n=16)'),
        ('E3_budget_tranche_minus_matched_before','Candidate minus C2 (E3, n=12)'),
        ('E4a_memory_on_minus_off','Memory on minus off (E4a, n=16)'),
        ('E4b_telling_minus_hints','Telling minus hints (E4b, n=16)')]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    fig,(ax,bx)=plt.subplots(1,2,figsize=(13,5.8),gridspec_kw={'width_ratios':[1.45,1]})
    colors=['#33699b','#33699b','#27877a','#77589e','#bd6844']
    for i,((key,label),color) in enumerate(zip(comparisons,colors)):
        row=data['paired_comparisons'][key]['quiz_gain'];value=row['difference'];lo,hi=row['cluster_bootstrap_ci95']
        ax.errorbar(value,i,xerr=[[value-lo],[hi-value]],fmt='o',color=color,capsize=5,markersize=7,lw=2)
    ax.axvline(0,color='#555',ls='--',lw=1)
    ax.set_yticks(range(len(comparisons)),[label for _,label in comparisons]);ax.invert_yaxis()
    ax.set_xlabel('Paired difference in simulated correct items')
    ax.set_title('Paired scores: student-cluster 95% intervals',loc='left',fontweight='bold',pad=15)
    ax.set_xlim(-.22,.22);ax.grid(axis='x',color='#e7e7e7',lw=.8);ax.set_axisbelow(True)
    labels={'c0':'C0','c1':'C1','c2':'C2','memory_off':'Memory off','direct_answers':'Telling (intentional)','e3_after_budget_tranche12':'E3 candidate'}
    rows=data['conditions'];rates=[100*r['full_leak_turns']/r['turns'] for r in rows]
    bars=bx.barh(range(len(rows)),rates,color=['#bd6844' if r['condition']=='direct_answers' else '#7799b5' for r in rows],height=.58)
    bx.set_yticks(range(len(rows)),[labels[r['condition']] for r in rows]);bx.invert_yaxis();bx.set_xlim(0,38)
    for bar,row,rate in zip(bars,rows,rates):
        bx.text(rate+.8,bar.get_y()+bar.get_height()/2,f"{rate:.1f}%  ({row['full_leak_turns']}/{row['turns']})",va='center',fontsize=9)
    bx.set_xlabel('Full code-detected leak turns (%)')
    bx.set_title('Recorded answer disclosure',loc='left',fontweight='bold',pad=15)
    bx.grid(axis='x',color='#e7e7e7',lw=.8);bx.set_axisbelow(True)
    fig.suptitle('Exploratory development results',x=.03,y=.98,ha='left',fontsize=17,fontweight='bold')
    fig.text(.03,.025,'Synthetic students and code proxies; no human learning or semantic-safety claim. E3 is 36/48 planned sessions. Intervals: 2,000 clustered resamples, seed 0.',fontsize=9,color='#555')
    fig.tight_layout(rect=[.01,.08,.99,.92],w_pad=3)
    for ext in ['png','svg']:
        path=out/f'development_results.{ext}';fig.savefig(path,dpi=170,facecolor='white',bbox_inches='tight',pad_inches=.2)
        import shutil;shutil.copy2(path,SOURCE/'Docs/m4'/path.name)
    plt.close(fig)
    (out/'FIGURE_METADATA.json').write_text(json.dumps({'matplotlib':matplotlib.__version__,'input':'RESULTS.json','no_new_experiments':True},indent=2)+'\n',encoding='utf-8')
    print(out/'development_results.png')


if __name__=='__main__':main()
