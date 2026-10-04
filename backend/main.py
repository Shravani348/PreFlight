from fastapi import FastAPI, HTTPException
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse, Summary
from backend.services.requirement_service import get_requirements
from backend.services.rule_engine import validate_documents
from backend.services.risk_engine import calculate_risk
from backend.services.fix_plan import generate_fix_plan
from backend.services.ai_adapter import adapt_ai_output

app = FastAPI(title="PreFlight Backend")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "PreFlight Backend"
    }

def run_analysis_pipeline(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        app_reqs = get_requirements(request.application_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    req_docs = app_reqs.requirements
        
    ai_issues = adapt_ai_output(request.documents)
    issues = validate_documents(req_docs, request.documents)
    issues.extend(ai_issues)
    
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
        fix_plan=fix_plan
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
