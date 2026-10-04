import pytest
from backend.models.schemas import Issue
from backend.services.recommendation import generate_recommendations

def test_missing_document():
    issues = [Issue(type="MISSING_DOCUMENT", severity="CRITICAL", message="test")]
    recs = generate_recommendations(issues)
    assert len(recs) == 1
    assert recs[0].issue_type == "MISSING_DOCUMENT"
    assert recs[0].priority == "VERY_HIGH"
    assert "required document is missing" in recs[0].why_it_matters
    assert "upload the required document" in recs[0].recommended_action

def test_dob_mismatch():
    issues = [Issue(type="DOB_MISMATCH", severity="CRITICAL", message="test")]
    recs = generate_recommendations(issues)
    assert len(recs) == 1
    assert recs[0].priority == "VERY_HIGH"
    assert "Conflicting Date of Birth values" in recs[0].why_it_matters

def test_name_mismatch():
    issues = [Issue(type="NAME_MISMATCH", severity="CRITICAL", message="test")]
    recs = generate_recommendations(issues)
    assert len(recs) == 1
    assert recs[0].priority == "VERY_HIGH"
    assert "Different names" in recs[0].why_it_matters

def test_name_needs_verification():
    issues = [Issue(type="NAME_NEEDS_VERIFICATION", severity="WARNING", message="test")]
    recs = generate_recommendations(issues)
    assert len(recs) == 1
    assert recs[0].priority == "MEDIUM"
    assert "similar but not confidently identical" in recs[0].why_it_matters

def test_invalid_format():
    issues = [Issue(type="INVALID_FORMAT", severity="WARNING", message="test")]
    recs = generate_recommendations(issues)
    assert len(recs) == 1
    assert recs[0].priority == "MEDIUM"
    assert "format does not satisfy" in recs[0].why_it_matters

def test_file_too_large():
    issues = [Issue(type="FILE_TOO_LARGE", severity="WARNING", message="test")]
    recs = generate_recommendations(issues)
    assert len(recs) == 1
    assert recs[0].priority == "MEDIUM"
    assert "exceeds the configured size limit" in recs[0].why_it_matters

def test_priority_mapping():
    issues = [
        Issue(type="UNKNOWN", severity="CRITICAL", message=""),
        Issue(type="UNKNOWN", severity="WARNING", message=""),
        Issue(type="UNKNOWN", severity="INFO", message="")
    ]
    recs = generate_recommendations(issues)
    assert recs[0].priority == "VERY_HIGH"
    assert recs[1].priority == "MEDIUM"
    assert recs[2].priority == "LOW"

def test_empty_issue_list():
    recs = generate_recommendations([])
    assert len(recs) == 0
