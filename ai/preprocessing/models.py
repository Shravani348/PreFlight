"""Data models representing preprocessed document content."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from PIL import Image


@dataclass
class PreprocessedPage:
    """Representation of an individual document page."""

    page_number: int
    text: Optional[str] = None
    images: List[Image.Image] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PreprocessedDocument:
    """Structured result produced by the document preprocessing pipeline."""

    file_path: str
    file_name: str
    file_type: str
    mime_type: str
    page_count: int
    full_text: Optional[str] = None
    page_texts: List[str] = field(default_factory=list)
    pages: List[PreprocessedPage] = field(default_factory=list)
    images: List[Image.Image] = field(default_factory=list)
    has_usable_text: bool = False
    requires_vision_processing: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
