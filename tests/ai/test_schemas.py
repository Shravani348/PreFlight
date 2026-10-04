"""Tests for Pydantic AI schemas and data contracts."""

import json
import pytest
from pydantic import ValidationError

from ai.schemas.comparison import ComparisonFinding, MatchStatus
from ai.schemas.document import (
    ClassificationResult,
    DocumentMetadata,
    DocumentType,
    Evidence,
    ProcessingStatus,
)
from ai.schemas.extraction import ExtractedDocument, ExtractedField
from ai.schemas.instructions import InstructionRequirement
from ai.schemas.result import AIProcessingResult


def test_valid_document_types() -> None:
    """Test that all supported scholarship document types are accepted."""
    expected_types = [
        "application_form",
        "aadhaar_or_identity",
        "marksheet",
        "income_certificate",
        "caste_certificate",
        "photograph",
        "instructions",
        "unknown",
    ]
    for doc_type_str in expected_types:
        doc_type = DocumentType(doc_type_str)
        result = ClassificationResult(document_type=doc_type, confidence=0.95)
        assert result.document_type == doc_type_str


def test_unknown_document_type() -> None:
    """Test unknown document type handling and rejection of unmapped types."""
    # 'unknown' is an explicit supported type
    unknown_doc = ClassificationResult(document_type=DocumentType.UNKNOWN)
    assert unknown_doc.document_type == DocumentType.UNKNOWN
    assert unknown_doc.document_type.value == "unknown"

    # Arbitrary strings not in DocumentType must raise ValidationError
    with pytest.raises(ValidationError):
        ClassificationResult(document_type="invalid_doc_type")  # type: ignore[arg-type]


def test_confidence_boundary_zero() -> None:
    """Confidence = 0.0 must be accepted."""
    field = ExtractedField(field_name="dob", confidence=0.0)
    assert field.confidence == 0.0

    classification = ClassificationResult(
        document_type=DocumentType.MARKSHEET, confidence=0.0
    )
    assert classification.confidence == 0.0


def test_confidence_boundary_one() -> None:
    """Confidence = 1.0 must be accepted."""
    field = ExtractedField(field_name="name", confidence=1.0)
    assert field.confidence == 1.0

    classification = ClassificationResult(
        document_type=DocumentType.MARKSHEET, confidence=1.0
    )
    assert classification.confidence == 1.0


def test_confidence_below_zero_rejected() -> None:
    """Confidence below 0.0 must raise ValidationError."""
    with pytest.raises(ValidationError):
        ExtractedField(field_name="name", confidence=-0.01)

    with pytest.raises(ValidationError):
        ClassificationResult(
            document_type=DocumentType.APPLICATION_FORM, confidence=-0.5
        )


def test_confidence_above_one_rejected() -> None:
    """Confidence above 1.0 must raise ValidationError."""
    with pytest.raises(ValidationError):
        ExtractedField(field_name="name", confidence=1.01)

    with pytest.raises(ValidationError):
        ClassificationResult(
            document_type=DocumentType.APPLICATION_FORM, confidence=1.5
        )


def test_missing_optional_fields() -> None:
    """Missing fields should safely default to None or empty collections without inventing values."""
    field = ExtractedField(field_name="name")
    assert field.field_name == "name"
    assert field.original is None
    assert field.normalized is None
    assert field.confidence is None
    assert field.evidence == []

    doc = ExtractedDocument(document_id="doc-001")
    assert doc.document_id == "doc-001"
    assert doc.document_type == DocumentType.UNKNOWN
    assert doc.name is None
    assert doc.date_of_birth is None
    assert doc.father_name is None
    assert doc.mother_name is None
    assert doc.address is None
    assert doc.certificate_number is None
    assert doc.issue_date is None
    assert doc.expiry_date is None
    assert doc.marks is None
    assert doc.percentage is None
    assert doc.additional_fields == {}


def test_original_and_normalized_values_preserved() -> None:
    """Ensure original raw string and normalized string are both preserved separately."""
    field = ExtractedField(
        field_name="name",
        original="Priti Shashikant Ahire",
        normalized="priti shashikant ahire",
        confidence=0.97,
    )
    assert field.original == "Priti Shashikant Ahire"
    assert field.normalized == "priti shashikant ahire"
    assert field.original != field.normalized


def test_evidence_with_page_and_snippet() -> None:
    """Evidence model supports source document, page number, and snippet."""
    evidence = Evidence(
        source_document="income_certificate.pdf",
        page_number=1,
        snippet="Annual Family Income: INR 1,50,000",
    )
    assert evidence.source_document == "income_certificate.pdf"
    assert evidence.page_number == 1
    assert evidence.snippet == "Annual Family Income: INR 1,50,000"

    # Evidence with omitted optional fields
    empty_evidence = Evidence()
    assert empty_evidence.source_document is None
    assert empty_evidence.page_number is None
    assert empty_evidence.snippet is None


def test_top_level_ai_result_serialization() -> None:
    """Verify top-level AIProcessingResult serialization and structure."""
    doc = ExtractedDocument(
        document_id="doc-123",
        document_type=DocumentType.AADHAAR_OR_IDENTITY,
        name=ExtractedField(
            field_name="name",
            original="PRITI AHIRE",
            normalized="priti ahire",
            confidence=0.98,
        ),
    )
    finding = ComparisonFinding(
        field_name="name",
        source_document="doc-123",
        comparison_document="doc-456",
        source_value="PRITI AHIRE",
        comparison_value="Priti S Ahire",
        normalized_source_value="priti ahire",
        normalized_comparison_value="priti s ahire",
        similarity_score=0.92,
        status=MatchStatus.LIKELY_MATCH,
        needs_verification=True,
        explanation="Middle name abbreviated",
    )
    requirement = InstructionRequirement(
        requirement_type="required_document",
        document_type_requested=DocumentType.INCOME_CERTIFICATE,
        is_required=True,
        accepted_formats=["pdf", "jpg"],
    )

    result = AIProcessingResult(
        documents=[doc],
        cross_document_findings=[finding],
        instruction_requirements=[requirement],
    )

    data = result.model_dump()
    assert len(data["documents"]) == 1
    assert data["documents"][0]["name"]["original"] == "PRITI AHIRE"
    assert len(data["cross_document_findings"]) == 1
    assert data["cross_document_findings"][0]["status"] == "likely_match"
    assert len(data["instruction_requirements"]) == 1
    assert data["instruction_requirements"][0]["document_type_requested"] == "income_certificate"


def test_json_serialization_roundtrip() -> None:
    """Verify JSON export and deserialization roundtrip."""
    result = AIProcessingResult(
        documents=[
            ExtractedDocument(
                document_id="doc-789",
                document_type=DocumentType.MARKSHEET,
                percentage=ExtractedField(
                    field_name="percentage",
                    original="88.5%",
                    normalized=88.5,
                    confidence=0.95,
                    evidence=[
                        Evidence(
                            source_document="marksheet.pdf",
                            page_number=1,
                            snippet="Total: 88.50%",
                        )
                    ],
                ),
            )
        ]
    )

    json_str = result.model_dump_json()
    assert isinstance(json_str, str)

    parsed = json.loads(json_str)
    assert parsed["documents"][0]["document_type"] == "marksheet"
    assert parsed["documents"][0]["percentage"]["normalized"] == 88.5

    # Roundtrip validation back into Pydantic model
    validated = AIProcessingResult.model_validate_json(json_str)
    assert validated.documents[0].document_type == DocumentType.MARKSHEET
    assert validated.documents[0].percentage is not None
    assert validated.documents[0].percentage.normalized == 88.5


def test_invalid_enum_status_values_rejected() -> None:
    """Invalid enum values for MatchStatus and ProcessingStatus must raise ValidationError."""
    with pytest.raises(ValidationError):
        ComparisonFinding(
            field_name="dob",
            source_document="docA",
            comparison_document="docB",
            status="not_a_valid_status",  # type: ignore[arg-type]
        )

    with pytest.raises(ValidationError):
        DocumentMetadata(
            document_id="doc1",
            processing_status="unknown_status",  # type: ignore[arg-type]
        )
