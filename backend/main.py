from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from starlette.datastructures import UploadFile
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse, Issue, Summary
from backend.services.requirement_service import get_requirements
from backend.services.rule_engine import validate_documents
from backend.services.risk_engine import calculate_risk
from backend.services.fix_plan import generate_fix_plan
from backend.services.ai_adapter import adapt_ai_output
from backend.services.ai_service import UploadedDocument
from backend.services.upload_service import UnknownSlotError, analyze_uploads

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PreFlight Backend")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application types for which the AI document-intelligence module is implemented.
AI_SUPPORTED_APPLICATION_TYPES = {"scholarship"}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "PreFlight Backend"
    }

def run_analysis_pipeline(
    request: AnalyzeRequest,
    extra_issues: Optional[List[Issue]] = None,
    ai_analysis: Optional[dict] = None,
) -> AnalyzeResponse:
    try:
        app_reqs = get_requirements(request.application_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    req_docs = app_reqs.requirements
        
    ai_issues = adapt_ai_output(request.documents)
    issues = validate_documents(req_docs, request.documents)
    issues.extend(ai_issues)
    issues.extend(extra_issues or [])
    
    risk_assessment = calculate_risk(issues)
    fix_plan = generate_fix_plan(issues)
    
    if risk_assessment.critical_count > 0 or risk_assessment.warning_count > 0:
        status = "FIX_REQUIRED"
    else:
        status = "READY"
        
    message = "Ready to submit based on the configured checks." if status == "READY" else "Issues detected that require attention."
    
    passed_count = max(0, len(req_docs) * 2 - len(issues))
        
    summary = Summary(
        passed=passed_count,
        warnings=risk_assessment.warning_count,
        critical=risk_assessment.critical_count
    )
    
    return AnalyzeResponse(
        status=status,
        readiness_score=risk_assessment.readiness_score,
        risk=risk_assessment.risk,
        message=message,
        summary=summary,
        issues=issues,
        fix_plan=fix_plan,
        ai_analysis=ai_analysis
    )

import uuid
from fastapi.responses import Response
from backend.services.report_service import generate_pdf_report

# In-memory store for reports
REPORTS_DB = {}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    response = run_analysis_pipeline(request)
    report_id = str(uuid.uuid4())
    pdf_bytes = generate_pdf_report(response)
    REPORTS_DB[report_id] = pdf_bytes
    response.report_id = report_id
    return response

@app.post("/analyze-upload", response_model=AnalyzeResponse)
async def analyze_upload(request: Request):
    """Multipart upload: files -> AI document intelligence -> Rule Engine -> result.

    Form fields: ``application_type`` plus one file per document slot, where the
    field name is the slot id (e.g. ``aadhaar``, ``marksheet``, ``income_cert``,
    ``photo``, ``caste_cert``, ``application_form``, ``instructions``).
    Also serves rechecks: the client simply uploads the corrected files again.
    """
    form = await request.form()
    application_type = str(form.get("application_type") or "scholarship")
    if application_type not in AI_SUPPORTED_APPLICATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Document intelligence is not available for '{application_type}' applications yet. "
                   f"Supported: {', '.join(sorted(AI_SUPPORTED_APPLICATION_TYPES))}",
        )

    uploads: List[UploadedDocument] = []
    for slot, value in form.multi_items():
        if isinstance(value, UploadFile):
            uploads.append(UploadedDocument(
                slot=slot,
                filename=value.filename or "upload",
                content=await value.read(),
            ))
    if not uploads:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    try:
        documents, extra_issues, ai_analysis = analyze_uploads(uploads)
    except UnknownSlotError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response = run_analysis_pipeline(
        AnalyzeRequest(application_type=application_type, documents=documents),
        extra_issues=extra_issues,
        ai_analysis=ai_analysis,
    )
    report_id = str(uuid.uuid4())
    REPORTS_DB[report_id] = generate_pdf_report(response)
    response.report_id = report_id
    return response

@app.post("/recheck", response_model=AnalyzeResponse)
def recheck(request: AnalyzeRequest):
    response = run_analysis_pipeline(request)
    report_id = str(uuid.uuid4())
    pdf_bytes = generate_pdf_report(response)
    REPORTS_DB[report_id] = pdf_bytes
    response.report_id = report_id
    return response

@app.get("/report/{report_id}")
def get_report(report_id: str):
    if report_id not in REPORTS_DB:
        raise HTTPException(status_code=404, detail="Report not found")
    pdf_bytes = REPORTS_DB[report_id]
    return Response(content=bytes(pdf_bytes), media_type="application/pdf")
