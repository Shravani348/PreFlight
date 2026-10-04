"""Instruction and guideline requirement schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from ai.schemas.document import DocumentType, Evidence


class InstructionRequirement(BaseModel):
    """Explicitly stated requirement extracted from application instructions."""

    model_config = ConfigDict(extra="allow")

    requirement_id: Optional[str] = None
    requirement_type: str
    document_type_requested: Optional[DocumentType] = None
    is_required: bool = True
    accepted_formats: List[str] = Field(default_factory=list)
    max_file_size_bytes: Optional[int] = Field(default=None, ge=1)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Evidence] = Field(default_factory=list)
