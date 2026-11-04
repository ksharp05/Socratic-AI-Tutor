"""Hand-calculated analysis contracts; no experiment or provider calls."""
import importlib.util
from tutor.config import ROOT
from tutor import store
import hashlib

spec=importlib.util.spec_from_file_location('m3_analysis',ROOT/'scripts/m3/analyse.py')
analysis=importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_paired_bootstrap_clusters_repeats_by_source_student():
    left=[{'student':sid+'__chapter','seed':seed,'value':0} for sid in ['a','b'] for seed in [1,2,3]]
    right=[{**s,'value':1 if s['student'].startswith('a') else 3} for s in left]
    result=analysis.paired(left,right,lambda s:s['value'])
    assert result['matched_sessions']==6 and result['student_clusters']==2
    assert result['difference']==2 and result['cluster_bootstrap_ci95']==[1,3]
    filtered=analysis.paired(left,right[:-1],lambda s:s['value'])
    assert filtered['unmatched_left']==1 and filtered['unmatched_right']==0


def test_citation_integrity_detects_tampered_snapshot_and_wrong_chapter(monkeypatch):
    card={'passage_id':'normalized:synthetic','text':'Synthetic source.'}
    monkeypatch.setattr(analysis,'topic_cards',lambda:[card])
    snapshot={**card,'chapter':'trigonometry'}
    snapshot['reference_sha256']=hashlib.sha256(store.dumps(snapshot).encode()).hexdigest()
    sessions=[{'chapter':'trigonometry','turns':[{'tutor':'Why [normalized:synthetic]?','citations':[snapshot]}]}]
    valid=analysis.citation_audit(sessions)
    assert valid['valid_snapshot_hash']==valid['same_chapter']==valid['registered_source_text_match']==1
    snapshot['text']='Changed';snapshot['chapter']='quadratic_equations'
    bad=analysis.citation_audit(sessions)
    assert bad['valid_snapshot_hash']==bad['same_chapter']==bad['registered_source_text_match']==0
    assert bad['semantic_faithfulness']=='unmeasured_requires_human_review'


def test_unsupported_security_cases_remain_in_uncertainty_bounds():
    result=analysis.security_bounds([{'kind':'attack','supported':True,'success':False},
                                     {'kind':'attack','supported':False},
                                     {'kind':'control','supported':True,'false_block':True},
                                     {'kind':'control','supported':False}])
    assert result['attack']['all_scheduled_rate_bounds']==[0,.5]
    assert result['control']['all_scheduled_rate_bounds']==[.5,1]
