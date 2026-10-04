"""Tests for deterministic document classification service."""

from pathlib import Path
import pytest
from PIL import Image

from ai.classification.document_classifier import DocumentClassifier
from ai.exceptions import DocumentProcessingError
from ai.preprocessing.models import PreprocessedDocument, PreprocessedPage
from ai.schemas.document import DocumentType, Evidence


def _make_doc(
    file_name: str = "doc.pdf",
    text: str = "",
    file_type: str = "pdf",
    width: int = 0,
    height: int = 0,
    has_images: bool = False,
) -> PreprocessedDocument:
    """Helper to build synthetic PreprocessedDocument instances for testing."""
    pages = []
    images = []
    if text:
        pages.append(PreprocessedPage(page_number=1, text=text))
    if has_images or (width > 0 and height > 0):
        img = Image.new("RGB", (width or 200, height or 200), color="white")
        images.append(img)
        if not pages:
            pages.append(PreprocessedPage(page_number=1, text=None, images=[img]))

    return PreprocessedDocument(
        file_path=f"D:/temp/{file_name}",
        file_name=file_name,
        file_type=file_type,
        mime_type="application/pdf" if file_type == "pdf" else "image/jpeg",
        page_count=len(pages) or 1,
        full_text=text or None,
        page_texts=[text] if text else [],
        pages=pages,
        images=images,
        has_usable_text=bool(text and len(text) > 20),
        requires_vision_processing=not text,
        metadata={"width": width, "height": height} if width and height else {},
    )


def test_clear_application_form_text() -> None:
    """Clear application form text should classify with high confidence."""
    text = (
        "Scholarship Application Form 2026. Applicant Details: Candidate registration number "
        "APP-12345. Scheme name: Pre-matric Scholarship. Student registration details."
    )
    doc = _make_doc(file_name="application_form.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    assert result.document_type == DocumentType.APPLICATION_FORM
    assert result.confidence >= 0.75
    assert result.needs_verification is False
    assert len(result.evidence) >= 1
    assert any("application form" in (e.snippet or "").lower() for e in result.evidence)


def test_clear_identity_document_text() -> None:
    """Clear identity text should classify as aadhaar_or_identity."""
    text = (
        "Government of India. Unique Identification Authority of India. Aadhaar Card. "
        "UIDAI Enrollment No 1234. DOB: 15/08/2004. Gender: Male. help@uidai.gov.in"
    )
    doc = _make_doc(file_name="identity.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    assert result.document_type == DocumentType.AADHAAR_OR_IDENTITY
    assert result.confidence >= 0.75
    assert result.needs_verification is False
    assert any("aadhaar" in (e.snippet or "").lower() for e in result.evidence)


def test_clear_marksheet_text() -> None:
    """Clear academic transcript text should classify as marksheet."""
    text = (
        "University Examination 2025. Statement of Marks. Academic Transcript. "
        "Semester V Grade Card. Total Marks Obtained: 450/500. Percentage: 90%. SGPA: 9.2."
    )
    doc = _make_doc(file_name="marksheet.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    assert result.document_type == DocumentType.MARKSHEET
    assert result.confidence >= 0.75
    assert result.needs_verification is False


def test_clear_income_certificate_text() -> None:
    """Clear income certificate text should classify as income_certificate."""
    text = (
        "Revenue Department, Government of Maharashtra. Family Income Certificate. "
        "Annual Family Income: INR 1,20,000. Certified by Tahasildar, Competent Authority."
    )
    doc = _make_doc(file_name="income_cert.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    assert result.document_type == DocumentType.INCOME_CERTIFICATE
    assert result.confidence >= 0.75
    assert result.needs_verification is False


def test_clear_caste_certificate_text() -> None:
    """Clear caste certificate text should classify as caste_certificate."""
    text = (
        "Office of Competent Authority. Caste Certificate. This is to certify that applicant "
        "belongs to Scheduled Caste community under Constitution Order."
    )
    doc = _make_doc(file_name="caste_cert.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    assert result.document_type == DocumentType.CASTE_CERTIFICATE
    assert result.confidence >= 0.75
    assert result.needs_verification is False


def test_clear_instructions_text() -> None:
    """Clear guidance text should classify as instructions."""
    text = (
        "General Instructions to candidates for scholarship. Guidelines for applicants. "
        "Eligibility criteria and required documents to be uploaded. Maximum file size 2MB."
    )
    doc = _make_doc(file_name="guidelines.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    assert result.document_type == DocumentType.INSTRUCTIONS
    assert result.confidence >= 0.75
    assert result.needs_verification is False


def test_ambiguous_text_requires_verification() -> None:
    """Sparse or ambiguous text must flag needs_verification."""
    text = "Candidate was present on the scheduled date."
    doc = _make_doc(file_name="ambiguous.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    # Low signal confidence must require verification
    assert result.needs_verification is True
    assert result.confidence < 0.75


def test_unknown_empty_document() -> None:
    """Empty documents with no text or images should classify as unknown."""
    doc = _make_doc(file_name="empty.pdf", text="")
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    assert result.document_type == DocumentType.UNKNOWN
    assert result.confidence == 0.0
    assert result.needs_verification is True


def test_confidence_range() -> None:
    """All classification results must produce confidence strictly between 0.0 and 1.0."""
    classifier = DocumentClassifier()

    cases = [
        "Statement of Marks and Semester Grade Card",
        "Unique Identification Authority Aadhaar UIDAI",
        "General instructions and eligibility criteria",
        "",
        "Some random non-matching words in a document",
    ]
    for text in cases:
        res = classifier.classify(_make_doc(text=text))
        assert 0.0 <= res.confidence <= 1.0


def test_needs_verification_for_low_confidence() -> None:
    """Configurable threshold should flag needs_verification when confidence is below threshold."""
    text = "Student details"
    doc = _make_doc(text=text)

    # Default threshold 0.75 -> weak text results in low confidence and needs_verification=True
    classifier_default = DocumentClassifier(verification_threshold=0.75)
    res_default = classifier_default.classify(doc)
    assert res_default.needs_verification is True

    # Very strict threshold 0.99 -> forces needs_verification even on moderate signals
    strict_classifier = DocumentClassifier(verification_threshold=0.99)
    res_strict = strict_classifier.classify(doc)
    assert res_strict.needs_verification is True


def test_evidence_generation() -> None:
    """Evidence objects must include source document, page number, and readable snippet."""
    text = "Candidate Statement of Marks obtained in University Examination."
    doc = _make_doc(file_name="student_marks.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    assert len(result.evidence) > 0
    first_evidence = result.evidence[0]
    assert isinstance(first_evidence, Evidence)
    assert first_evidence.source_document == "student_marks.pdf"
    assert first_evidence.page_number == 1
    assert first_evidence.snippet is not None
    assert len(first_evidence.snippet) > 0


def test_conflicting_signals_handling() -> None:
    """Documents with conflicting strong signals must be flagged for verification."""
    # Balanced signals for both marksheet and income certificate
    text = (
        "Statement of Marks semester examination. "
        "Annual Family Income Certificate issued by Tahasildar."
    )
    doc = _make_doc(file_name="mixed.pdf", text=text)
    classifier = DocumentClassifier()
    result = classifier.classify(doc)

    # Conflicting signals must reduce confidence and flag verification
    assert result.needs_verification is True
    assert result.confidence <= 0.65
    # Evidence should preserve context from the conflict
    assert len(result.evidence) >= 2


def test_photograph_and_image_classification_behavior() -> None:
    """Validate photograph classification against filenames and aspect ratios."""
    classifier = DocumentClassifier()

    # 1. Clear photograph by filename
    photo_doc = _make_doc(
        file_name="candidate_passport_photo.jpg",
        file_type="jpg",
        width=350,
        height=450,
        has_images=True,
    )
    res_photo = classifier.classify(photo_doc)
    assert res_photo.document_type == DocumentType.PHOTOGRAPH
    assert res_photo.confidence >= 0.85
    assert res_photo.needs_verification is False

    # 2. Image with portrait aspect ratio (e.g. 350x450 = 0.77) without photo filename
    portrait_doc = _make_doc(
        file_name="upload_001.jpg",
        file_type="jpg",
        width=350,
        height=450,
        has_images=True,
    )
    res_portrait = classifier.classify(portrait_doc)
    assert res_portrait.document_type == DocumentType.PHOTOGRAPH
    assert res_portrait.needs_verification is True  # Needs verification without filename clue

    # 3. Wide landscape image (e.g. 1000x500 = ratio 2.0) should NOT falsely classify as photograph
    landscape_doc = _make_doc(
        file_name="scan_doc.png",
        file_type="png",
        width=1000,
        height=500,
        has_images=True,
    )
    res_landscape = classifier.classify(landscape_doc)
    assert res_landscape.document_type == DocumentType.UNKNOWN
    assert res_landscape.needs_verification is True


def test_unsupported_or_invalid_input_handling() -> None:
    """Invalid input types should raise DocumentProcessingError."""
    classifier = DocumentClassifier()

    with pytest.raises(DocumentProcessingError):
        classifier.classify("invalid_string_argument")  # type: ignore[arg-type]

    with pytest.raises(DocumentProcessingError):
        classifier.classify(None)  # type: ignore[arg-type]


# ==============================================================================
# MULTILINGUAL DETERMINISTIC CLASSIFICATION TESTS (Hindi, Marathi, Bilingual)
# ==============================================================================

def test_hindi_income_certificate_classification() -> None:
    """Pure Hindi income certificate with clear revenue authority markers."""
    text = "राजस्व विभाग\nतहसीलदार कार्यालय\nआय प्रमाण पत्र\nप्रमाणित किया जाता है कि कुल वार्षिक आय रु. 1,40,000 है।"
    doc = _make_doc(file_name="hindi_income.pdf", text=text)
    classifier = DocumentClassifier()
    res = classifier.classify(doc)

    assert res.document_type == DocumentType.INCOME_CERTIFICATE
    assert res.confidence >= 0.75
    assert res.needs_verification is False
    assert len(res.evidence) >= 1
    assert any("आय प्रमाण पत्र" in (e.snippet or "") for e in res.evidence)


def test_hindi_caste_certificate_classification() -> None:
    """Pure Hindi caste certificate with reserved category markers."""
    text = "सक्षम प्राधिकारी कार्यालय\nजाति प्रमाण पत्र\nप्रमाणित किया जाता है कि आवेदक अनुसूचित जाति वर्ग से संबंधित है।"
    doc = _make_doc(file_name="hindi_caste.pdf", text=text)
    classifier = DocumentClassifier()
    res = classifier.classify(doc)

    assert res.document_type == DocumentType.CASTE_CERTIFICATE
    assert res.confidence >= 0.75
    assert res.needs_verification is False
    assert len(res.evidence) >= 1
    assert any("जाति प्रमाण पत्र" in (e.snippet or "") for e in res.evidence)


def test_hindi_marksheet_classification() -> None:
    """Pure Hindi academic board marksheet with score breakdown."""
    text = "माध्यमिक शिक्षा परिषद\nअंकतालिका\nपरीक्षार्थी का नाम: अमित कुमार\nप्राप्तांक: 430/500\nप्रतिशत: 86.0%"
    doc = _make_doc(file_name="hindi_marksheet.pdf", text=text)
    classifier = DocumentClassifier()
    res = classifier.classify(doc)

    assert res.document_type == DocumentType.MARKSHEET
    assert res.confidence >= 0.75
    assert res.needs_verification is False
    assert len(res.evidence) >= 1
    assert any("अंकतालिका" in (e.snippet or "") for e in res.evidence)


def test_hindi_application_form_classification() -> None:
    """Pure Hindi scholarship application submission form."""
    text = "छात्रवृत्ति आवेदन पत्र\nआवेदन संख्या: HIN-2026-101\nआवेदक विवरण: अमित कुमार\nपिता का नाम: राजेश कुमार"
    doc = _make_doc(file_name="hindi_app.pdf", text=text)
    classifier = DocumentClassifier()
    res = classifier.classify(doc)

    assert res.document_type == DocumentType.APPLICATION_FORM
    assert res.confidence >= 0.75
    assert res.needs_verification is False


def test_marathi_income_certificate_classification() -> None:
    """Pure Marathi income certificate with revenue department markers."""
    text = "महाराष्ट्र शासन महसूल विभाग\nतहसीलदार कार्यालय\nउत्पन्न प्रमाणपत्र\nप्रमाणित करण्यात येते की कुटुंबाचे वार्षिक उत्पन्न रु. 1,50,000 आहे."
    doc = _make_doc(file_name="marathi_income.pdf", text=text)
    classifier = DocumentClassifier()
    res = classifier.classify(doc)

    assert res.document_type == DocumentType.INCOME_CERTIFICATE
    assert res.confidence >= 0.75
    assert res.needs_verification is False
    assert len(res.evidence) >= 1
    assert any("उत्पन्न प्रमाणपत्र" in (e.snippet or "") for e in res.evidence)


def test_marathi_caste_certificate_classification() -> None:
    """Pure Marathi caste validity certificate."""
    text = "सक्षम प्राधिकारी उपविभागीय अधिकारी\nजात प्रमाणपत्र\nप्रमाणित करण्यात येते की अर्जदार अनुसूचित जाती प्रवर्गातील आहे."
    doc = _make_doc(file_name="marathi_caste.pdf", text=text)
    classifier = DocumentClassifier()
    res = classifier.classify(doc)

    assert res.document_type == DocumentType.CASTE_CERTIFICATE
    assert res.confidence >= 0.75
    assert res.needs_verification is False
    assert len(res.evidence) >= 1
    assert any("जात प्रमाणपत्र" in (e.snippet or "") for e in res.evidence)


def test_marathi_marksheet_classification() -> None:
    """Pure Marathi state board statement of marks (गुणपत्रिका)."""
    text = "महाराष्ट्र राज्य माध्यमिक व उच्च माध्यमिक शिक्षण मंडळ\nगुणपत्रिका\nविद्यार्थ्याचे नाव: स्नेहा देशमुख\nप्राप्त गुण: 475/500\nटक्केवारी: 95.00%"
    doc = _make_doc(file_name="marathi_marksheet.pdf", text=text)
    classifier = DocumentClassifier()
    res = classifier.classify(doc)

    assert res.document_type == DocumentType.MARKSHEET
    assert res.confidence >= 0.75
    assert res.needs_verification is False
    assert len(res.evidence) >= 1
    assert any("गुणपत्रिका" in (e.snippet or "") for e in res.evidence)


def test_marathi_application_form_classification() -> None:
    """Pure Marathi scholarship portal application form."""
    text = "महाराष्ट्र राज्य शिष्यवृत्ती अर्ज\nअर्ज क्रमांक: MAH-2026-404\nअर्जदार तपशील\nविद्यार्थ्याचे नाव: स्नेहा देशमुख"
    doc = _make_doc(file_name="marathi_app.pdf", text=text)
    classifier = DocumentClassifier()
    res = classifier.classify(doc)

    assert res.document_type == DocumentType.APPLICATION_FORM
    assert res.confidence >= 0.75
    assert res.needs_verification is False


def test_bilingual_classification_robustness() -> None:
    """Bilingual English and Indic documents classify accurately with high confidence."""
    text_hin = "GOVERNMENT OF MAHARASHTRA / महाराष्ट्र शासन\nINCOME CERTIFICATE / आय प्रमाण पत्र\nAnnual Family Income: Rs. 1,60,000"
    doc_hin = _make_doc(file_name="bilingual_income.pdf", text=text_hin)
    classifier = DocumentClassifier()
    res_hin = classifier.classify(doc_hin)

    assert res_hin.document_type == DocumentType.INCOME_CERTIFICATE
    assert res_hin.confidence >= 0.80
    assert res_hin.needs_verification is False

    text_mar = "STATEMENT OF MARKS / गुणपत्रिका\nMarks Obtained: 480/500\nPercentage: 96.00%"
    doc_mar = _make_doc(file_name="bilingual_marks.pdf", text=text_mar)
    res_mar = classifier.classify(doc_mar)

    assert res_mar.document_type == DocumentType.MARKSHEET
    assert res_mar.confidence >= 0.80
    assert res_mar.needs_verification is False


def test_ambiguous_indic_signals_handled_conservatively() -> None:
    """Ambiguous or insufficient Indic text should remain UNKNOWN or require verification."""
    # Text with only generic words like date/name without document type markers
    text_weak = "विद्यार्थ्याचे नाव: अमित पाटील\nदिनांक: 15/08/2024\nपत्ता: पुणे महाराष्ट्र"
    doc_weak = _make_doc(file_name="weak_marathi.pdf", text=text_weak)
    classifier = DocumentClassifier()
    res_weak = classifier.classify(doc_weak)

    # Must NOT guess a document type without evidence
    assert res_weak.document_type == DocumentType.UNKNOWN
    assert res_weak.needs_verification is True

    # Conflicting strong signals: income certificate and marksheet equally claimed
    text_conflict = "आय प्रमाण पत्र\nवार्षिक आय रु. 1,00,000\nअंकतालिका\nप्राप्तांक: 450/500"
    doc_conflict = _make_doc(file_name="conflict_indic.pdf", text=text_conflict)
    res_conflict = classifier.classify(doc_conflict)
    assert res_conflict.needs_verification is True
