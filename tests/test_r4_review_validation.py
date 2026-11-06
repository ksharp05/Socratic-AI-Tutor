"""AI-review validation preserves mistakes as unusable evidence, never approval."""
import copy,importlib.util
from pathlib import Path
import pytest
path=Path(__file__).resolve().parents[1]/"scripts/product_quality/review_r4_examples.py"
spec=importlib.util.spec_from_file_location("r4_review_runner",path)
reviewer=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviewer)
CASE={"id":"opaque","worked_presentation":"The example sum is 42."}
REVIEW={"id":"opaque","math_status":"correct","clarity_score":4,"method_match":"yes","issues":[],"improvement":"Label the method."}
def test_bound_structured_review_is_usable_but_is_only_a_review():
    row=reviewer.validate_review(copy.deepcopy(REVIEW),CASE)
    assert row["schema_errors"]==[] and "approved" not in row
@pytest.mark.parametrize("bad",[True,0,6])
def test_invalid_clarity_scores_are_not_accepted(bad):
    row=copy.deepcopy(REVIEW);row["clarity_score"]=bad
    assert "clarity_score" in reviewer.validate_review(row,CASE)["schema_errors"]
def test_invented_issue_quote_remains_visible_but_unusable():
    row=copy.deepcopy(REVIEW);row["math_status"]="incorrect"
    row["issues"]=[{"kind":"math","quote":"Invented computation","explanation":"A claimed fault."}]
    result=reviewer.validate_review(row,CASE)
    assert result["issues"][0]["validation_errors"]==["unbound_quote"]
    assert result["issues"][0]["quote"]=="Invented computation"
def test_wrong_case_id_cannot_be_used_as_a_paired_review():
    row=copy.deepcopy(REVIEW);row["id"]="another-case"
    assert "unbound_id" in reviewer.validate_review(row,CASE)["schema_errors"]
