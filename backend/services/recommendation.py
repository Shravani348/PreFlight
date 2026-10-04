from typing import List
from backend.models.schemas import Issue, Recommendation

PRIORITY_MAP = {
    "CRITICAL": "VERY_HIGH",
    "WARNING": "MEDIUM",
    "INFO": "LOW"
}

RECOMMENDATION_TEMPLATES = {
    "MISSING_DOCUMENT": {
        "why_it_matters": "A required document is missing from the application.",
        "recommended_action": "Obtain and upload the required document."
    },
    "DOB_MISMATCH": {
        "why_it_matters": "Conflicting Date of Birth values may cause identity verification problems.",
        "recommended_action": "Verify DOB against the primary/official identity or birth document and correct the inconsistent document/form."
    },
    "NAME_MISMATCH": {
        "why_it_matters": "Different names across documents may cause identity verification problems.",
        "recommended_action": "Verify the correct legal name and provide supporting documentation if a name change occurred."
    },
    "NAME_NEEDS_VERIFICATION": {
        "why_it_matters": "The names are similar but not confidently identical.",
        "recommended_action": "Manually verify the names before submission."
    },
    "INVALID_FORMAT": {
        "why_it_matters": "The uploaded format does not satisfy the application requirement.",
        "recommended_action": "Convert and re-upload the file using an allowed format."
    },
    "FILE_TOO_LARGE": {
        "why_it_matters": "The file exceeds the configured size limit.",
        "recommended_action": "Compress or resize the file and upload it again."
    },
    "LOW_AI_CONFIDENCE": {
        "why_it_matters": "The AI could not confidently extract data from this document, increasing the risk of errors.",
        "recommended_action": "Manually verify the extracted fields against the original document."
    }
}

def generate_recommendations(issues: List[Issue]) -> List[Recommendation]:
    recommendations = []
    
    for issue in issues:
        template = RECOMMENDATION_TEMPLATES.get(issue.type)
        if not template:
            # Fallback for unknown issue types
            template = {
                "why_it_matters": f"An issue of type {issue.type} was detected.",
                "recommended_action": "Review the issue details and resolve it."
            }
            
        priority = PRIORITY_MAP.get(issue.severity.upper(), "LOW")
        
        rec = Recommendation(
            issue_type=issue.type,
            priority=priority,
            why_it_matters=template["why_it_matters"],
            recommended_action=template["recommended_action"]
        )
        recommendations.append(rec)
        
    return recommendations
