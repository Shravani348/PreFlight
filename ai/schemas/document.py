"""Document-level schemas and types for PreFlight AI module."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Supported document types for scholarship applications."""

    APPLICATION_FORM = "application_form"
    AADHAAR_OR_IDENTITY = "aadhaar_or_identity"
    MARKSHEET = "marksheet"
    INCOME_CERTIFICATE = "income_certificate"
    CASTE_CERTIFICATE = "caste_certificate"
    PHOTOGRAPH = "photograph"
    INSTRUCTIONS = "instructions"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Processing status for a document."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Evidence(BaseModel):
    """Traceable evidence linking an extraction back to source document content."""

    model_config = ConfigDict(extra="forbid")

    source_document: Optional[str] = None
    page_number: Optional[int] = Field(default=None, ge=1)
    snippet: Optional[str] = None


class ClassificationResult(BaseModel):
    """Document classification result with confidence and verification flag."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    needs_verification: bool = False
    evidence: list[Evidence] = Field(default_factory=list)


class DocumentMetadata(BaseModel):
    """Document-level metadata and processing state."""

    model_config = ConfigDict(extra="allow")

    document_id: str
    file_name: Optional[str] = None
    document_type: DocumentType = DocumentType.UNKNOWN
    classification_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    page_count: Optional[int] = Field(default=None, ge=1)
    source_info: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)
