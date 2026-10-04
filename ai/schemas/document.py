"""Document-related schemas."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class DocumentMetadata:
    """Metadata representing an uploaded document."""

    document_id: str
    file_name: str
    mime_type: str
    file_size_bytes: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentClassificationResult:
    """Result of document classification."""

    document_id: str
    document_type: str
    confidence: float
