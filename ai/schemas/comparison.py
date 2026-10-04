"""Comparison and cross-document matching schemas."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class MatchStatus(str, Enum):
    """Status outcomes for cross-document field comparisons."""

    MATCH = "match"
    LIKELY_MATCH = "likely_match"
    VERIFICATION_REQUIRED = "verification_required"
    MISMATCH = "mismatch"
    MISSING = "missing"


class ComparisonFinding(BaseModel):
    """Finding resulting from comparing a field across two documents."""

    model_config = ConfigDict(extra="forbid")

    field_name: str
    source_document: str
    comparison_document: str

    source_value: Optional[Any] = None
    comparison_value: Optional[Any] = None

    normalized_source_value: Optional[Any] = None
    normalized_comparison_value: Optional[Any] = None

    similarity_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    status: MatchStatus
    needs_verification: bool = False
    explanation: Optional[str] = None


# Alias for explicit naming
CrossDocumentFinding = ComparisonFinding
