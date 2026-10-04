"""Tests for information extraction service and vision extractor adapter."""

from typing import Any, Dict, List, Optional
import pytest
from PIL import Image

from ai.exceptions import DocumentProcessingError, ExtractionError
from ai.extraction.extractor import DocumentExtractor
from ai.extraction.vision_extractor import VisionExtractor
from ai.preprocessing.models import PreprocessedDocument, PreprocessedPage
from ai.schemas.document import DocumentType, Evidence
from ai.schemas.extraction import ExtractedDocument, ExtractedField


def _make_preprocessed_doc(
    file_name: str = "doc.pdf",
    text: Optional[str] = "Sample text content",
    file_type: str = "pdf",
    images: Optional[List[Image.Image]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> PreprocessedDocument:
    """Helper to create a synthetic PreprocessedDocument."""
    pages = []
    if text:
        pages.append(PreprocessedPage(page_number=1, text=text))
    doc_images = images or []

    return PreprocessedDocument(
        file_path=f"D:/temp/{file_name}",
        file_name=file_name,
        file_type=file_type,
        mime_type="application/pdf" if file_type == "pdf" else "image/jpeg",
        page_count=len(pages) or (1 if doc_images else 0),
        full_text=text,
        page_texts=[text] if text else [],
        pages=pages,
        images=doc_images,
        has_usable_text=bool(text and len(text) > 10),
        requires_vision_processing=not text or bool(doc_images),
        metadata=metadata or {},
    )


def test_application_form_extraction() -> None:
    """Verify extraction of standard application form fields and additional metadata."""
    mock_payload = {
        "name": {"value": "Priti Shashikant Ahire", "confidence": 0.96, "snippet": "Applicant: Priti Shashikant Ahire"},
        "date_of_birth": {"value": "2004-08-15", "confidence": 0.94, "snippet": "DOB: 15/08/2004"},
        "father_name": {"value": "Shashikant Ahire", "confidence": 0.90},
        "mother_name": {"value": "Sunita Ahire", "confidence": 0.90},
        "address": {"value": "Pune, Maharashtra", "confidence": 0.88},
        "additional_fields": {
            "application_id": {"value": "APP-2026-9876", "confidence": 0.95},
            "scheme_name": {"value": "Post-Matric Scholarship", "confidence": 0.92},
        },
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(file_name="application.pdf")

    result = extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert isinstance(result, ExtractedDocument)
    assert result.document_type == DocumentType.APPLICATION_FORM
    assert result.name is not None
    assert result.name.original == "Priti Shashikant Ahire"
    assert result.name.normalized is None  # Deferred to Task 6 (Normalization)
    assert result.name.confidence == 0.96
    assert result.date_of_birth is not None
    assert result.date_of_birth.original == "2004-08-15"
    assert result.father_name is not None
    assert result.father_name.original == "Shashikant Ahire"
    assert "application_id" in result.additional_fields
    assert result.additional_fields["application_id"].original == "APP-2026-9876"


def test_aadhaar_identity_extraction() -> None:
    """Verify identity document extraction with identity number in additional_fields."""
    mock_payload = {
        "name": {"value": "Priti S Ahire", "confidence": 0.97},
        "date_of_birth": {"value": "15/08/2004", "confidence": 0.95},
        "address": {"value": "Pune, Maharashtra - 411033", "confidence": 0.91},
        "identity_number": {"value": "XXXX-XXXX-1234", "confidence": 0.92, "snippet": "Aadhaar: XXXX-XXXX-1234"},
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(file_name="aadhaar.pdf")

    result = extractor.extract_document(doc, document_type=DocumentType.AADHAAR_OR_IDENTITY)

    assert result.document_type == DocumentType.AADHAAR_OR_IDENTITY
    assert result.name is not None
    assert result.name.original == "Priti S Ahire"
    assert "identity_number" in result.additional_fields
    assert result.additional_fields["identity_number"].original == "XXXX-XXXX-1234"


def test_marksheet_extraction() -> None:
    """Verify academic marksheet field extraction."""
    mock_payload = {
        "name": "Priti Ahire",
        "marks": "450/500",
        "percentage": "90.0%",
        "confidence_scores": {"name": 0.98, "marks": 0.95, "percentage": 0.96},
        "additional_fields": {
            "examination": "Semester VI B.Tech",
            "cgpa": 9.25,
            "board_or_university": "Pune University",
        },
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(file_name="marksheet.pdf")

    result = extractor.extract_document(doc, document_type=DocumentType.MARKSHEET)

    assert result.marks is not None
    assert result.marks.original == "450/500"
    assert result.percentage is not None
    assert result.percentage.original == "90.0%"
    assert result.additional_fields["cgpa"].original == 9.25
    assert result.additional_fields["board_or_university"].original == "Pune University"


def test_income_certificate_extraction() -> None:
    """Verify income certificate extraction."""
    mock_payload = {
        "name": "Shashikant Ahire",
        "certificate_number": "INC/2026/8899",
        "issue_date": "2026-03-10",
        "expiry_date": "2027-03-31",
        "annual_income": {"value": "INR 1,50,000", "confidence": 0.96},
        "issuing_authority": "Tahasildar Haveli",
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(file_name="income.pdf")

    result = extractor.extract_document(doc, document_type=DocumentType.INCOME_CERTIFICATE)

    assert result.certificate_number is not None
    assert result.certificate_number.original == "INC/2026/8899"
    assert result.issue_date is not None
    assert result.issue_date.original == "2026-03-10"
    assert result.expiry_date is not None
    assert result.expiry_date.original == "2027-03-31"
    assert result.additional_fields["annual_income"].original == "INR 1,50,000"


def test_caste_certificate_extraction() -> None:
    """Verify caste certificate extraction."""
    mock_payload = {
        "name": "Priti Ahire",
        "certificate_number": "CST/4567/2024",
        "issue_date": "2024-05-12",
        "caste": "Hindu - Maratha",
        "category": "OBC",
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(file_name="caste.pdf")

    result = extractor.extract_document(doc, document_type=DocumentType.CASTE_CERTIFICATE)

    assert result.certificate_number is not None
    assert result.certificate_number.original == "CST/4567/2024"
    assert result.additional_fields["caste"].original == "Hindu - Maratha"
    assert result.additional_fields["category"].original == "OBC"


def test_photograph_handling_avoids_llm() -> None:
    """Photograph documents should extract image metadata directly without calling LLM."""
    was_called = False

    def mock_model(prompt: str, text: Optional[str], img: Optional[List[Image.Image]], doc_type: DocumentType) -> Dict[str, Any]:
        nonlocal was_called
        was_called = True
        return {}

    vision_extractor = VisionExtractor(model_client=mock_model)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(
        file_name="applicant_photo.jpg",
        text=None,
        file_type="jpg",
        metadata={"width": 350, "height": 450, "format": "JPEG"},
    )

    result = extractor.extract_document(doc, document_type=DocumentType.PHOTOGRAPH)

    assert not was_called  # Confirmed: no LLM/OCR attempted
    assert result.document_type == DocumentType.PHOTOGRAPH
    assert "width" in result.additional_fields
    assert result.additional_fields["width"].original == 350
    assert result.additional_fields["height"].original == 450


def test_instructions_extraction() -> None:
    """Verify application instructions and document requirements extraction."""
    mock_payload = {
        "additional_fields": {
            "required_documents": ["Aadhaar", "Marksheet", "Income Certificate"],
            "accepted_formats": ["PDF", "JPG"],
            "max_file_size": "2MB",
            "application_deadline": "30-10-2026",
        }
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(file_name="guidelines.pdf")

    result = extractor.extract_document(doc, document_type=DocumentType.INSTRUCTIONS)

    assert result.document_type == DocumentType.INSTRUCTIONS
    assert "required_documents" in result.additional_fields
    assert result.additional_fields["required_documents"].original == [
        "Aadhaar",
        "Marksheet",
        "Income Certificate",
    ]


def test_missing_optional_fields() -> None:
    """Absent optional fields in model output should remain None."""
    mock_payload = {
        "name": {"value": "Priti Ahire", "confidence": 0.95},
        # All other fields absent
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc()

    result = extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert result.name is not None
    assert result.date_of_birth is None
    assert result.father_name is None
    assert result.mother_name is None
    assert result.address is None
    assert result.certificate_number is None
    assert result.issue_date is None
    assert result.expiry_date is None
    assert result.marks is None
    assert result.percentage is None


def test_null_values_handling() -> None:
    """Explicit null/None values from the model must not be guessed or fabricated."""
    mock_payload = {
        "name": {"value": "Priti Ahire"},
        "father_name": None,
        "date_of_birth": {"value": None},
        "mother_name": None,
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc()

    result = extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert result.name is not None
    assert result.name.original == "Priti Ahire"
    assert result.father_name is None
    assert result.date_of_birth is None
    assert result.mother_name is None


def test_confidence_values_preservation() -> None:
    """Confidence scores must be preserved and clamped between 0.0 and 1.0."""
    mock_payload = {
        "name": {"value": "Valid Name", "confidence": 0.88},
        "date_of_birth": {"value": "2000-01-01", "confidence": 1.50},  # Out of range -> clamped to 1.0
        "address": {"value": "Test Address", "confidence": None},
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc()

    result = extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert result.name is not None and result.name.confidence == 0.88
    assert result.date_of_birth is not None and result.date_of_birth.confidence == 1.0
    assert result.address is not None and result.address.confidence is None


def test_evidence_preservation() -> None:
    """Evidence snippets and page numbers should be preserved cleanly."""
    mock_payload = {
        "name": {
            "value": "Priti Ahire",
            "snippet": "Applicant Name: Priti Ahire",
            "page_number": 1,
        }
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(file_name="test_form.pdf")

    result = extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert result.name is not None
    assert len(result.name.evidence) == 1
    ev = result.name.evidence[0]
    assert ev.source_document == "test_form.pdf"
    assert ev.page_number == 1
    assert ev.snippet == "Applicant Name: Priti Ahire"


def test_malformed_model_response_handling() -> None:
    """Non-dictionary model responses must raise ExtractionError."""
    vision_extractor = VisionExtractor(
        model_client=lambda prompt, text, img, doc_type: "malformed text string instead of dict"  # type: ignore[return-value]
    )
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc()

    with pytest.raises(ExtractionError):
        extractor.extract_document(doc)


def test_unsupported_unknown_document_type_fallback() -> None:
    """Unknown document type should use default prompt and safely parse visible fields."""
    mock_payload = {
        "name": "General Person",
        "date_of_birth": "1995-10-20",
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(file_name="unknown_file.pdf")

    result = extractor.extract_document(doc, document_type=DocumentType.UNKNOWN)

    assert result.document_type == DocumentType.UNKNOWN
    assert result.name is not None
    assert result.name.original == "General Person"


def test_selectable_pdf_text_extraction_path() -> None:
    """Extractor should pass selectable text content to the vision extractor."""
    captured_text = None

    def capture_client(prompt: str, text: Optional[str], img: Optional[List[Image.Image]], doc_type: DocumentType) -> Dict[str, Any]:
        nonlocal captured_text
        captured_text = text
        return {"name": "Test Name"}

    vision_extractor = VisionExtractor(model_client=capture_client)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(text="Extracted selectable PDF text page 1")

    extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert captured_text == "Extracted selectable PDF text page 1"


def test_image_vision_extraction_path() -> None:
    """Extractor should pass document images to the vision extractor when text is absent."""
    captured_images = None

    def capture_client(prompt: str, text: Optional[str], img: Optional[List[Image.Image]], doc_type: DocumentType) -> Dict[str, Any]:
        nonlocal captured_images
        captured_images = img
        return {"name": "Scanned Document Name"}

    test_image = Image.new("RGB", (100, 100), color="blue")
    vision_extractor = VisionExtractor(model_client=capture_client)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc(text=None, images=[test_image])

    extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert captured_images is not None
    assert len(captured_images) == 1
    assert captured_images[0].size == (100, 100)


def test_no_hallucination_rule_preservation() -> None:
    """Confirm strictly no synthetic values are generated and normalized remains None."""
    mock_payload = {
        "name": "Only Name Given",
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc()

    result = extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert result.name is not None
    assert result.name.original == "Only Name Given"
    assert result.name.normalized is None  # Strictly None, no normalization
    assert result.date_of_birth is None
    assert result.certificate_number is None


def test_additional_fields_handling() -> None:
    """Extra fields beyond standard core fields must be preserved in additional_fields."""
    mock_payload = {
        "name": "Priti Ahire",
        "custom_registration_code": "REG-2026-X",
        "additional_fields": {
            "counseling_rank": 1042,
            "quota": "State Merit",
        },
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc()

    result = extractor.extract_document(doc, document_type=DocumentType.APPLICATION_FORM)

    assert "custom_registration_code" in result.additional_fields
    assert result.additional_fields["custom_registration_code"].original == "REG-2026-X"
    assert "counseling_rank" in result.additional_fields
    assert result.additional_fields["counseling_rank"].original == 1042
    assert "quota" in result.additional_fields
    assert result.additional_fields["quota"].original == "State Merit"


def test_schema_validation_and_json_roundtrip() -> None:
    """Verify that ExtractedDocument serializes cleanly to JSON and validates back."""
    mock_payload = {
        "name": {"value": "Priti Ahire", "confidence": 0.95},
        "percentage": {"value": "88.5%", "confidence": 0.92},
    }

    vision_extractor = VisionExtractor(model_client=lambda prompt, text, img, doc_type: mock_payload)
    extractor = DocumentExtractor(vision_extractor=vision_extractor)
    doc = _make_preprocessed_doc()

    result = extractor.extract_document(doc, document_type=DocumentType.MARKSHEET)

    # Pydantic JSON export and roundtrip
    json_data = result.model_dump_json()
    assert isinstance(json_data, str)

    restored = ExtractedDocument.model_validate_json(json_data)
    assert restored.document_type == DocumentType.MARKSHEET
    assert restored.name is not None
    assert restored.name.original == "Priti Ahire"
    assert restored.percentage is not None
    assert restored.percentage.original == "88.5%"


def test_invalid_document_input_type() -> None:
    """Calling extractor with non-PreprocessedDocument must raise DocumentProcessingError."""
    extractor = DocumentExtractor()
    with pytest.raises(DocumentProcessingError):
        extractor.extract_document("string_instead_of_doc")  # type: ignore[arg-type]
