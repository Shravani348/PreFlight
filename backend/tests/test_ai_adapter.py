import pytest
import os
import json
from fastapi.testclient import TestClient
from backend.models.schemas import DocumentMetadata
from backend.services.ai_adapter import adapt_ai_output
from backend.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_dummy_requirements(tmp_path):
    req_dir = os.path.join(os.path.dirname(__file__), "..", "requirements")
    os.makedirs(req_dir, exist_ok=True)
    dummy_req = {
        "application_type": "test_ai",
        "requirements": [
            {
                "document_type": "aadhaar",
                "required": True,
                "allowed_formats": ["pdf"]
            }
        ]
    }
    with open(os.path.join(req_dir, "test_ai.json"), "w") as f:
        json.dump(dummy_req, f)
    yield
    if os.path.exists(os.path.join(req_dir, "test_ai.json")):
        os.remove(os.path.join(req_dir, "test_ai.json"))

def test_valid_ai_extraction():
    docs = [
        DocumentMetadata(
            document_type="aadhaar",
            format="pdf",
            size_kb=500,
            document_name="aadhaar.pdf",
            page=1,
            confidence=0.97,
            extracted_data={
                "name": "Rahul Kumar Sharma",
                "dob": "14/03/2005"
            }
        )
    ]
    issues = adapt_ai_output(docs)
    assert len(issues) == 0
    assert docs[0].extracted_data.get("needs_verification") is None

def test_low_confidence_extraction():
    docs = [
        DocumentMetadata(
            document_type="aadhaar",
            format="pdf",
            size_kb=500,
            document_name="aadhaar.pdf",
            confidence=0.60,
            extracted_data={"name": "Rahul"}
        )
    ]
    issues = adapt_ai_output(docs)
    assert len(issues) == 1
    assert issues[0].type == "LOW_AI_CONFIDENCE"
    assert issues[0].severity == "WARNING"
    assert docs[0].extracted_data.get("needs_verification") is True

def test_multiple_documents():
    docs = [
        DocumentMetadata(
            document_type="aadhaar",
            format="pdf",
            size_kb=500,
            confidence=0.90,
            extracted_data={}
        ),
        DocumentMetadata(
            document_type="pan",
            format="pdf",
            size_kb=500,
            confidence=0.70,
            extracted_data={}
        )
    ]
    issues = adapt_ai_output(docs)
    assert len(issues) == 1
    assert issues[0].document_type == "pan"

def test_missing_optional_field():
    doc = DocumentMetadata(
        document_type="aadhaar",
        format="pdf",
        size_kb=500,
        document_name="aadhaar.pdf",
        confidence=0.99,
        extracted_data={"name": "Rahul"}
    )
    assert doc.page is None
    issues = adapt_ai_output([doc])
    assert len(issues) == 0

def test_ai_output_passed_into_analyze():
    data = {
        "application_type": "test_ai",
        "documents": [
            {
                "document_type": "aadhaar",
                "document_name": "aadhaar.pdf",
                "format": "pdf",
                "size_kb": 500,
                "confidence": 0.5,
                "extracted_data": {"name": "Rahul"}
            }
        ]
    }
    response = client.post("/analyze", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "FIX_REQUIRED"
    issues = res_json["issues"]
    assert any(i["type"] == "LOW_AI_CONFIDENCE" for i in issues)
