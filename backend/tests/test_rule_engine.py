import pytest
from backend.models.schemas import Requirement, DocumentMetadata, Issue
from backend.services.rule_engine import validate_documents

def test_all_required_documents_provided():
    reqs = [
        Requirement(document_type="aadhaar", required=True),
        Requirement(document_type="marksheet", required=True)
    ]
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=100),
        DocumentMetadata(document_type="marksheet", format="pdf", size_kb=100)
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 0

def test_missing_required_document():
    reqs = [
        Requirement(document_type="aadhaar", required=True),
        Requirement(document_type="marksheet", required=True)
    ]
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=100)
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 1
    assert issues[0].type == "MISSING_DOCUMENT"
    assert issues[0].severity == "CRITICAL"
    assert issues[0].document_type == "marksheet"

def test_valid_file_format():
    reqs = [
        Requirement(document_type="aadhaar", required=True, allowed_formats=["pdf", "jpg"])
    ]
    provided = [
        DocumentMetadata(document_type="aadhaar", format="jpg", size_kb=100)
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 0

def test_invalid_file_format():
    reqs = [
        Requirement(document_type="aadhaar", required=True, allowed_formats=["pdf", "jpg"])
    ]
    provided = [
        DocumentMetadata(document_type="aadhaar", format="png", size_kb=100)
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 1
    assert issues[0].type == "INVALID_FORMAT"
    assert issues[0].severity == "WARNING"
    assert issues[0].document_type == "aadhaar"

def test_valid_file_size():
    reqs = [
        Requirement(document_type="aadhaar", required=True, max_size_kb=500)
    ]
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=250)
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 0

def test_oversized_file():
    reqs = [
        Requirement(document_type="aadhaar", required=True, max_size_kb=500)
    ]
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=600)
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 1
    assert issues[0].type == "FILE_TOO_LARGE"
    assert issues[0].severity == "WARNING"
    assert issues[0].document_type == "aadhaar"

def test_matching_dob():
    reqs = [Requirement(document_type="aadhaar", required=True)]
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=100, extracted_data={"dob": "15/08/1990"}),
        DocumentMetadata(document_type="pan", format="pdf", size_kb=100, extracted_data={"dob": "1990-08-15"})
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 0

def test_mismatching_dob():
    reqs = [Requirement(document_type="aadhaar", required=True)]
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=100, extracted_data={"dob": "15/08/1990"}),
        DocumentMetadata(document_type="pan", format="pdf", size_kb=100, extracted_data={"dob": "16/08/1990"})
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 1
    assert issues[0].type == "DOB_MISMATCH"
    assert issues[0].severity == "CRITICAL"

def test_matching_names():
    reqs = []
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=100, extracted_data={"name": "Rahul Kumar Sharma"}),
        DocumentMetadata(document_type="pan", format="pdf", size_kb=100, extracted_data={"name": "Rahul Kumar Sharma"})
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 0

def test_minor_name_variation():
    reqs = []
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=100, extracted_data={"name": "Rahul Kumar Sharma"}),
        DocumentMetadata(document_type="pan", format="pdf", size_kb=100, extracted_data={"name": "Rahul K. Sharma"})
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 0

def test_clear_name_mismatch():
    reqs = []
    provided = [
        DocumentMetadata(document_type="aadhaar", format="pdf", size_kb=100, extracted_data={"name": "Rahul Kumar Sharma"}),
        DocumentMetadata(document_type="pan", format="pdf", size_kb=100, extracted_data={"name": "Priya Singh"})
    ]
    issues = validate_documents(reqs, provided)
    assert len(issues) == 1
    assert issues[0].type == "NAME_MISMATCH"
    assert issues[0].severity == "CRITICAL"
