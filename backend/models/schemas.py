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
    extracted_data: dict = {}

class Issue(BaseModel):
    type: str
    severity: str
    message: str
    evidence: List[str] = []
    document_type: Optional[str] = None

class RiskAssessment(BaseModel):
    risk: str
    readiness_score: int
    critical_count: int
    warning_count: int
    info_count: int
    highest_risk_issue: Optional[Issue] = None
