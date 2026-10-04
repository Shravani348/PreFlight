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
    },
    "DOB_NEEDS_VERIFICATION": {
        "why_it_matters": "The dates of birth are similar but not confidently identical.",
        "recommended_action": "Manually verify the date of birth against the official identity document."
    },
    "PARENT_NAME_MISMATCH": {
        "why_it_matters": "A parent's name differs across documents and may cause verification problems.",
        "recommended_action": "Check the parent's name on each document and correct the inconsistent one."
    },
    "PARENT_NAME_NEEDS_VERIFICATION": {
        "why_it_matters": "A parent's name is similar but not confidently identical across documents.",
        "recommended_action": "Manually verify the parent's name before submission."
    },
    "ADDRESS_MISMATCH": {
        "why_it_matters": "Different addresses across documents may need supporting proof.",
        "recommended_action": "Confirm the correct address and be ready to explain or document any change."
    },
    "ADDRESS_NEEDS_VERIFICATION": {
        "why_it_matters": "The addresses are similar but not confidently identical.",
        "recommended_action": "Manually verify the address on each document."
    },
    "DOCUMENT_TYPE_MISMATCH": {
        "why_it_matters": "The uploaded file does not look like the document type it was uploaded as.",
        "recommended_action": "Check that the correct document was uploaded in each slot."
    },
    "UNREADABLE_DOCUMENT": {
        "why_it_matters": "The file could not be opened or read, so it cannot be checked.",
        "recommended_action": "Re-scan or re-export the document and upload it again."
    },
    "UNSUPPORTED_FILE_TYPE": {
        "why_it_matters": "Only PDF, JPG, JPEG and PNG files can be checked.",
        "recommended_action": "Convert the file to PDF, JPG or PNG and upload it again."
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
