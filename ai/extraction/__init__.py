"""Information extraction package for PreFlight AI."""

from ai.extraction.extractor import DocumentExtractor
from ai.extraction.prompts import (
    SYSTEM_EXTRACTION_PROMPT,
    get_extraction_prompt,
)
from ai.extraction.vision_extractor import VisionExtractor

__all__ = [
    "DocumentExtractor",
    "VisionExtractor",
    "get_extraction_prompt",
    "SYSTEM_EXTRACTION_PROMPT",
]
