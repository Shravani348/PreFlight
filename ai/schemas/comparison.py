"""Comparison and cross-document schemas."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class FieldMatchResult:
    """Result of matching a specific field across documents."""

    field_name: str
    is_match: bool
    similarity_score: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossDocumentComparisonResult:
    """Result of comparing fields across multiple documents."""

    matched_fields: List[FieldMatchResult] = field(default_factory=list)
    has_mismatches: bool = False
