"""Comprehensive unit tests for scholarship instruction extraction."""

import pytest
from ai.exceptions import ExtractionError
from ai.extraction.vision_extractor import VisionExtractor
from ai.instructions import (
    InstructionExtractor,
    generate_requirement_id,
    parse_file_size,
    parse_formats,
)
from ai.preprocessing.models import PreprocessedDocument, PreprocessedPage
from ai.schemas.document import DocumentType
from ai.schemas.instructions import InstructionRequirement


# ==============================================================================
# 1. CORE DOCUMENT REQUIREMENT TESTS (1 - 5)
# ==============================================================================

def test_required_aadhaar_document() -> None:
    """1. Explicit requirement for Aadhaar card."""
    extractor = InstructionExtractor()
    text = "Aadhaar card must be uploaded by the applicant."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    req = reqs[0]
    assert req.requirement_type == "required_document"
    assert req.document_type_requested == DocumentType.AADHAAR_OR_IDENTITY
    assert req.is_required is True


def test_required_marksheet() -> None:
    """2. Explicit requirement for latest marksheet."""
    extractor = InstructionExtractor()
    text = "Latest marksheet must be submitted."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    req = reqs[0]
    assert req.requirement_type == "required_document"
    assert req.document_type_requested == DocumentType.MARKSHEET
    assert req.is_required is True


def test_required_income_certificate() -> None:
    """3. Explicit mandatory requirement for income certificate."""
    extractor = InstructionExtractor()
    text = "Valid income certificate is mandatory."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    req = reqs[0]
    assert req.requirement_type == "required_document"
    assert req.document_type_requested == DocumentType.INCOME_CERTIFICATE
    assert req.is_required is True


def test_conditional_caste_certificate() -> None:
    """4. Conditional requirement for caste certificate for reserved categories."""
    extractor = InstructionExtractor()
    text = "Caste certificate must be uploaded for applicable categories."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    req = reqs[0]
    assert req.requirement_type == "required_document"
    assert req.document_type_requested == DocumentType.CASTE_CERTIFICATE
    assert req.constraints.get("conditional") is True


def test_photograph_requirement() -> None:
    """5. Photograph requirement with dimensions and formats."""
    extractor = InstructionExtractor()
    text = "Upload passport-size photograph in JPG format with white background."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    req = reqs[0]
    assert req.requirement_type == "photograph"
    assert req.document_type_requested == DocumentType.PHOTOGRAPH
    assert "jpg" in req.accepted_formats
    assert req.constraints.get("dimensions") == "passport size"
    assert req.constraints.get("background") == "white"


# ==============================================================================
# 2. FORMAT AND SIZE PARSING TESTS (6 - 11)
# ==============================================================================

def test_pdf_format_extraction() -> None:
    """6. PDF format extraction from general document statement."""
    extractor = InstructionExtractor()
    text = "Documents must be uploaded in PDF format."
    reqs = extractor.extract_instructions(text)

    assert any("pdf" in r.accepted_formats for r in reqs)
    assert parse_formats("Documents must be uploaded in PDF format.") == ["pdf"]


def test_jpg_png_format_extraction() -> None:
    """7. JPG and PNG formats extraction."""
    extractor = InstructionExtractor()
    text = "Photos must be in JPG or PNG format."
    reqs = extractor.extract_instructions(text)

    assert any(set(["jpg", "png"]).issubset(set(r.accepted_formats)) for r in reqs)
    assert parse_formats("Supported: JPG or PNG") == ["jpg", "png"]


def test_maximum_file_size() -> None:
    """8. Maximum file size in MB converted to bytes."""
    assert parse_file_size("Maximum file size is 2 MB.") == 2097152
    extractor = InstructionExtractor()
    reqs = extractor.extract_instructions("Maximum file size is 2 MB.")
    assert len(reqs) == 1
    assert reqs[0].max_file_size_bytes == 2097152


def test_kb_conversion() -> None:
    """9. KB file size conversion to bytes."""
    assert parse_file_size("Photo should not exceed 200 KB.") == 204800
    extractor = InstructionExtractor()
    reqs = extractor.extract_instructions("Photo should not exceed 200 KB.")
    assert len(reqs) == 1
    assert reqs[0].max_file_size_bytes == 204800


def test_mb_conversion() -> None:
    """10. Multi-MB conversion to bytes."""
    assert parse_file_size("File limit: 5 MB.") == 5 * 1024 * 1024
    assert parse_file_size("File limit: 1 GB.") == 1073741824


def test_decimal_file_sizes() -> None:
    """11. Decimal MB file sizes converted accurately."""
    assert parse_file_size("Size limit is 1.5 MB.") == 1572864


# ==============================================================================
# 3. ELIGIBILITY AND ID TESTS (12 - 13)
# ==============================================================================

def test_eligibility_percentage() -> None:
    """12. Minimum percentage eligibility requirement extracted without evaluation."""
    extractor = InstructionExtractor()
    text = "Applicant must have secured at least 60% marks in previous examination."
    reqs = extractor.extract_instructions(text)

    eligibility_reqs = [r for r in reqs if r.requirement_type == "eligibility"]
    assert len(eligibility_reqs) == 1
    assert eligibility_reqs[0].constraints.get("minimum_percentage") == 60.0
    # Confirms no applicant status or decision attribute is added
    assert not hasattr(eligibility_reqs[0], "is_eligible")


def test_deterministic_requirement_ids() -> None:
    """13. Requirement IDs are identical for identical inputs."""
    id1 = generate_requirement_id("required_document", DocumentType.AADHAAR_OR_IDENTITY, "aadhaar card required")
    id2 = generate_requirement_id("required_document", DocumentType.AADHAAR_OR_IDENTITY, "aadhaar card required")
    assert id1 == id2
    assert id1.startswith("req_aadhaar_or_identity_required_document_")


# ==============================================================================
# 4. EVIDENCE AND MULTI-PAGE TESTS (14 - 17)
# ==============================================================================

def test_evidence_page_number() -> None:
    """14. Evidence contains correct page number from preprocessed page."""
    doc = PreprocessedDocument(
        file_path="guidelines.pdf",
        file_name="guidelines.pdf",
        file_type="pdf",
        mime_type="application/pdf",
        page_count=2,
        pages=[
            PreprocessedPage(page_number=1, text="General guidelines."),
            PreprocessedPage(page_number=2, text="Aadhaar card must be uploaded."),
        ],
    )
    extractor = InstructionExtractor()
    reqs = extractor.extract_instructions(doc)

    assert len(reqs) == 1
    assert reqs[0].evidence[0].page_number == 2
    assert reqs[0].evidence[0].source_document == "guidelines.pdf"


def test_evidence_snippet() -> None:
    """15. Evidence snippet preserves original instruction text."""
    text = "Aadhaar card must be uploaded."
    extractor = InstructionExtractor()
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    assert reqs[0].evidence[0].snippet == "Aadhaar card must be uploaded"


def test_multi_page_instructions() -> None:
    """16. Inspects all pages in multi-page document."""
    doc = PreprocessedDocument(
        file_path="guide.pdf",
        file_name="guide.pdf",
        file_type="pdf",
        mime_type="application/pdf",
        page_count=3,
        pages=[
            PreprocessedPage(page_number=1, text="Aadhaar card must be uploaded."),
            PreprocessedPage(page_number=2, text="Latest marksheet must be submitted."),
            PreprocessedPage(page_number=3, text="Valid income certificate is mandatory."),
        ],
    )
    extractor = InstructionExtractor()
    reqs = extractor.extract_instructions(doc)

    doc_types = {r.document_type_requested for r in reqs}
    assert DocumentType.AADHAAR_OR_IDENTITY in doc_types
    assert DocumentType.MARKSHEET in doc_types
    assert DocumentType.INCOME_CERTIFICATE in doc_types


def test_duplicate_requirement_merging() -> None:
    """17. Identical requirements on multiple pages merge evidence without duplicate items."""
    doc = PreprocessedDocument(
        file_path="guide.pdf",
        file_name="guide.pdf",
        file_type="pdf",
        mime_type="application/pdf",
        page_count=2,
        pages=[
            PreprocessedPage(page_number=1, text="Aadhaar card must be uploaded."),
            PreprocessedPage(page_number=2, text="Aadhaar card must be uploaded."),
        ],
    )
    extractor = InstructionExtractor()
    reqs = extractor.extract_instructions(doc)

    # Merged into single requirement with 2 evidence entries
    assert len(reqs) == 1
    assert len(reqs[0].evidence) == 2
    pages = {e.page_number for e in reqs[0].evidence}
    assert pages == {1, 2}


# ==============================================================================
# 5. ABSENCE, SAFETY, AND UNKNOWN TESTS (18 - 23)
# ==============================================================================

def test_unknown_document_reference() -> None:
    """18. Non-standard document is mapped to UNKNOWN and preserved in constraints."""
    extractor = InstructionExtractor()
    text = "Bonafide certificate must be submitted."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    assert reqs[0].document_type_requested == DocumentType.UNKNOWN
    assert reqs[0].constraints.get("document_name") == "bonafide certificate"


def test_absent_format_should_remain_absent() -> None:
    """19. When no format is stated, accepted_formats is empty."""
    extractor = InstructionExtractor()
    text = "Upload all requested documents."
    reqs = extractor.extract_instructions(text)
    for r in reqs:
        assert r.accepted_formats == []


def test_absent_file_size_should_remain_absent() -> None:
    """20. When no file size is stated, max_file_size_bytes is None."""
    extractor = InstructionExtractor()
    text = "Latest marksheet must be submitted."
    reqs = extractor.extract_instructions(text)
    assert len(reqs) == 1
    assert reqs[0].max_file_size_bytes is None


def test_no_hallucination_behavior() -> None:
    """21. Plain photograph statement does not hallucinate JPG, 200 KB, or white background."""
    extractor = InstructionExtractor()
    text = "Upload your photograph."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    assert reqs[0].accepted_formats == []
    assert reqs[0].max_file_size_bytes is None
    assert "dimensions" not in reqs[0].constraints
    assert "background" not in reqs[0].constraints


def test_conflicting_requirements() -> None:
    """22. Conflicting requirements (e.g. 2 MB vs 5 MB) are preserved separately."""
    doc = PreprocessedDocument(
        file_path="guide.pdf",
        file_name="guide.pdf",
        file_type="pdf",
        mime_type="application/pdf",
        page_count=2,
        pages=[
            PreprocessedPage(page_number=2, text="Maximum file size is 2 MB."),
            PreprocessedPage(page_number=5, text="Maximum file size is 5 MB."),
        ],
    )
    extractor = InstructionExtractor()
    reqs = extractor.extract_instructions(doc)

    sizes = {r.max_file_size_bytes for r in reqs if r.requirement_type == "file_size"}
    assert 2097152 in sizes
    assert 5242880 in sizes
    assert len(reqs) == 2


def test_empty_instructions() -> None:
    """23. Empty instruction document returns empty requirements list."""
    extractor = InstructionExtractor()
    assert extractor.extract_instructions("") == []
    assert extractor.extract_instructions("   ") == []


# ==============================================================================
# 6. MODEL BOUNDARY & PREPROCESSING INTEGRATION TESTS (24 - 26)
# ==============================================================================

def test_malformed_model_response() -> None:
    """24. Malformed model boundary response raises ExtractionError safely."""
    mock_client = lambda prompt, text, images, doc_type: {"bad_key": 123}
    vision_extractor = VisionExtractor(model_client=mock_client)
    extractor = InstructionExtractor(vision_extractor=vision_extractor)

    with pytest.raises(ExtractionError):
        extractor.extract_instructions("Some instructions", use_vision=True)


def test_selectable_pdf_text_path() -> None:
    """25. PreprocessedDocument with selectable PDF text extracts requirements seamlessly."""
    doc = PreprocessedDocument(
        file_path="scholarship_rules.pdf",
        file_name="scholarship_rules.pdf",
        file_type="pdf",
        mime_type="application/pdf",
        page_count=1,
        full_text="Aadhaar card must be uploaded. Maximum file size is 2 MB.",
        has_usable_text=True,
    )
    extractor = InstructionExtractor()
    reqs = extractor.extract_instructions(doc)

    assert len(reqs) == 2
    types = {r.requirement_type for r in reqs}
    assert "required_document" in types
    assert "file_size" in types


def test_synthetic_vision_model_path() -> None:
    """26. VisionExtractor mock path parses structured model requirements."""
    synthetic_payload = {
        "requirements": [
            {
                "requirement_type": "required_document",
                "document_type_requested": "income_certificate",
                "is_required": True,
                "accepted_formats": ["pdf"],
                "max_file_size_bytes": 2097152,
                "constraints": {},
                "snippet": "Income certificate mandatory in PDF up to 2MB.",
                "page_number": 1,
            }
        ]
    }
    mock_client = lambda prompt, text, images, doc_type: synthetic_payload
    vision_extractor = VisionExtractor(model_client=mock_client)
    extractor = InstructionExtractor(vision_extractor=vision_extractor)

    reqs = extractor.extract_instructions("scanned guidelines", use_vision=True)
    assert len(reqs) == 1
    assert reqs[0].document_type_requested == DocumentType.INCOME_CERTIFICATE
    assert reqs[0].accepted_formats == ["pdf"]
    assert reqs[0].max_file_size_bytes == 2097152


# ==============================================================================
# MULTILINGUAL INSTRUCTION EXTRACTION TESTS (Hindi, Marathi, Indic Patterns)
# ==============================================================================

def test_hindi_required_documents_extraction() -> None:
    """Hindi document requirements for income certificate, marksheet, and caste certificate."""
    extractor = InstructionExtractor()
    text = (
        "आवश्यक दस्तावेज:\n"
        "सक्षम प्राधिकारी द्वारा जारी आय प्रमाण पत्र अपलोड करना अनिवार्य है।\n"
        "कक्षा 12वीं की अंकतालिका संलग्न करना आवश्यक है।\n"
        "जाति प्रमाण पत्र लागू होने पर प्रस्तुत करें।"
    )
    reqs = extractor.extract_instructions(text)
    assert len(reqs) == 3

    income_req = next(r for r in reqs if r.document_type_requested == DocumentType.INCOME_CERTIFICATE)
    assert income_req.requirement_type == "required_document"
    assert income_req.is_required is True

    marks_req = next(r for r in reqs if r.document_type_requested == DocumentType.MARKSHEET)
    assert marks_req.requirement_type == "required_document"

    caste_req = next(r for r in reqs if r.document_type_requested == DocumentType.CASTE_CERTIFICATE)
    assert caste_req.requirement_type == "required_document"
    assert caste_req.constraints.get("conditional") is True


def test_marathi_required_documents_extraction() -> None:
    """Marathi document requirements for income certificate, marksheet, and caste certificate."""
    extractor = InstructionExtractor()
    text = (
        "आवश्यक कागदपत्रे:\n"
        "तहसीलदार कार्यालयाने दिलेले उत्पन्न प्रमाणपत्र सादर करणे बंधनकारक आहे.\n"
        "महाराष्ट्र राज्य माध्यमिक मंडळाची गुणपत्रिका जोडणे आवश्यक आहे.\n"
        "सक्षम प्राधिकरणाचे जात प्रमाणपत्र लागू असल्यास अपलोड करावे."
    )
    reqs = extractor.extract_instructions(text)
    assert len(reqs) == 3

    income_req = next(r for r in reqs if r.document_type_requested == DocumentType.INCOME_CERTIFICATE)
    assert income_req.requirement_type == "required_document"

    marks_req = next(r for r in reqs if r.document_type_requested == DocumentType.MARKSHEET)
    assert marks_req.requirement_type == "required_document"

    caste_req = next(r for r in reqs if r.document_type_requested == DocumentType.CASTE_CERTIFICATE)
    assert caste_req.requirement_type == "required_document"
    assert caste_req.constraints.get("conditional") is True


def test_hindi_photo_requirement() -> None:
    """Hindi photograph requirement with background constraint."""
    extractor = InstructionExtractor()
    text = "सफेद पृष्ठभूमि वाला पासपोर्ट आकार का फोटो अपलोड करें।"
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    req = reqs[0]
    assert req.requirement_type == "photograph"
    assert req.document_type_requested == DocumentType.PHOTOGRAPH
    assert req.constraints.get("dimensions") == "passport size"
    assert req.constraints.get("background") == "white"


def test_marathi_photo_requirement() -> None:
    """Marathi photograph requirement with dimensions."""
    extractor = InstructionExtractor()
    text = "उमेदवाराने स्वतःचा पासपोर्ट आकाराचा फोटो अपलोड करावा."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    req = reqs[0]
    assert req.requirement_type == "photograph"
    assert req.document_type_requested == DocumentType.PHOTOGRAPH
    assert req.constraints.get("dimensions") == "passport size"


def test_hindi_and_marathi_file_format_extraction() -> None:
    """Explicit file format extraction from Hindi and Marathi statements."""
    extractor = InstructionExtractor()

    text_hin = "दस्तावेज केवल PDF प्रारूप में अपलोड करें।"
    reqs_hin = extractor.extract_instructions(text_hin)
    assert any("pdf" in r.accepted_formats for r in reqs_hin)

    text_mar = "कागदपत्रे फक्त PDF स्वरूपात अपलोड करावीत."
    reqs_mar = extractor.extract_instructions(text_mar)
    assert any("pdf" in r.accepted_formats for r in reqs_mar)

    # Devanagari format transliterations
    assert parse_formats("फाइल जेपीजी किंवा पीएनजी स्वरूपात असावी.") == ["jpg", "png"]
    assert parse_formats("केवल पीडीएफ फाइल स्वीकार्य है") == ["pdf"]


def test_hindi_and_marathi_file_size_extraction() -> None:
    """Explicit file size extraction reusing existing parse_file_size logic."""
    extractor = InstructionExtractor()

    text_hin = "अधिकतम फ़ाइल आकार 2 MB होना चाहिए।"
    reqs_hin = extractor.extract_instructions(text_hin)
    assert len(reqs_hin) == 1
    assert reqs_hin[0].requirement_type == "file_size"
    assert reqs_hin[0].max_file_size_bytes == 2 * 1024 * 1024

    text_mar = "कमाल फाइल आकार 5 MB असावा."
    reqs_mar = extractor.extract_instructions(text_mar)
    assert len(reqs_mar) == 1
    assert reqs_mar[0].requirement_type == "file_size"
    assert reqs_mar[0].max_file_size_bytes == 5 * 1024 * 1024


def test_hindi_and_marathi_eligibility_constraints() -> None:
    """Eligibility percentage constraints extracted but not evaluated."""
    extractor = InstructionExtractor()

    text_hin = "आवेदक को अर्हक परीक्षा में न्यूनतम 60 प्रतिशत अंक प्राप्त होने चाहिए।"
    reqs_hin = extractor.extract_instructions(text_hin)
    assert len(reqs_hin) == 1
    assert reqs_hin[0].requirement_type == "eligibility"
    assert reqs_hin[0].constraints.get("minimum_percentage") == 60.0

    text_mar = "उमेदवारास अर्हता परीक्षेत किमान 60% गुण असणे आवश्यक आहे."
    reqs_mar = extractor.extract_instructions(text_mar)
    assert len(reqs_mar) == 1
    assert reqs_mar[0].requirement_type == "eligibility"
    assert reqs_mar[0].constraints.get("minimum_percentage") == 60.0


def test_indic_unknown_document_extraction() -> None:
    """Unmapped Indic certificate is preserved with DocumentType.UNKNOWN."""
    extractor = InstructionExtractor()
    text = "बोनाफाइड प्रमाणपत्र सादर करणे आवश्यक आहे."
    reqs = extractor.extract_instructions(text)

    assert len(reqs) == 1
    assert reqs[0].requirement_type == "required_document"
    assert reqs[0].document_type_requested == DocumentType.UNKNOWN
    assert "बोनाफाइड प्रमाणपत्र" in reqs[0].constraints.get("document_name", "")


def test_generic_indic_text_without_requirements() -> None:
    """Generic or advisory Indic text should NOT produce fabricated requirements."""
    extractor = InstructionExtractor()
    text = "सर्व उमेदवारांनी अर्जातील माहिती काळजीपूर्वक वाचावी आणि मार्गदर्शन घ्यावे."
    reqs = extractor.extract_instructions(text)
    assert len(reqs) == 0
