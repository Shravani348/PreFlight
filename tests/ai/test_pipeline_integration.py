"""Comprehensive integration and orchestration tests for PreFlight AI Pipeline."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
from PIL import Image

from ai.exceptions import DocumentNotFoundError, DocumentProcessingError
from ai.extraction.vision_extractor import VisionExtractor
from ai.pipeline import AIPipeline, PreFlightAIPipeline
from ai.preprocessing.models import PreprocessedDocument, PreprocessedPage
from ai.schemas.comparison import MatchStatus
from ai.schemas.document import DocumentType
from ai.schemas.extraction import ExtractedDocument, ExtractedField
from ai.schemas.result import AIProcessingResult
from ai.verification.confidence_service import ConfidenceLevel


# ==============================================================================
# SYNTHETIC TEST FIXTURES / HELPERS
# ==============================================================================

def make_page(page_num: int, text: str) -> PreprocessedPage:
    return PreprocessedPage(page_number=page_num, text=text)


def make_doc(
    name: str,
    text: str,
    images: Optional[list] = None,
    page_count: int = 1,
) -> PreprocessedDocument:
    return PreprocessedDocument(
        file_path=name,
        file_name=name,
        file_type="pdf" if name.endswith(".pdf") else "image",
        mime_type="application/pdf" if name.endswith(".pdf") else "image/jpeg",
        page_count=page_count,
        full_text=text,
        page_texts=[text],
        pages=[make_page(1, text)],
        images=images or [],
        has_usable_text=bool(text and text.strip()),
    )


def synthetic_model_client(
    prompt: str,
    text: Optional[str],
    images: Optional[list],
    doc_type: DocumentType,
) -> Dict[str, Any]:
    """Offline deterministic model client mocking vision extraction for pipeline tests."""
    if not text:
        return {}

    res: Dict[str, Any] = {}
    confidence_map: Dict[str, float] = {}
    evidence_map: Dict[str, str] = {}

    # Name
    m_name = re.search(r"(?:Name|Applicant(?:\s+Name)?|Candidate(?:\s+Name)?)\s*:\s*([A-Za-z\s.]+?)(?:\n|$)", text, re.I)
    if m_name:
        val = m_name.group(1).strip()
        res["name"] = {"value": val, "confidence": 0.96, "snippet": m_name.group(0).strip()}

    # DOB
    m_dob = re.search(r"(?:DOB|Date of Birth)\s*:\s*([0-9\-/]+)(?:\n|$)", text, re.I)
    if m_dob:
        val = m_dob.group(1).strip()
        res["date_of_birth"] = {"value": val, "confidence": 0.95, "snippet": m_dob.group(0).strip()}

    # Father name
    m_father = re.search(r"(?:Father(?:'s)?\s*Name)\s*:\s*([A-Za-z\s.]+?)(?:\n|$)", text, re.I)
    if m_father:
        val = m_father.group(1).strip()
        res["father_name"] = {"value": val, "confidence": 0.90, "snippet": m_father.group(0).strip()}

    # Mother name
    m_mother = re.search(r"(?:Mother(?:'s)?\s*Name)\s*:\s*([A-Za-z\s.]+?)(?:\n|$)", text, re.I)
    if m_mother:
        val = m_mother.group(1).strip()
        res["mother_name"] = {"value": val, "confidence": 0.90, "snippet": m_mother.group(0).strip()}

    # Address
    m_addr = re.search(r"(?:Address)\s*:\s*([^\n]+)(?:\n|$)", text, re.I)
    if m_addr:
        val = m_addr.group(1).strip()
        res["address"] = {"value": val, "confidence": 0.88, "snippet": m_addr.group(0).strip()}

    # Certificate Number
    m_cert = re.search(r"(?:Certificate\s*(?:Number|No\.?)|Seat\s*No\.?)\s*:\s*([A-Za-z0-9/\-]+)(?:\n|$)", text, re.I)
    if m_cert:
        val = m_cert.group(1).strip()
        res["certificate_number"] = {"value": val, "confidence": 0.94, "snippet": m_cert.group(0).strip()}

    # Issue Date
    m_iss = re.search(r"(?:Issue\s*Date)\s*:\s*([0-9\-/]+)(?:\n|$)", text, re.I)
    if m_iss:
        val = m_iss.group(1).strip()
        res["issue_date"] = {"value": val, "confidence": 0.92, "snippet": m_iss.group(0).strip()}

    # Expiry Date
    m_exp = re.search(r"(?:Expiry\s*Date)\s*:\s*([0-9\-/]+)(?:\n|$)", text, re.I)
    if m_exp:
        val = m_exp.group(1).strip()
        res["expiry_date"] = {"value": val, "confidence": 0.92, "snippet": m_exp.group(0).strip()}

    # Marks
    m_marks = re.search(r"(?:Total\s*Marks|Marks)\s*:\s*([0-9/]+)(?:\n|$)", text, re.I)
    if m_marks:
        val = m_marks.group(1).strip()
        res["marks"] = {"value": val, "confidence": 0.93, "snippet": m_marks.group(0).strip()}

    # Percentage
    m_pct = re.search(r"(?:Percentage)\s*:\s*([0-9.]+%?)(?:\n|$)", text, re.I)
    if m_pct:
        val = m_pct.group(1).strip()
        res["percentage"] = {"value": val, "confidence": 0.94, "snippet": m_pct.group(0).strip()}

    # Additional fields
    additional = {}
    m_inc = re.search(r"(?:Annual\s*Income)\s*:\s*([^\n]+)(?:\n|$)", text, re.I)
    if m_inc:
        additional["annual_income"] = {"value": m_inc.group(1).strip(), "confidence": 0.95}

    m_cat = re.search(r"(?:Category)\s*:\s*([^\n]+)(?:\n|$)", text, re.I)
    if m_cat:
        additional["category"] = {"value": m_cat.group(1).strip(), "confidence": 0.95}

    if additional:
        res["additional_fields"] = additional

    res["confidence_scores"] = confidence_map
    res["evidence"] = evidence_map
    return res


def create_test_pipeline(model_client=synthetic_model_client, **kwargs) -> AIPipeline:
    """Create AIPipeline configured with an offline mock VisionExtractor."""
    vision_extractor = VisionExtractor(model_client=model_client)
    return AIPipeline(vision_extractor=vision_extractor, **kwargs)


# ==============================================================================
# 1. BASIC PIPELINE TESTS (1 - 5)
# ==============================================================================

def test_empty_document_list() -> None:
    """1. Empty document input returns clean AIProcessingResult."""
    pipeline = create_test_pipeline()
    result = pipeline.process([])
    assert isinstance(result, AIProcessingResult)
    assert result.documents == []
    assert result.cross_document_findings == []
    assert result.instruction_requirements == []
    assert result.verification.verification_required is False


def test_one_valid_pdf() -> None:
    """2. Single valid PDF preprocessed document executes through pipeline."""
    pipeline = create_test_pipeline()
    doc = make_doc(
        "app.pdf",
        "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Shashikant Ahire\nDOB: 01/05/2005",
    )
    result = pipeline.process([doc])
    assert len(result.documents) == 1
    assert result.documents[0].document_type == DocumentType.APPLICATION_FORM
    assert result.documents[0].name.normalized == "priti shashikant ahire"


def test_one_valid_image() -> None:
    """3. Single valid image executes through pipeline without OCR failure."""
    pipeline = create_test_pipeline()
    img = Image.new("RGB", (200, 200), color="white")
    doc = make_doc("photo_applicant.jpg", "", images=[img])
    result = pipeline.process([doc])
    assert len(result.documents) == 1
    assert result.documents[0].document_type == DocumentType.PHOTOGRAPH


def test_multiple_documents() -> None:
    """4. Multiple documents processed together in one pipeline run."""
    pipeline = create_test_pipeline()
    d1 = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire\nDOB: 01/05/2005")
    d2 = make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nName: Priti Ahire\nDOB: 01/05/2005")
    result = pipeline.process([d1, d2])
    assert len(result.documents) == 2
    assert len(result.cross_document_findings) >= 1


def test_scholarship_document_set() -> None:
    """5. Full scholarship application document set integration."""
    pipeline = create_test_pipeline()
    docs = [
        make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire\nDOB: 01/05/2005"),
        make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nName: Priti Ahire\nDOB: 01/05/2005"),
        make_doc("marksheet.pdf", "BOARD OF SECONDARY EDUCATION STATEMENT OF MARKS\nName: Priti Ahire\nTotal Marks: 450/500\nPercentage: 90%"),
        make_doc("income.pdf", "INCOME CERTIFICATE TAHSILDAR REVENUE DEPARTMENT\nName: Priti Ahire\nAnnual Income: Rs. 150000"),
        make_doc("caste.pdf", "COMMUNITY CASTE CERTIFICATE SUB DIVISIONAL MAGISTRATE\nName: Priti Ahire\nCategory: SC"),
        make_doc("photo.jpg", "", images=[Image.new("RGB", (100, 100))]),
        make_doc("instructions.pdf", "GENERAL INSTRUCTIONS TO CANDIDATES\nRequired documents: Aadhaar card must be uploaded."),
    ]
    result = pipeline.process(docs)
    assert len(result.documents) == 7
    assert len(result.cross_document_findings) >= 1
    assert len(result.instruction_requirements) >= 1
    assert isinstance(result, AIProcessingResult)


# ==============================================================================
# 2. CLASSIFICATION INTEGRATION TESTS (6 - 13)
# ==============================================================================

def test_classification_application_form() -> None:
    """6. Pipeline correctly classifies scholarship application form."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA STATE SCHOLARSHIP APPLICATION FORM\nApplication ID: 98765")
    result = pipeline.process([doc])
    assert result.documents[0].document_type == DocumentType.APPLICATION_FORM


def test_classification_identity_document() -> None:
    """7. Pipeline correctly classifies identity document."""
    pipeline = create_test_pipeline()
    doc = make_doc("id.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR")
    result = pipeline.process([doc])
    assert result.documents[0].document_type == DocumentType.AADHAAR_OR_IDENTITY


def test_classification_marksheet() -> None:
    """8. Pipeline correctly classifies marksheet."""
    pipeline = create_test_pipeline()
    doc = make_doc("m.pdf", "BOARD OF SECONDARY EDUCATION STATEMENT OF MARKS\nSeat No: 12345")
    result = pipeline.process([doc])
    assert result.documents[0].document_type == DocumentType.MARKSHEET


def test_classification_income_certificate() -> None:
    """9. Pipeline correctly classifies income certificate."""
    pipeline = create_test_pipeline()
    doc = make_doc("i.pdf", "INCOME CERTIFICATE TAHSIL OFFICE REVENUE DEPARTMENT\nAnnual Income: Rs. 1,00,000")
    result = pipeline.process([doc])
    assert result.documents[0].document_type == DocumentType.INCOME_CERTIFICATE


def test_classification_caste_certificate() -> None:
    """10. Pipeline correctly classifies caste certificate."""
    pipeline = create_test_pipeline()
    doc = make_doc("c.pdf", "COMMUNITY CASTE CERTIFICATE SUB DIVISIONAL OFFICER\nCategory: SC")
    result = pipeline.process([doc])
    assert result.documents[0].document_type == DocumentType.CASTE_CERTIFICATE


def test_classification_photograph() -> None:
    """11. Pipeline correctly classifies applicant photograph."""
    pipeline = create_test_pipeline()
    doc = make_doc("passport_photo.png", "", images=[Image.new("RGB", (100, 100))])
    result = pipeline.process([doc])
    assert result.documents[0].document_type == DocumentType.PHOTOGRAPH


def test_classification_instructions() -> None:
    """12. Pipeline correctly classifies scholarship instructions."""
    pipeline = create_test_pipeline()
    doc = make_doc("instructions.pdf", "GENERAL INSTRUCTIONS TO CANDIDATES\nRequired documents: Aadhaar card must be uploaded.")
    result = pipeline.process([doc])
    assert result.documents[0].document_type == DocumentType.INSTRUCTIONS


def test_classification_unknown_document() -> None:
    """13. Pipeline handles completely unknown document without guessing."""
    pipeline = create_test_pipeline()
    doc = make_doc("invoice.pdf", "Commercial invoice 12345 for computer parts and hardware supplies.")
    result = pipeline.process([doc])
    assert result.documents[0].document_type == DocumentType.UNKNOWN


# ==============================================================================
# 3. EXTRACTION INTEGRATION TESTS (14 - 18)
# ==============================================================================

def test_extracted_name_preserved() -> None:
    """14. Name field is cleanly extracted and preserved in original form."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Shashikant Ahire")
    result = pipeline.process([doc])
    assert result.documents[0].name is not None
    assert result.documents[0].name.original == "Priti Shashikant Ahire"


def test_extracted_dob_preserved() -> None:
    """15. Date of birth is cleanly extracted and preserved."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nDOB: 15/08/2004")
    result = pipeline.process([doc])
    assert result.documents[0].date_of_birth is not None
    assert result.documents[0].date_of_birth.original == "15/08/2004"


def test_extracted_certificate_number_preserved() -> None:
    """16. Certificate number is preserved without modification."""
    pipeline = create_test_pipeline()
    doc = make_doc("caste.pdf", "COMMUNITY CASTE CERTIFICATE SUB DIVISIONAL OFFICER\nCertificate Number: CST/2026/8901")
    result = pipeline.process([doc])
    assert result.documents[0].certificate_number is not None
    assert result.documents[0].certificate_number.original == "CST/2026/8901"


def test_extracted_percentage_preserved() -> None:
    """17. Academic percentage is preserved."""
    pipeline = create_test_pipeline()
    doc = make_doc("m.pdf", "BOARD OF SECONDARY EDUCATION STATEMENT OF MARKS\nPercentage: 88.5%")
    result = pipeline.process([doc])
    assert result.documents[0].percentage is not None
    assert result.documents[0].percentage.original == "88.5%"


def test_missing_field_remains_none() -> None:
    """18. Non-existent field strictly remains None without guessing."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    result = pipeline.process([doc])
    assert result.documents[0].date_of_birth is None
    assert result.documents[0].certificate_number is None


# ==============================================================================
# 4. NORMALIZATION INTEGRATION TESTS (19 - 21)
# ==============================================================================

def test_original_value_preserved() -> None:
    """19. Normalization never overwrites or mutates original value."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti   S.   Ahire")
    result = pipeline.process([doc])
    assert result.documents[0].name.original == "Priti   S.   Ahire"
    assert result.documents[0].name.normalized == "priti s ahire"


def test_normalized_name_available() -> None:
    """20. Normalized lowercase cleaned name available for matching."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: PRITI SHASHIKANT AHIRE")
    result = pipeline.process([doc])
    assert result.documents[0].name.normalized == "priti shashikant ahire"


def test_normalized_date_available() -> None:
    """21. Dates are standardized into ISO format."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nDOB: 15/08/2004")
    result = pipeline.process([doc])
    assert result.documents[0].date_of_birth.normalized == "2004-08-15"


# ==============================================================================
# 5. MATCHING INTEGRATION TESTS (22 - 27)
# ==============================================================================

def test_matching_names() -> None:
    """22. Identical names across documents produce MATCH status."""
    pipeline = create_test_pipeline()
    d1 = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Shashikant Ahire")
    d2 = make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nName: Priti Shashikant Ahire")
    result = pipeline.process([d1, d2])
    name_finding = next(f for f in result.cross_document_findings if f.field_name == "name")
    assert name_finding.status == MatchStatus.MATCH


def test_likely_matching_names() -> None:
    """23. Minor typo or ordering difference produces LIKELY_MATCH."""
    pipeline = create_test_pipeline()
    d1 = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Shashikant Ahire")
    d2 = make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nName: Priti S Ahire")
    result = pipeline.process([d1, d2])
    name_finding = next(f for f in result.cross_document_findings if f.field_name == "name")
    assert name_finding.status in (MatchStatus.LIKELY_MATCH, MatchStatus.MATCH, MatchStatus.VERIFICATION_REQUIRED)


def test_mismatching_names() -> None:
    """24. Distinct names produce MISMATCH finding."""
    pipeline = create_test_pipeline()
    d1 = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    d2 = make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nName: Rahul Sharma")
    result = pipeline.process([d1, d2])
    name_finding = next(f for f in result.cross_document_findings if f.field_name == "name")
    assert name_finding.status == MatchStatus.MISMATCH


def test_matching_dob() -> None:
    """25. Matching dates of birth produce MATCH status."""
    pipeline = create_test_pipeline()
    d1 = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nDOB: 15/08/2004")
    d2 = make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nDOB: 2004-08-15")
    result = pipeline.process([d1, d2])
    dob_finding = next(f for f in result.cross_document_findings if f.field_name == "date_of_birth")
    assert dob_finding.status == MatchStatus.MATCH


def test_mismatching_dob() -> None:
    """26. Discrepant dates of birth produce MISMATCH status."""
    pipeline = create_test_pipeline()
    d1 = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nDOB: 15/08/2004")
    d2 = make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nDOB: 20/12/2003")
    result = pipeline.process([d1, d2])
    dob_finding = next(f for f in result.cross_document_findings if f.field_name == "date_of_birth")
    assert dob_finding.status == MatchStatus.MISMATCH


def test_missing_comparison_value() -> None:
    """27. Missing field in one document produces MISSING status."""
    pipeline = create_test_pipeline()
    d1 = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    d2 = make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nDOB: 01/05/2005")
    result = pipeline.process([d1, d2])
    name_finding = next(f for f in result.cross_document_findings if f.field_name == "name")
    assert name_finding.status == MatchStatus.MISSING


# ==============================================================================
# 6. CONFIDENCE INTEGRATION TESTS (28 - 31)
# ==============================================================================

def test_confidence_high() -> None:
    """28. High confidence results are aggregated accurately."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire\nDOB: 01/05/2005")
    result = pipeline.process([doc])
    assert result.verification.high_confidence_count >= 1


def test_confidence_low() -> None:
    """29. Low confidence items flag verification."""
    def low_conf_client(prompt, text, img, dt):
        return {"name": {"value": "Priti Ahire", "confidence": 0.50}}

    pipeline = create_test_pipeline(model_client=low_conf_client)
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    result = pipeline.process([doc])
    assert result.verification.verification_required is True
    assert result.verification.low_confidence_count >= 1


def test_confidence_missing() -> None:
    """30. Missing confidence fields produce MISSING level."""
    def missing_conf_client(prompt, text, img, dt):
        return {"name": {"value": "Priti Ahire", "confidence": None}}

    pipeline = create_test_pipeline(model_client=missing_conf_client)
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    result = pipeline.process([doc])
    missing_items = [i for i in result.verification.items if i.confidence_level == ConfidenceLevel.MISSING]
    assert len(missing_items) >= 1


def test_confidence_verification_flag_propagated() -> None:
    """31. If any item needs verification, verification_required is True."""
    pipeline = create_test_pipeline()
    # A mismatch in names triggers verification_required in matching findings
    d1 = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    d2 = make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nName: John Doe")
    result = pipeline.process([d1, d2])
    assert result.verification.verification_required is True


# ==============================================================================
# 7. INSTRUCTION INTEGRATION TESTS (32 - 36)
# ==============================================================================

def test_instruction_required_document() -> None:
    """32. Required document extracted from instructions brochure."""
    pipeline = create_test_pipeline()
    doc = make_doc("rules.pdf", "GENERAL INSTRUCTIONS TO CANDIDATES\nRequired documents: Aadhaar card must be uploaded.")
    result = pipeline.process([doc])
    req = next(r for r in result.instruction_requirements if r.document_type_requested == DocumentType.AADHAAR_OR_IDENTITY)
    assert req.is_required is True


def test_instruction_format() -> None:
    """33. Accepted file format extracted from instructions."""
    pipeline = create_test_pipeline()
    doc = make_doc("rules.pdf", "GENERAL INSTRUCTIONS TO CANDIDATES\nDocuments must be uploaded in PDF format.")
    result = pipeline.process([doc])
    assert any("pdf" in r.accepted_formats for r in result.instruction_requirements)


def test_instruction_file_size() -> None:
    """34. File size limit extracted as constraint."""
    pipeline = create_test_pipeline()
    doc = make_doc("rules.pdf", "GENERAL INSTRUCTIONS TO CANDIDATES\nMaximum file size 2 MB.")
    result = pipeline.process([doc])
    size_req = next(r for r in result.instruction_requirements if r.requirement_type == "file_size")
    assert size_req.max_file_size_bytes == 2 * 1024 * 1024


def test_instruction_eligibility_requirement() -> None:
    """35. Minimum percentage eligibility extracted as constraint."""
    pipeline = create_test_pipeline()
    doc = make_doc("rules.pdf", "GENERAL INSTRUCTIONS TO CANDIDATES\nEligibility criteria: Applicant must have secured at least 60% marks.")
    result = pipeline.process([doc])
    eligibility_req = next(r for r in result.instruction_requirements if r.requirement_type == "eligibility")
    assert eligibility_req.constraints.get("minimum_percentage") == 60.0


def test_instruction_evidence_preserved() -> None:
    """36. Instruction requirement preserves traceable evidence snippet."""
    pipeline = create_test_pipeline()
    doc = make_doc("guidelines.pdf", "GENERAL INSTRUCTIONS TO CANDIDATES\nRequired documents: Aadhaar card must be uploaded.")
    result = pipeline.process([doc])
    req = next(r for r in result.instruction_requirements if r.document_type_requested == DocumentType.AADHAAR_OR_IDENTITY)
    assert len(req.evidence) > 0
    assert "guidelines.pdf" in req.evidence[0].source_document


# ==============================================================================
# 8. FINAL CONTRACT & SAFETY TESTS (37 - 43)
# ==============================================================================

def test_returns_ai_processing_result() -> None:
    """37. Result conforms strictly to AIProcessingResult contract."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    result = pipeline.process([doc])
    assert isinstance(result, AIProcessingResult)
    assert hasattr(result, "documents")
    assert hasattr(result, "cross_document_findings")
    assert hasattr(result, "instruction_requirements")
    assert hasattr(result, "verification")


def test_deterministic_ordering() -> None:
    """38. Deterministic ordering: documents and findings follow stable canonical sorting."""
    pipeline = create_test_pipeline()
    docs = [
        make_doc("marksheet.pdf", "BOARD OF SECONDARY EDUCATION STATEMENT OF MARKS\nName: Priti Ahire"),
        make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire"),
        make_doc("aadhaar.pdf", "UNIQUE IDENTIFICATION AUTHORITY OF INDIA GOVERNMENT OF INDIA AADHAAR CARD\nName: Priti Ahire"),
    ]
    res1 = pipeline.process(docs)
    res2 = pipeline.process(docs)

    # Document ordering must be identical and respect DOCUMENT_TYPE_ORDER
    assert [d.document_type for d in res1.documents] == [d.document_type for d in res2.documents]
    assert res1.documents[0].document_type == DocumentType.APPLICATION_FORM
    assert res1.documents[1].document_type == DocumentType.AADHAAR_OR_IDENTITY
    assert res1.documents[2].document_type == DocumentType.MARKSHEET


def test_no_hallucinated_fields() -> None:
    """39. Missing fields strictly remain None."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    result = pipeline.process([doc])
    assert result.documents[0].address is None
    assert result.documents[0].certificate_number is None


def test_no_ready_or_eligibility_decision() -> None:
    """40. Pipeline reports evidence only, no approval or eligibility decisions."""
    pipeline = create_test_pipeline()
    doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    result = pipeline.process([doc])

    res_dict = result.model_dump()
    forbidden_keys = ["is_ready", "decision", "eligible", "approved", "rejected", "risk_score"]
    for key in forbidden_keys:
        assert key not in res_dict


def test_alias_preflight_ai_pipeline() -> None:
    """41. PreFlightAIPipeline alias is identical to AIPipeline."""
    assert PreFlightAIPipeline is AIPipeline


def test_partial_failure_preservation() -> None:
    """42. Pipeline preserves valid documents when partial failure is allowed."""
    pipeline = create_test_pipeline()
    valid_doc = make_doc("app.pdf", "MAHARASHTRA SCHOLARSHIP APPLICATION FORM\nName: Priti Ahire")
    # Simulate a missing file path along with valid document
    result = pipeline.process(
        document_inputs=[valid_doc, "non_existent_file.pdf"],
        allow_partial_failure=True,
    )
    assert len(result.documents) == 2
    types = [d.document_type for d in result.documents]
    assert DocumentType.APPLICATION_FORM in types
    assert DocumentType.UNKNOWN in types
    # Verification required must be set because of the partial failure
    assert result.verification.verification_required is True


def test_strict_failure_on_missing_file() -> None:
    """43. Pipeline raises DocumentNotFoundError when missing file and partial failure disabled."""
    pipeline = create_test_pipeline()
    with pytest.raises(DocumentNotFoundError):
        pipeline.process(["non_existent_document_file.pdf"])
