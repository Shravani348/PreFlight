import pytest
from backend.services.requirement_service import get_requirements, get_required_documents

def test_scholarship_requirements_load():
    reqs = get_requirements("scholarship")
    assert reqs.application_type == "scholarship"
    assert len(reqs.requirements) == 4

def test_required_documents_returned():
    docs = get_required_documents("scholarship")
    doc_types = [doc.document_type for doc in docs]
    assert "aadhaar" in doc_types
    assert "marksheet" in doc_types
    assert "income_certificate" in doc_types
    assert "photograph" in doc_types

def test_photograph_allowed_formats():
    reqs = get_requirements("scholarship")
    photo_req = next(req for req in reqs.requirements if req.document_type == "photograph")
    assert photo_req.allowed_formats == ["jpg", "jpeg"]

def test_photograph_max_size():
    reqs = get_requirements("scholarship")
    photo_req = next(req for req in reqs.requirements if req.document_type == "photograph")
    assert photo_req.max_size_kb == 200

def test_unsupported_application_type_raises_error():
    with pytest.raises(ValueError, match="Unsupported application type: college_admission"):
        get_requirements("college_admission")
