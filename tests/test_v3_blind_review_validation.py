"""Blind-review validation never accepts invented quotes or unrelated catalogue IDs."""
import copy,importlib.util
from pathlib import Path
import pytest
path=Path(__file__).resolve().parents[1]/'scripts/product_quality/review_v3_case_labels.py'
spec=importlib.util.spec_from_file_location('v3_label_review',path)
reviewer=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviewer)
GOOD={'id':'opaque-a','decision':'incorrect_claim','misconception_id':'test_m01','evidence_quote':'I always drop the sign','reason':'The coefficient is signed.'}
MESSAGES={'opaque-a':'I always drop the sign when recording b.'}
def test_exact_bound_evidence_is_usable():
    result=reviewer.validate([copy.deepcopy(GOOD)],MESSAGES,{'test_m01'})
    assert result[0]['validation_errors']==[]
@pytest.mark.parametrize('field,value',[('evidence_quote','Invented learner step'),('misconception_id','other_chapter')])
def test_unbound_evidence_remains_visible_and_unusable(field,value):
    row=copy.deepcopy(GOOD);row[field]=value
    result=reviewer.validate([row],MESSAGES,{'test_m01'})
    assert result[0]['validation_errors'] and result[0][field]==value
def test_unknown_or_duplicate_ids_cannot_replace_missing_reviews():
    row=copy.deepcopy(GOOD);row['id']='unknown'
    with pytest.raises(ValueError):reviewer.validate([row],MESSAGES,{'test_m01'})
    with pytest.raises(ValueError):reviewer.validate([GOOD,GOOD],{'opaque-a':MESSAGES['opaque-a'],'opaque-b':'Another message'},{'test_m01'})
def test_nonclaim_review_cannot_smuggle_a_diagnosis():
    row=copy.deepcopy(GOOD);row['decision']='no_incorrect_claim'
    with pytest.raises(ValueError):reviewer.validate([row],MESSAGES,{'test_m01'})
def test_ambiguous_review_stays_ambiguous():
    row={'id':'opaque-a','decision':'ambiguous','misconception_id':None,'evidence_quote':'','reason':'Insufficient asserted work.'}
    assert reviewer.validate([row],MESSAGES,{'test_m01'})[0]['decision']=='ambiguous'
