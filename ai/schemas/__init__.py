"""Data schemas and Pydantic contracts for PreFlight AI module."""

from ai.schemas.comparison import ComparisonFinding, CrossDocumentFinding, MatchStatus
from ai.schemas.document import (
    ClassificationResult,
    DocumentMetadata,
    DocumentType,
    Evidence,
    ProcessingStatus,
)
from ai.schemas.extraction import ExtractedDocument, ExtractedField
from ai.schemas.instructions import InstructionRequirement
from ai.schemas.result import AIProcessingResult

__all__ = [
    "DocumentType",
    "ProcessingStatus",
    "Evidence",
    "ClassificationResult",
    "DocumentMetadata",
    "ExtractedField",
    "ExtractedDocument",
    "MatchStatus",
    "ComparisonFinding",
    "CrossDocumentFinding",
    "InstructionRequirement",
    "AIProcessingResult",
]
