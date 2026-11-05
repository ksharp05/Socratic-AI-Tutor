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


def test_existing_human_packet_is_not_overwritten(tmp_path):
    packet=tmp_path/'review';packet.mkdir();rated=packet/'rater_a.csv';rated.write_text('human rating must stay')
    result=analysis.review_packet({},packet)
    assert result['existing_packet_preserved'] is True
    assert rated.read_text()=='human rating must stay'


def test_contextual_packet_has_references_and_refuses_overwrite(tmp_path,monkeypatch):
    import json,csv,pytest
    spec=importlib.util.spec_from_file_location('m3_review',ROOT/'scripts/m3/review_packet.py')
    review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
    monkeypatch.setattr(review,'SOURCE',tmp_path)
    data=tmp_path/'Directions/m3_data/development-v1';data.mkdir(parents=True)
    (data/'assignments.json').write_text(json.dumps([{'student_id':'synthetic','pair_ids':['p']}]))
    (data/'pairs.json').write_text(json.dumps([{'pair_id':'p','post':{'prompt':'Synthetic post question','answer':{'kind':'scalar','value':'2'}}}]))
    catalogue=tmp_path/'catalogue.jsonl';catalogue.write_text(json.dumps({'misconception_id':'m','incorrect_rule':'Synthetic wrong rule','correct_reasoning':'Synthetic reasoning'}))
    run=tmp_path/'run';run.mkdir();(run/'manifest.json').write_text(json.dumps({'run_id':'synthetic-run'}))
    turn={'index':0,'problem':{'prompt':'Synthetic question','answer':'2'},'student':'1','tutor':'Check the step?',
          'leaks':[],'citations':[{'passage_id':'normalized:synthetic','text':'Synthetic source'}]}
    (run/'sessions.jsonl').write_text(json.dumps({'student':'synthetic','seed':1,'seeded':['m'],'session':'s','turns':[turn]}))
    index=tmp_path/'INDEX.json';index.write_text(json.dumps({'jobs':{'c2':{'status':'completed','run':str(run)}}}))
    out=tmp_path/'packet';result=review.create(index,out,catalogue)
    assert result['human_labels_at_creation']==0
    with (out/'rater_a.csv').open(encoding='utf-8-sig',newline='') as f:row=next(csv.DictReader(f))
    assert 'Synthetic post question' in row['session_references_evaluator_only']
    assert 'Synthetic source' in row['citation_sources']
    assert row['leak_label_none_partial_full']=='' and row['rater']==''
    before=(out/'rater_a.csv').read_bytes()
    with pytest.raises(ValueError,match='preserved'):review.create(index,out,catalogue)
    assert (out/'rater_a.csv').read_bytes()==before


def test_calibration_helper_refuses_existing_output_before_any_other_read(tmp_path):
    import pytest
    spec=importlib.util.spec_from_file_location('m3_calibration',ROOT/'scripts/m3/prepare_calibration.py')
    calibration=importlib.util.module_from_spec(spec);spec.loader.exec_module(calibration)
    out=tmp_path/'existing';out.mkdir();protected=out/'rater_a.csv';protected.write_text('human data')
    with pytest.raises(ValueError,match='preserved'):calibration.prepare(tmp_path/'missing',out)
    assert protected.read_text()=='human data'


def test_complete_e3_merge_keeps_all_unique_matched_student_seed_pairs():
    spec=importlib.util.spec_from_file_location('m3_complete_report',ROOT/'scripts/m3/e3_complete_results.py')
    report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)
    baseline=[{'student':'a','seed':1},{'student':'b','seed':1},{'student':'a','seed':2}]
    result=report.merge_candidate(baseline,[[baseline[2],baseline[1]],[baseline[0]]])
    assert [(s['student'],s['seed']) for s in result]==[('a',1),('a',2),('b',1)]


def test_complete_e3_merge_rejects_duplicate_missing_or_unmatched_evidence():
    import pytest
    spec=importlib.util.spec_from_file_location('m3_complete_report_guard',ROOT/'scripts/m3/e3_complete_results.py')
    report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)
    a={'student':'a','seed':1};b={'student':'b','seed':1};extra={'student':'x','seed':1}
    for baseline,chunks,error in [([a,b],[[a],[a,b]],'Duplicate'),
                                  ([a,b],[[a]],'Incomplete'),
                                  ([a,b],[[a,extra]],'Incomplete'),
                                  ([a,a],[[a]],'Duplicate')]:
        with pytest.raises(ValueError,match=error):report.merge_candidate(baseline,chunks)
