import pytest
import os
import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_dummy_requirements(tmp_path):
    req_dir = os.path.join(os.path.dirname(__file__), "..", "requirements")
    os.makedirs(req_dir, exist_ok=True)
    dummy_req = {
        "application_type": "test_recheck",
        "requirements": [
            {
                "document_type": "aadhaar",
                "required": True,
                "allowed_formats": ["pdf"],
                "max_size_kb": 1000
            }
        ]
    }
    with open(os.path.join(req_dir, "test_recheck.json"), "w") as f:
        json.dump(dummy_req, f)
    yield
    if os.path.exists(os.path.join(req_dir, "test_recheck.json")):
        os.remove(os.path.join(req_dir, "test_recheck.json"))


def test_initial_problematic_data():
    data = {
        "application_type": "test_recheck",
        "documents": [
            {
                "document_type": "aadhaar",
                "document_name": "aadhaar.png",
                "format": "png",  # Warning issue
                "size_kb": 1500,  # Warning issue
                "confidence": 0.5, # Warning issue
                "extracted_data": {}
            }
        ]
    }
    response = client.post("/recheck", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "FIX_REQUIRED"
    assert res_json["summary"]["warnings"] == 3
    assert len(res_json["fix_plan"]) == 3
    assert res_json["risk"] == "MEDIUM"  # 3 warnings = 30 penalty
    assert res_json["readiness_score"] == 70

def test_corrected_data_ready():
    data = {
        "application_type": "test_recheck",
        "documents": [
            {
                "document_type": "aadhaar",
                "document_name": "aadhaar.pdf",
                "format": "pdf",
                "size_kb": 500,
                "confidence": 0.98,
                "extracted_data": {}
            }
        ]
    }
    response = client.post("/recheck", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "READY"
    assert res_json["risk"] == "LOW"
    assert res_json["readiness_score"] == 100
    assert len(res_json["issues"]) == 0
    assert len(res_json["fix_plan"]) == 0

def test_corrected_data_with_one_remaining_issue():
    data = {
        "application_type": "test_recheck",
        "documents": [
            {
                "document_type": "aadhaar",
                "document_name": "aadhaar.pdf",
                "format": "pdf",
                "size_kb": 1500,  # Still oversized
                "confidence": 0.95,
                "extracted_data": {}
            }
        ]
    }
    response = client.post("/recheck", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "FIX_REQUIRED"
    assert res_json["summary"]["warnings"] == 1
    assert len(res_json["issues"]) == 1
    assert len(res_json["fix_plan"]) == 1
    assert res_json["fix_plan"][0]["issue_type"] == "FILE_TOO_LARGE"
    assert res_json["readiness_score"] == 90
    assert res_json["risk"] == "LOW"

def test_recheck_missing_document():
    data = {
        "application_type": "test_recheck",
        "documents": []
    }
    response = client.post("/recheck", json=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "FIX_REQUIRED"
    assert res_json["summary"]["critical"] == 1
    assert res_json["risk"] == "MEDIUM"

def test_analyze_and_recheck_compatible():
    data = {
        "application_type": "test_recheck",
        "documents": []
    }
    res_analyze = client.post("/analyze", json=data)
    res_recheck = client.post("/recheck", json=data)
    
    assert res_analyze.status_code == 200
    assert res_recheck.status_code == 200
    
    res_analyze_json = res_analyze.json()
    res_recheck_json = res_recheck.json()
    
    res_analyze_json.pop("report_id", None)
    res_recheck_json.pop("report_id", None)
    
    assert res_analyze_json == res_recheck_json
