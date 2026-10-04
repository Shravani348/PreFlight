import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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


# ---------------------------------------------------------------------------
# AIProcessingResult -> backend contract
#
# The AI module reports *facts* (classification, fields, confidence, evidence,
# cross-document comparisons). This adapter translates them into the backend's
# DocumentMetadata / Issue vocabulary. Severity assignment lives here (backend
# side); the AI module never decides severity, status, risk or readiness.
# ---------------------------------------------------------------------------

# Upload slot id (frontend) -> backend requirement document_type.
SLOT_TO_DOCUMENT_TYPE: Dict[str, str] = {
    "application_form": "application_form",
    "aadhaar": "aadhaar",
    "marksheet": "marksheet",
    "income_cert": "income_certificate",
    "income_certificate": "income_certificate",
    "caste_cert": "caste_certificate",
    "caste_certificate": "caste_certificate",
    "photo": "photograph",
    "photograph": "photograph",
    "instructions": "instructions",
}

# AI DocumentType value -> backend requirement document_type.
AI_TO_DOCUMENT_TYPE: Dict[str, str] = {
    "application_form": "application_form",
    "aadhaar_or_identity": "aadhaar",
    "marksheet": "marksheet",
    "income_certificate": "income_certificate",
    "caste_certificate": "caste_certificate",
    "photograph": "photograph",
    "instructions": "instructions",
}

CORE_FIELDS = (
    "name", "date_of_birth", "father_name", "mother_name", "address",
    "certificate_number", "issue_date", "expiry_date", "marks", "percentage",
)

# AI comparison field -> issue type stem and the severity of a hard MISMATCH.
_FINDING_LABELS = {
    "name": "NAME",
    "date_of_birth": "DOB",
    "father_name": "PARENT_NAME",
    "mother_name": "PARENT_NAME",
    "address": "ADDRESS",
}
_CRITICAL_MISMATCH_FIELDS = {"name", "date_of_birth"}


@dataclass
class AdaptedAIResult:
    documents: List[DocumentMetadata] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    analysis: Dict[str, Any] = field(default_factory=dict)


def _field_payload(extracted_field: Any) -> Dict[str, Any]:
    return {
        "original": extracted_field.original,
        "normalized": extracted_field.normalized,
        "confidence": extracted_field.confidence,
        "evidence": [
            {"page": ev.page_number, "snippet": ev.snippet}
            for ev in extracted_field.evidence
        ],
    }


def _document_fields(ai_doc: Any) -> Dict[str, Dict[str, Any]]:
    """All extracted fields of an AI document (core + additional) with confidence/evidence."""
    fields: Dict[str, Dict[str, Any]] = {}
    for name in CORE_FIELDS:
        value = getattr(ai_doc, name, None)
        if value is not None:
            fields[name] = _field_payload(value)
    for name, value in (ai_doc.additional_fields or {}).items():
        if name != "processing_error" and value is not None:
            fields[name] = _field_payload(value)
    return fields


def _document_confidence(ai_type_value: str, fields: Dict[str, Dict[str, Any]], type_known: bool) -> float:
    """Conservative document-level confidence: the weakest field wins; nothing extracted -> 0.0.

    Photographs are never OCR'd by design; the Rule Engine only checks measured file
    facts (format, size), so extraction confidence does not apply. Any classification
    uncertainty stays visible in ``ai_analysis.verification``.
    """
    if not type_known:
        return 0.0
    if ai_type_value == "photograph":
        return 1.0
    scores = [
        (payload["confidence"] if payload["confidence"] is not None else 0.0)
        for payload in fields.values()
    ]
    return round(min(scores), 2) if scores else 0.0


def _first_page(fields: Dict[str, Dict[str, Any]]) -> Optional[int]:
    for payload in fields.values():
        for ev in payload["evidence"]:
            if ev["page"]:
                return ev["page"]
    return None


def _finding_issue(finding: Any) -> Optional[Issue]:
    status = finding.status.value
    if status in ("match", "missing"):
        return None
    if status == "likely_match" and not finding.needs_verification:
        return None

    label = _FINDING_LABELS.get(finding.field_name, finding.field_name.upper())
    if status == "mismatch":
        issue_type = f"{label}_MISMATCH"
        severity = "CRITICAL" if finding.field_name in _CRITICAL_MISMATCH_FIELDS else "WARNING"
    else:  # verification_required, or likely_match flagged by the AI for review
        issue_type = f"{label}_NEEDS_VERIFICATION"
        severity = "WARNING"

    evidence = [
        f"{finding.source_document} {finding.field_name}: {finding.source_value}",
        f"{finding.comparison_document} {finding.field_name}: {finding.comparison_value}",
    ]
    if finding.similarity_score is not None:
        evidence.append(f"Similarity: {finding.similarity_score:.2f}")
    if finding.explanation:
        evidence.append(finding.explanation)

    return Issue(
        type=issue_type,
        severity=severity,
        message=(
            f"{finding.field_name.replace('_', ' ').title()} "
            f"{'differs' if status == 'mismatch' else 'needs verification'} between "
            f"{finding.source_document} and {finding.comparison_document}"
        ),
        evidence=evidence,
    )


def adapt_ai_result(result: Any, uploads_by_id: Dict[str, Any]) -> AdaptedAIResult:
    """Translate an ``AIProcessingResult`` into backend documents, issues and analysis.

    ``uploads_by_id`` maps AI document ids (file names) to the uploads (``slot``,
    ``filename``, ``content``) they came from.
    """
    adapted = AdaptedAIResult()

    for ai_doc in result.documents:
        upload = uploads_by_id.get(ai_doc.document_id)
        declared = SLOT_TO_DOCUMENT_TYPE.get(upload.slot) if upload else None
        filename = upload.filename if upload else ai_doc.document_id

        if "processing_error" in (ai_doc.additional_fields or {}):
            reason = ai_doc.additional_fields["processing_error"].original
            adapted.issues.append(Issue(
                type="UNREADABLE_DOCUMENT",
                severity="CRITICAL",
                message=f"Could not read {filename}",
                evidence=[f"File: {filename}", f"Reason: {reason}"],
                document_type=declared,
            ))
            continue

        ai_type_value = ai_doc.document_type.value
        ai_type = AI_TO_DOCUMENT_TYPE.get(ai_type_value)
        type_known = ai_type is not None
        document_type = ai_type or declared or "unknown"

        if ai_type and declared and ai_type != declared:
            adapted.issues.append(Issue(
                type="DOCUMENT_TYPE_MISMATCH",
                severity="WARNING",
                message=f"{filename} was uploaded as {declared} but looks like {ai_type}",
                evidence=[f"Uploaded as: {declared}", f"AI classification: {ai_type}"],
                document_type=declared,
            ))

        fields = _document_fields(ai_doc)
        size_bytes = len(upload.content) if upload else 0
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        adapted.documents.append(DocumentMetadata(
            document_type=document_type,
            format=extension,
            size_kb=max(1, math.ceil(size_bytes / 1024)),
            document_name=filename,
            page=_first_page(fields),
            confidence=_document_confidence(ai_type_value, fields, type_known),
            # Name/DOB are deliberately NOT exposed under the legacy "name"/"dob" keys:
            # cross-document identity comparison is performed once, by the AI matcher
            # (family-member safe, cross-script aware), and surfaced via the findings below.
            extracted_data={
                "ai_document_type": ai_type_value,
                "declared_slot": upload.slot if upload else None,
                "type_verified_by_ai": type_known,
                "ai_fields": fields,
            },
        ))

    for finding in result.cross_document_findings:
        issue = _finding_issue(finding)
        if issue is not None:
            adapted.issues.append(issue)

    adapted.analysis = result.model_dump(mode="json")
    return adapted
