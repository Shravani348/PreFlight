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
    document_name: str = "unknown"
    page: Optional[int] = None
    confidence: float = 1.0

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

class Recommendation(BaseModel):
    issue_type: str
    priority: str
    why_it_matters: str
    recommended_action: str

class FixPlanStep(BaseModel):
    step: int
    issue_type: str
    priority: str
    title: str
    action: str
    why: str
    evidence: List[str]

class AnalyzeRequest(BaseModel):
    application_type: str
    documents: List[DocumentMetadata]

class Summary(BaseModel):
    passed: int
    warnings: int
    critical: int

class AnalyzeResponse(BaseModel):
    status: str
    readiness_score: int
    risk: str
    message: str
    summary: Summary
    issues: List[Issue]
    fix_plan: List[FixPlanStep]
    report_id: Optional[str] = None
    # Structured AI document-intelligence output (only set by /analyze-upload).
    # Informational evidence for display; never used to decide status/risk.
    ai_analysis: Optional[dict] = None
