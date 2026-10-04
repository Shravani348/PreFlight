from pydantic import BaseModel
from typing import List, Optional

class Requirement(BaseModel):
    document_type: str
    required: bool
    allowed_formats: Optional[List[str]] = None
    max_size_kb: Optional[int] = None

class ApplicationRequirements(BaseModel):
    application_type: str
    requirements: List[Requirement]

class DocumentMetadata(BaseModel):
    document_type: str
    format: str
    size_kb: int
