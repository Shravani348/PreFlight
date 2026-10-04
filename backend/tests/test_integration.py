import pytest
import os
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.schemas import AnalyzeResponse

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_dummy_requirements(tmp_path):
    req_dir = os.path.join(os.path.dirname(__file__), "..", "requirements")
    os.makedirs(req_dir, exist_ok=True)
    dummy_req = {
        "application_type": "integration_test_app",
        "requirements": [
            {
                "document_type": "aadhaar",
                "required": True,
                "allowed_formats": ["pdf"],
                "max_size_kb": 1000
            },
            {
                "document_type": "marksheet",
                "required": True,
                "allowed_formats": ["pdf"],
                "max_size_kb": 1000
            }
        ]
    }
    with open(os.path.join(req_dir, "integration_test_app.json"), "w") as f:
        json.dump(dummy_req, f)
    yield
    if os.path.exists(os.path.join(req_dir, "integration_test_app.json")):
        os.remove(os.path.join(req_dir, "integration_test_app.json"))

def test_full_integration_flow():
    """
    Tests the complete end-to-end flow:
    AI output -> AI adapter -> Rule Engine -> Risk Engine -> Recommendation Engine -> Fix Plan -> API response
    """
    mock_ai_output = {
        "application_type": "integration_test_app",
        "documents": [
            {
                "document_type": "aadhaar",
                "document_name": "aadhaar_scan.pdf",
                "format": "pdf",
                "size_kb": 500,
                "page": 1,
                "confidence": 0.60, # Will trigger AI adapter warning
                "extracted_data": {
                    "name": "Rahul Kumar Sharma",
                    "dob": "14-03-2005"
                }
            },
            {
                "document_type": "marksheet",
                "document_name": "marksheet.png", # Invalid format based on requirements (but marksheet isn't required in dummy_req, wait, if it's there it might trigger format check if rule engine checks all provided docs)
                "format": "png",
                "size_kb": 2500, # Too large
                "page": 1,
                "confidence": 0.95,
                "extracted_data": {
                    "name": "Rahul Sharma", # Name mismatch
                    "dob": "14/03/2005"
                }
            }
        ]
    }
    
    response = client.post("/analyze", json=mock_ai_output)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "FIX_REQUIRED"
    assert data["risk"] in ["MEDIUM", "HIGH"]
    assert "report_id" in data
    
    issue_types = [issue["type"] for issue in data["issues"]]
    # Should contain low AI confidence from adapter
    assert "LOW_AI_CONFIDENCE" in issue_types
    
    # Check fix plan is correctly populated
    assert len(data["fix_plan"]) > 0
    assert data["fix_plan"][0]["step"] == 1
    
    # We generated a report, let's test fetching it
    report_id = data["report_id"]
    report_res = client.get(f"/report/{report_id}")
    assert report_res.status_code == 200
    assert report_res.headers["content-type"] == "application/pdf"
