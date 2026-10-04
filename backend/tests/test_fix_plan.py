import pytest
from backend.models.schemas import Issue
from backend.services.fix_plan import generate_fix_plan

def test_empty_issue_list():
    plan = generate_fix_plan([])
    assert len(plan) == 0

def test_single_critical_issue():
    issues = [Issue(type="DOB_MISMATCH", severity="CRITICAL", message="test", evidence=["dob1", "dob2"])]
    plan = generate_fix_plan(issues)
    assert len(plan) == 1
    assert plan[0].step == 1
    assert plan[0].priority == "VERY_HIGH"
    assert plan[0].issue_type == "DOB_MISMATCH"
    assert plan[0].title == "Fix Date of Birth Mismatch"
    assert plan[0].evidence == ["dob1", "dob2"]

def test_multiple_issues_prioritization():
    issues = [
        Issue(type="FILE_TOO_LARGE", severity="WARNING", message="test"),
        Issue(type="DOB_MISMATCH", severity="CRITICAL", message="test"),
        Issue(type="NAME_NEEDS_VERIFICATION", severity="WARNING", message="test"),
        Issue(type="MISSING_DOCUMENT", severity="CRITICAL", message="test")
    ]
    
    plan = generate_fix_plan(issues)
    assert len(plan) == 4
    
    assert plan[0].priority == "VERY_HIGH"
    assert plan[1].priority == "VERY_HIGH"
    assert plan[2].priority == "MEDIUM"
    assert plan[3].priority == "MEDIUM"
    
    assert plan[0].issue_type == "DOB_MISMATCH"
    assert plan[1].issue_type == "MISSING_DOCUMENT"
    assert plan[2].issue_type == "FILE_TOO_LARGE"
    assert plan[3].issue_type == "NAME_NEEDS_VERIFICATION"
    
    assert [p.step for p in plan] == [1, 2, 3, 4]

def test_recommendation_and_evidence_preserved():
    issues = [
        Issue(
            type="INVALID_FORMAT", 
            severity="WARNING", 
            message="test", 
            evidence=["Format: png"]
        )
    ]
    plan = generate_fix_plan(issues)
    assert len(plan) == 1
    assert plan[0].evidence == ["Format: png"]
    assert "format does not satisfy" in plan[0].why
    assert "upload the file using an allowed format" in plan[0].action

def test_unknown_issue_fallback():
    issues = [Issue(type="UNKNOWN_ERR", severity="CRITICAL", message="test")]
    plan = generate_fix_plan(issues)
    assert plan[0].title == "Resolve UNKNOWN_ERR"
    assert plan[0].priority == "VERY_HIGH"
