"""Instruction and application rule schemas."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ApplicationInstruction:
    """Parsed application instruction or document requirement."""

    requirement_id: str
    description: str
    required_document_types: List[str] = field(default_factory=list)
    rules: Dict[str, Any] = field(default_factory=dict)
