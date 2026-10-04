"""Extraction schemas."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ExtractedField:
    """A single extracted field from a document."""

    field_name: str
    raw_value: Any
    confidence: float
    normalized_value: Optional[Any] = None


@dataclass
class DocumentExtractionResult:
    """Collection of extracted fields for a document."""

    document_id: str
    fields: Dict[str, ExtractedField] = field(default_factory=dict)
