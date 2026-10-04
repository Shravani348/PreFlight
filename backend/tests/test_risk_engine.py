import pytest
from backend.models.schemas import Issue
from backend.services.risk_engine import calculate_risk

def test_no_issues():
    result = calculate_risk([])
    assert result.risk == "LOW"
    assert result.readiness_score == 100
    assert result.critical_count == 0
    assert result.warning_count == 0
    assert result.info_count == 0
    assert result.highest_risk_issue is None

def test_warning_only():
    issues = [Issue(type="INVALID_FORMAT", severity="WARNING", message="test")]
    result = calculate_risk(issues)
    assert result.risk == "LOW"
    assert result.readiness_score == 90
    assert result.warning_count == 1
    assert result.highest_risk_issue.type == "INVALID_FORMAT"

def test_critical_issue():
    issues = [Issue(type="MISSING_DOCUMENT", severity="CRITICAL", message="test")]
    result = calculate_risk(issues)
    assert result.risk == "MEDIUM"
    assert result.readiness_score == 70
    assert result.critical_count == 1
    assert result.highest_risk_issue.type == "MISSING_DOCUMENT"

def test_multiple_issues():
    issues = [
        Issue(type="MISSING_DOCUMENT", severity="CRITICAL", message="test"),
        Issue(type="INVALID_FORMAT", severity="WARNING", message="test"),
        Issue(type="FILE_TOO_LARGE", severity="WARNING", message="test"),
        Issue(type="INFO_MSG", severity="INFO", message="test")
    ]
    result = calculate_risk(issues)
    assert result.risk == "HIGH"
    assert result.readiness_score == 48
    assert result.critical_count == 1
    assert result.warning_count == 2
    assert result.info_count == 1
    assert result.highest_risk_issue.type == "MISSING_DOCUMENT"

def test_readiness_score_never_below_zero():
    issues = [Issue(type="CRITICAL_ERR", severity="CRITICAL", message="test") for _ in range(5)]
    result = calculate_risk(issues)
    assert result.risk == "HIGH"
    assert result.readiness_score == 0
    assert result.critical_count == 5

def test_highest_risk_issue_selection():
    issues = [
        Issue(type="INFO_ERR", severity="INFO", message="test"),
        Issue(type="WARN_ERR", severity="WARNING", message="test"),
        Issue(type="CRITICAL_ERR", severity="CRITICAL", message="test")
    ]
    result = calculate_risk(issues)
    assert result.highest_risk_issue.type == "CRITICAL_ERR"

    issues_reversed = list(reversed(issues))
    result2 = calculate_risk(issues_reversed)
    assert result2.highest_risk_issue.type == "CRITICAL_ERR"
