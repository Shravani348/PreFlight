import io
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.ai_service import UploadedDocument, _unique_name, get_pipeline, process_uploads, set_pipeline
from backend.services.upload_service import (
    MAX_UPLOAD_BYTES,
    UnknownSlotError,
    _precheck,
    analyze_uploads,
    validate_slots,
)

client = TestClient(app)


def test_validate_slots():
    valid = [
        UploadedDocument(slot="aadhaar", filename="aadhaar.pdf", content=b"123"),
        UploadedDocument(slot="marksheet", filename="marksheet.pdf", content=b"123"),
        UploadedDocument(slot="photo", filename="photo.jpg", content=b"123"),
    ]
    validate_slots(valid)  # Should not raise

    invalid = [
        UploadedDocument(slot="random_slot", filename="test.pdf", content=b"123"),
    ]
    try:
        validate_slots(invalid)
        assert False, "Should have raised UnknownSlotError"
    except UnknownSlotError as e:
        assert "Unknown document slot: random_slot" in str(e)


def test_precheck_unsupported_extension():
    up = UploadedDocument(slot="aadhaar", filename="aadhaar.exe", content=b"data")
    issue = _precheck(up)
    assert issue is not None
    assert issue.type == "UNSUPPORTED_FILE_TYPE"
    assert issue.severity == "CRITICAL"


def test_precheck_empty_file():
    up = UploadedDocument(slot="aadhaar", filename="aadhaar.pdf", content=b"")
    issue = _precheck(up)
    assert issue is not None
    assert issue.type == "UNREADABLE_DOCUMENT"
    assert issue.severity == "CRITICAL"


def test_precheck_too_large():
    up = UploadedDocument(slot="aadhaar", filename="aadhaar.pdf", content=b"x" * (MAX_UPLOAD_BYTES + 10))
    issue = _precheck(up)
    assert issue is not None
    assert issue.type == "FILE_TOO_LARGE"
    assert issue.severity == "CRITICAL"


def test_precheck_valid():
    up = UploadedDocument(slot="aadhaar", filename="aadhaar.pdf", content=b"x" * 1024)
    issue = _precheck(up)
    assert issue is None


def test_unique_name():
    taken = {"doc.pdf", "doc (2).pdf"}
    assert _unique_name("new.pdf", taken) == "new.pdf"
    assert _unique_name("doc.pdf", taken) == "doc (3).pdf"


def test_pipeline_singleton():
    pipe1 = get_pipeline()
    pipe2 = get_pipeline()
    assert pipe1 is pipe2
    set_pipeline(None)
    pipe3 = get_pipeline()
    assert pipe3 is not None


from fpdf import FPDF

def _make_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in text.split("\n"):
        if line:
            pdf.cell(0, 10, text=line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def test_analyze_uploads_end_to_end():
    sample_text = (
        "GOVERNMENT OF INDIA\nAADHAAR CARD\nName: Priya Suresh Patil\nDOB: 15/08/2004\nGender: Female"
    )
    pdf_bytes = _make_pdf(sample_text)
    uploads = [
        UploadedDocument(slot="aadhaar", filename="aadhaar.pdf", content=pdf_bytes),
    ]
    docs, issues, analysis = analyze_uploads(uploads)
    assert len(docs) == 1
    assert docs[0].document_type == "aadhaar"
    assert "ai_document_type" in docs[0].extracted_data
    assert isinstance(analysis, dict)


def test_analyze_upload_api_unsupported_app_type():
    res = client.post(
        "/analyze-upload",
        data={"application_type": "invalid_type"},
        files={"aadhaar": ("test.pdf", b"%PDF-dummy", "application/pdf")},
    )
    assert res.status_code == 400
    assert "Document intelligence is not available" in res.json()["detail"]


def test_analyze_upload_api_no_files():
    res = client.post(
        "/analyze-upload",
        data={"application_type": "scholarship"},
    )
    assert res.status_code == 400
    assert "No files were uploaded" in res.json()["detail"]


def test_analyze_upload_api_unknown_slot():
    res = client.post(
        "/analyze-upload",
        data={"application_type": "scholarship"},
        files={"invalid_slot": ("test.pdf", b"%PDF-dummy", "application/pdf")},
    )
    assert res.status_code == 400
    assert "Unknown document slot: invalid_slot" in res.json()["detail"]


def test_analyze_upload_api_success_and_report_download():
    # Provide synthetic documents matching scholarship slots
    aadhaar_content = _make_pdf(
        "GOVERNMENT OF INDIA\nAADHAAR\nName: Rahul Kumar Sharma\nDOB: 14/03/2005\nGender: Male"
    )
    marksheet_content = _make_pdf(
        "BOARD OF HIGHER SECONDARY EDUCATION\nMARKSHEET\nName: Rahul Kumar Sharma\nPercentage: 85%"
    )
    income_content = _make_pdf(
        "GOVERNMENT OF MAHARASHTRA\nINCOME CERTIFICATE\nName: Rahul Kumar Sharma\nAnnual Income: Rs. 150000"
    )
    app_form_content = _make_pdf(
        "SCHOLARSHIP APPLICATION FORM\nName: Rahul Kumar Sharma\nDOB: 14/03/2005"
    )
    photo_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb"  # JPEG magic

    files = [
        ("aadhaar", ("aadhaar.pdf", aadhaar_content, "application/pdf")),
        ("marksheet", ("marksheet.pdf", marksheet_content, "application/pdf")),
        ("income_cert", ("income_cert.pdf", income_content, "application/pdf")),
        ("application_form", ("form.pdf", app_form_content, "application/pdf")),
        ("photo", ("photo.jpg", photo_content, "image/jpeg")),
    ]

    res = client.post(
        "/analyze-upload",
        data={"application_type": "scholarship"},
        files=files,
    )
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "risk" in data
    assert "readiness_score" in data
    assert "summary" in data
    assert "issues" in data
    assert "fix_plan" in data
    assert "report_id" in data
    assert data["ai_analysis"] is not None

    # Now verify report download
    report_id = data["report_id"]
    report_res = client.get(f"/report/{report_id}")
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
    assert len(report_res.content) > 100
