"""Top-level AI processing result schema."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field
from ai.schemas.comparison import ComparisonFinding
from ai.schemas.extraction import ExtractedDocument
from ai.schemas.instructions import InstructionRequirement


class AIProcessingResult(BaseModel):
    """Top-level unified AI processing result consumed by upstream callers."""

    model_config = ConfigDict(extra="allow")

    documents: List[ExtractedDocument] = Field(default_factory=list)
    cross_document_findings: List[ComparisonFinding] = Field(default_factory=list)
    instruction_requirements: List[InstructionRequirement] = Field(default_factory=list)
