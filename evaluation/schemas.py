"""Pydantic schemas for AI evaluation test cases, ground truth, and metric reports."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from ai.schemas.comparison import MatchStatus
from ai.schemas.document import DocumentType


# ==============================================================================
# EVALUATION TEST CASE & GROUND TRUTH SCHEMAS
# ==============================================================================

class ClassificationTestCase(BaseModel):
    """Evaluation case for document classification."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    description: Optional[str] = None
    file_name: str
    text_content: Optional[str] = None
    has_image: bool = False
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    expected_document_type: DocumentType
    expected_needs_verification: Optional[bool] = None
    language: str = "english"
    document_condition: str = "clean"
    difficulty: str = "easy"


class MatchingTestCase(BaseModel):
    """Evaluation case for cross-document field matching."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    description: Optional[str] = None
    field_name: str
    value_a: Optional[str] = None
    value_b: Optional[str] = None
    expected_status: MatchStatus
    expected_needs_verification: Optional[bool] = None
    language: str = "english"
    document_condition: str = "clean"
    difficulty: str = "easy"


class InstructionTestCase(BaseModel):
    """Evaluation case for scholarship instructions extraction."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    description: Optional[str] = None
    instruction_text: str
    expected_requirement_types: List[str]
    expected_document_types: List[Optional[DocumentType]] = Field(default_factory=list)
    expected_constraints: Dict[str, Any] = Field(default_factory=dict)
    language: str = "english"
    document_condition: str = "clean"
    difficulty: str = "easy"


class FieldExtractionTestCase(BaseModel):
    """Evaluation case for structured field extraction from document content."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    description: Optional[str] = None
    document_type: DocumentType
    document_text: str
    expected_fields: Dict[str, Optional[str]]
    expected_normalized_fields: Dict[str, Optional[str]] = Field(default_factory=dict)
    language: str = "english"
    document_condition: str = "clean"
    difficulty: str = "easy"


# ==============================================================================
# BENCHMARK METRIC RESULT SCHEMAS
# ==============================================================================

class ClassificationMetrics(BaseModel):
    """Aggregated metrics for document classification."""

    model_config = ConfigDict(extra="allow")

    total_cases: int
    correct: int
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    per_class_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    by_language: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    by_condition: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    by_difficulty: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class MatchingMetrics(BaseModel):
    """Aggregated metrics for cross-document matching."""

    model_config = ConfigDict(extra="allow")

    total_cases: int
    correct: int
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    false_matches: int
    false_mismatches: int
    by_language: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    by_condition: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    by_difficulty: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class InstructionMetrics(BaseModel):
    """Aggregated metrics for instruction extraction."""

    model_config = ConfigDict(extra="allow")

    total_cases: int
    precision: float
    recall: float
    f1: float


class ExtractionMetrics(BaseModel):
    """Aggregated metrics for field extraction."""

    model_config = ConfigDict(extra="allow")

    total_fields: int
    exact_matches: int
    normalized_matches: int
    missing_fields: int
    exact_match_rate: float
    normalized_match_rate: float


class BenchmarkReport(BaseModel):
    """Complete benchmark execution report."""

    model_config = ConfigDict(extra="allow")

    dataset_name: str = "DEVELOPMENT / SYNTHETIC EVALUATION DATA"
    is_synthetic: bool = True
    disclaimer: str = (
        "These metrics evaluate framework integrity and baseline component logic on synthetic fixtures. "
        "They do NOT establish real-world production accuracy on live documents."
    )
    classification: Optional[ClassificationMetrics] = None
    matching: Optional[MatchingMetrics] = None
    instructions: Optional[InstructionMetrics] = None
    extraction: Optional[ExtractionMetrics] = None
