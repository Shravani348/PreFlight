from typing import List
from backend.models.schemas import DocumentMetadata, Issue

CONFIDENCE_THRESHOLD = 0.85

def adapt_ai_output(documents: List[DocumentMetadata]) -> List[Issue]:
    """
    Checks the AI confidence for each document. 
    If confidence is below threshold, flags it as needing verification
    by returning a WARNING issue.
    """
    issues = []
    for doc in documents:
        if doc.confidence < CONFIDENCE_THRESHOLD:
            doc.extracted_data["needs_verification"] = True
            
            issues.append(Issue(
                type="LOW_AI_CONFIDENCE",
                severity="WARNING",
                message=f"AI extraction confidence is low ({doc.confidence}) for {doc.document_name}",
                evidence=[f"File: {doc.document_name}", f"Confidence: {doc.confidence}"],
                document_type=doc.document_type
            ))
    return issues
