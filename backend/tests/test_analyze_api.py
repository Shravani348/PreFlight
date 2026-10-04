import pytest
import os
import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Helper to create a dummy requirement for testing
@pytest.fixture(autouse=True)
def setup_dummy_requirements(tmp_path):
    req_dir = os.path.join(os.path.dirname(__file__), "..", "requirements")
    os.makedirs(req_dir, exist_ok=True)
    dummy_req = {
        "application_type": "test_app",
        "requirements": [
            {
                "document_type": "id_card",
                "required": True,
                "allowed_formats": ["pdf"],
                "max_size_kb": 1000
            }
        ]
    }
    with open(os.path.join(req_dir, "test_app.json"), "w") as f:
        json.dump(dummy_req, f)
    yield
    # Cleanup (optional but good practice)
    os.remove(os.path.join(req_dir, "test_app.json"))

def test_valid_application():
    data = {
        "application_type": "test_app",
        "documents": [
            {
                "document_type": "id_card",
                "format": "pdf",
                "size_kb": 500,
                "extracted_data": {}
            }
        ]
    }
    response = client.post("/analyze", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "READY"
    assert res_json["readiness_score"] == 100
    assert res_json["risk"] == "LOW"
    assert len(res_json["issues"]) == 0
    assert len(res_json["fix_plan"]) == 0

def test_missing_required_document():
    data = {
        "application_type": "test_app",
        "documents": []
    }
    response = client.post("/analyze", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "FIX_REQUIRED"
    assert res_json["summary"]["critical"] == 1
    assert res_json["issues"][0]["type"] == "MISSING_DOCUMENT"
    assert len(res_json["fix_plan"]) == 1

def test_invalid_file_format():
    data = {
        "application_type": "test_app",
        "documents": [
            {
                "document_type": "id_card",
                "format": "png",
                "size_kb": 500,
                "extracted_data": {}
            }
        ]
    }
    response = client.post("/analyze", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "FIX_REQUIRED"
    assert res_json["summary"]["warnings"] == 1
    assert res_json["issues"][0]["type"] == "INVALID_FORMAT"

def test_dob_mismatch():
    data = {
        "application_type": "test_app",
        "documents": [
            {
                "document_type": "id_card",
                "format": "pdf",
                "size_kb": 500,
                "extracted_data": {"dob": "10/10/1990"}
            },
            {
                "document_type": "other_doc",
                "format": "pdf",
                "size_kb": 500,
                "extracted_data": {"dob": "11/10/1990"}
            }
        ]
    }
    response = client.post("/analyze", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "FIX_REQUIRED"
    issue_types = [i["type"] for i in res_json["issues"]]
    assert "DOB_MISMATCH" in issue_types

def test_multiple_issues():
    data = {
        "application_type": "test_app",
        "documents": [
            {
                "document_type": "id_card",
                "format": "png",  # Warning
                "size_kb": 2000,  # Warning
                "extracted_data": {}
            }
        ]
    }
    response = client.post("/analyze", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "FIX_REQUIRED"
    assert res_json["summary"]["warnings"] == 2
    assert "readiness_score" in res_json
    assert "risk" in res_json
    assert "summary" in res_json
    assert "fix_plan" in res_json
    assert len(res_json["fix_plan"]) == 2
