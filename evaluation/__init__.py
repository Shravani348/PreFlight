"""PreFlight AI Evaluation and Benchmarking Framework."""

from evaluation.metrics import (
    calculate_classification_metrics,
    calculate_extraction_metrics,
    calculate_instruction_metrics,
    calculate_matching_metrics,
)
from evaluation.schemas import (
    ClassificationMetrics,
    ClassificationTestCase,
    ExtractionMetrics,
    FieldExtractionTestCase,
    InstructionMetrics,
    InstructionTestCase,
    MatchingMetrics,
    MatchingTestCase,
)

__all__ = [
    "ClassificationTestCase",
    "MatchingTestCase",
    "InstructionTestCase",
    "FieldExtractionTestCase",
    "ClassificationMetrics",
    "MatchingMetrics",
    "InstructionMetrics",
    "ExtractionMetrics",
    "calculate_classification_metrics",
    "calculate_matching_metrics",
    "calculate_instruction_metrics",
    "calculate_extraction_metrics",
]
