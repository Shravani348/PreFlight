"""Extraction schemas for document fields and complete documents."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from ai.schemas.document import DocumentType, Evidence


class ExtractedField(BaseModel):
    """Reusable extracted field schema preserving raw and normalized values."""

    model_config = ConfigDict(extra="allow")

    field_name: str
    original: Optional[Any] = None
    normalized: Optional[Any] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)


class ExtractedDocument(BaseModel):
    """Extracted data from a single document across supported scholarship types."""

    model_config = ConfigDict(extra="allow")

    document_id: str
    document_type: DocumentType = DocumentType.UNKNOWN

    # Core individual identity fields (optional per document type)
    name: Optional[ExtractedField] = None
    date_of_birth: Optional[ExtractedField] = None
    father_name: Optional[ExtractedField] = None
    mother_name: Optional[ExtractedField] = None
    address: Optional[ExtractedField] = None

    # Certificate & validity fields
    certificate_number: Optional[ExtractedField] = None
    issue_date: Optional[ExtractedField] = None
    expiry_date: Optional[ExtractedField] = None

    # Academic fields
    marks: Optional[ExtractedField] = None
    percentage: Optional[ExtractedField] = None

    # Extensible field container for future or document-specific fields
    additional_fields: Dict[str, ExtractedField] = Field(default_factory=dict)
