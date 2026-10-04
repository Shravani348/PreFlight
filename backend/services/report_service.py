import re
from fpdf import FPDF
from datetime import datetime
from backend.models.schemas import AnalyzeResponse

def mask_sensitive_data(text: str) -> str:
    if not isinstance(text, str):
        return text
    # Mask Aadhaar (12 digits, optional spaces/dashes)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?(\d{4})\b', r'XXXX-XXXX-\1', text)
    # Mask PAN (5 letters, 4 numbers, 1 letter)
    text = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', r'XXXXX0000X', text)
    # The built-in PDF font is latin-1 only; replace other scripts (e.g. Devanagari)
    # rather than letting report generation fail.
    return text.encode("latin-1", "replace").decode("latin-1")

def generate_pdf_report(response: AnalyzeResponse) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "PreFlight Analysis Report", new_x="LMARGIN", new_y="NEXT", align="C")
    
    # Meta
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Application Type: Application", new_x="LMARGIN", new_y="NEXT") # We don't have this in response easily, just use generic or we could add it
    pdf.cell(0, 8, f"Status: {response.status}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Readiness Score: {response.readiness_score}/100", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Risk Level: {response.risk}", new_x="LMARGIN", new_y="NEXT")
    
    # Summary
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 6, f"Passed Checks: {response.summary.passed}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Warnings: {response.summary.warnings}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Critical Issues: {response.summary.critical}", new_x="LMARGIN", new_y="NEXT")
    
    # Critical Issues
    criticals = [i for i in response.issues if i.severity == "CRITICAL"]
    if criticals:
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 8, "Critical Issues", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        for issue in criticals:
            pdf.multi_cell(0, 6, text=mask_sensitive_data(f"- {issue.type}: {issue.message}"), new_x="LMARGIN", new_y="NEXT")
            
    # Warnings
    warnings = [i for i in response.issues if i.severity == "WARNING"]
    if warnings:
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 8, "Warnings", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        for issue in warnings:
            pdf.multi_cell(0, 6, text=mask_sensitive_data(f"- {issue.type}: {issue.message}"), new_x="LMARGIN", new_y="NEXT")
            
    # Fix Plan
    if response.fix_plan:
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 8, "Personalized Fix Plan", new_x="LMARGIN", new_y="NEXT")
        for step in response.fix_plan:
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 6, f"Step {step.step}: {step.title} ({step.priority})", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            pdf.multi_cell(0, 6, text=mask_sensitive_data(f"Action: {step.action}"), new_x="LMARGIN", new_y="NEXT")
            pdf.multi_cell(0, 6, text=mask_sensitive_data(f"Why: {step.why}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            
    # Evidence Summary
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 8, "Evidence Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    for issue in response.issues:
        if issue.evidence:
            evidence_str = ", ".join(issue.evidence)
            pdf.multi_cell(0, 6, text=mask_sensitive_data(f"Issue {issue.type}: {evidence_str}"), new_x="LMARGIN", new_y="NEXT")
            
    return pdf.output()
