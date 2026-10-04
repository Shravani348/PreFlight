"""Upload handling: validate files, run AI document intelligence, adapt for the Rule Engine."""

from pathlib import Path
from typing import List, Tuple

from backend.models.schemas import DocumentMetadata, Issue
from backend.services.ai_adapter import SLOT_TO_DOCUMENT_TYPE, adapt_ai_result
from backend.services.ai_service import UploadedDocument, process_uploads

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # matches the frontend upload limit


class UnknownSlotError(ValueError):
    """Raised when an upload field name is not a recognised document slot."""


def validate_slots(uploads: List[UploadedDocument]) -> None:
    for upload in uploads:
        if upload.slot not in SLOT_TO_DOCUMENT_TYPE:
            raise UnknownSlotError(f"Unknown document slot: {upload.slot}")


def _precheck(upload: UploadedDocument) -> Issue | None:
    """Reject files that can never be processed, before they reach the AI module."""
    declared = SLOT_TO_DOCUMENT_TYPE[upload.slot]
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return Issue(
            type="UNSUPPORTED_FILE_TYPE",
            severity="CRITICAL",
            message=f"Unsupported file type for {upload.filename}",
            evidence=[f"File: {upload.filename}", "Supported: PDF, JPG, JPEG, PNG"],
            document_type=declared,
        )
    if len(upload.content) == 0:
        return Issue(
            type="UNREADABLE_DOCUMENT",
            severity="CRITICAL",
            message=f"Could not read {upload.filename}",
            evidence=[f"File: {upload.filename}", "Reason: file is empty"],
            document_type=declared,
        )
    if len(upload.content) > MAX_UPLOAD_BYTES:
        return Issue(
            type="FILE_TOO_LARGE",
            severity="CRITICAL",
            message=f"{upload.filename} exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit",
            evidence=[f"Size: {len(upload.content) // 1024}KB"],
            document_type=declared,
        )
    return None


def analyze_uploads(
    uploads: List[UploadedDocument],
) -> Tuple[List[DocumentMetadata], List[Issue], dict]:
    """Return (documents for the Rule Engine, extra issues, structured AI analysis)."""
    validate_slots(uploads)

    issues: List[Issue] = []
    processable: List[UploadedDocument] = []
    for upload in uploads:
        problem = _precheck(upload)
        if problem is not None:
            issues.append(problem)
        else:
            processable.append(upload)

    if not processable:
        return [], issues, {}

    result, id_map = process_uploads(processable)
    adapted = adapt_ai_result(result, id_map)
    return adapted.documents, issues + adapted.issues, adapted.analysis
