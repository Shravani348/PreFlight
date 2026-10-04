from typing import List
from backend.models.schemas import Issue, FixPlanStep
from backend.services.recommendation import generate_recommendations

PRIORITY_ORDER = {
    "VERY_HIGH": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4
}

TITLES = {
    "MISSING_DOCUMENT": "Provide Missing Document",
    "DOB_MISMATCH": "Fix Date of Birth Mismatch",
    "NAME_MISMATCH": "Fix Name Mismatch",
    "NAME_NEEDS_VERIFICATION": "Verify Name Variation",
    "INVALID_FORMAT": "Fix Invalid File Format",
    "FILE_TOO_LARGE": "Reduce File Size",
    "LOW_AI_CONFIDENCE": "Verify Low Confidence Extraction",
    "DOB_NEEDS_VERIFICATION": "Verify Date of Birth",
    "PARENT_NAME_MISMATCH": "Fix Parent Name Mismatch",
    "PARENT_NAME_NEEDS_VERIFICATION": "Verify Parent Name",
    "ADDRESS_MISMATCH": "Fix Address Mismatch",
    "ADDRESS_NEEDS_VERIFICATION": "Verify Address",
    "DOCUMENT_TYPE_MISMATCH": "Check Uploaded Document Type",
    "UNREADABLE_DOCUMENT": "Re-upload Unreadable Document",
    "UNSUPPORTED_FILE_TYPE": "Use a Supported File Type"
}

def generate_fix_plan(issues: List[Issue]) -> List[FixPlanStep]:
    if not issues:
        return []
        
    recommendations = generate_recommendations(issues)
    
    combined = []
    for issue, rec in zip(issues, recommendations):
        title = TITLES.get(issue.type, f"Resolve {issue.type}")
        
        combined.append({
            "issue": issue,
            "rec": rec,
            "title": title
        })
        
    # Sort primarily by priority, then by issue type for deterministic order
    combined.sort(key=lambda x: (
        PRIORITY_ORDER.get(x["rec"].priority, 99),
        x["issue"].type
    ))
    
    plan = []
    for idx, item in enumerate(combined, start=1):
        issue = item["issue"]
        rec = item["rec"]
        
        step = FixPlanStep(
            step=idx,
            issue_type=issue.type,
            priority=rec.priority,
            title=item["title"],
            action=rec.recommended_action,
            why=rec.why_it_matters,
            evidence=issue.evidence
        )
        plan.append(step)
        
    return plan
