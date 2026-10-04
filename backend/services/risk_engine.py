from typing import List
from backend.models.schemas import Issue, RiskAssessment

def calculate_risk(issues: List[Issue]) -> RiskAssessment:
    critical_count = 0
    warning_count = 0
    info_count = 0
    total_penalty = 0
    
    highest_risk_issue = None
    max_issue_penalty = -1
    
    penalty_map = {
        "CRITICAL": 30,
        "WARNING": 10,
        "INFO": 2
    }
    
    for issue in issues:
        severity = issue.severity.upper()
        if severity == "CRITICAL":
            critical_count += 1
        elif severity == "WARNING":
            warning_count += 1
        elif severity == "INFO":
            info_count += 1
            
        issue_penalty = penalty_map.get(severity, 0)
        total_penalty += issue_penalty
        
        if issue_penalty > max_issue_penalty:
            max_issue_penalty = issue_penalty
            highest_risk_issue = issue
            
    readiness_score = max(0, 100 - total_penalty)
    
    if total_penalty <= 20:
        risk = "LOW"
    elif total_penalty <= 50:
        risk = "MEDIUM"
    else:
        risk = "HIGH"
        
    return RiskAssessment(
        risk=risk,
        readiness_score=readiness_score,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
        highest_risk_issue=highest_risk_issue
    )
