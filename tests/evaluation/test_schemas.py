"""Tests for evaluation dataset and metric Pydantic schemas."""

import pytest
from pydantic import ValidationError

from ai.schemas.comparison import MatchStatus
from ai.schemas.document import DocumentType
from evaluation.schemas import (
    BenchmarkReport,
    ClassificationMetrics,
    ClassificationTestCase,
    ExtractionMetrics,
    FieldExtractionTestCase,
    InstructionMetrics,
    InstructionTestCase,
    MatchingMetrics,
    MatchingTestCase,
)


def test_classification_test_case_schema() -> None:
    """Verify ClassificationTestCase validation and serialization."""
    case = ClassificationTestCase(
        case_id="case_001",
        description="Sample marksheet",
        file_name="marksheet.pdf",
        text_content="STATEMENT OF MARKS",
        expected_document_type=DocumentType.MARKSHEET,
        expected_needs_verification=False,
    )
    assert case.case_id == "case_001"
    assert case.expected_document_type == DocumentType.MARKSHEET

    # Extra fields should be forbidden
    with pytest.raises(ValidationError):
        ClassificationTestCase(
            case_id="bad_001",
            file_name="bad.pdf",
            expected_document_type=DocumentType.MARKSHEET,
            unrecognized_field="illegal",
        )


def test_matching_test_case_schema() -> None:
    """Verify MatchingTestCase validation and serialization."""
    case = MatchingTestCase(
        case_id="match_001",
        field_name="name",
        value_a="Priti Ahire",
        value_b="Priti Ahire",
        expected_status=MatchStatus.MATCH,
    )
    assert case.case_id == "match_001"
    assert case.expected_status == MatchStatus.MATCH

    with pytest.raises(ValidationError):
        MatchingTestCase(
            case_id="bad_match",
            field_name="name",
            expected_status="invalid_status_enum",
        )


def test_instruction_test_case_schema() -> None:
    """Verify InstructionTestCase validation."""
    case = InstructionTestCase(
        case_id="inst_001",
        instruction_text="Upload Aadhaar card in PDF format.",
        expected_requirement_types=["required_document", "file_format"],
        expected_document_types=[DocumentType.AADHAAR_OR_IDENTITY],
        expected_constraints={"format": "pdf"},
    )
    assert len(case.expected_requirement_types) == 2
    assert case.expected_document_types[0] == DocumentType.AADHAAR_OR_IDENTITY


def test_extraction_test_case_schema() -> None:
    """Verify FieldExtractionTestCase validation."""
    case = FieldExtractionTestCase(
        case_id="ext_001",
        document_type=DocumentType.MARKSHEET,
        document_text="Marks: 450/500",
        expected_fields={"marks": "450/500"},
        expected_normalized_fields={"marks": "450/500"},
    )
    assert case.document_type == DocumentType.MARKSHEET
    assert case.expected_fields["marks"] == "450/500"


def test_benchmark_report_schema() -> None:
    """Verify BenchmarkReport default attributes and serialization."""
    report = BenchmarkReport(
        dataset_name="DEVELOPMENT / SYNTHETIC EVALUATION DATA",
        is_synthetic=True,
    )
    assert report.is_synthetic is True
    assert "NOT" in report.disclaimer
    assert report.classification is None

    # Test with metric children
    report.classification = ClassificationMetrics(
        total_cases=10,
        correct=8,
        accuracy=0.8,
        precision_macro=0.82,
        recall_macro=0.80,
        f1_macro=0.81,
        by_language={"english": {"total_cases": 10, "correct": 8, "accuracy": 0.8, "f1_macro": 0.81}},
        by_condition={"clean": {"total_cases": 10, "correct": 8, "accuracy": 0.8, "f1_macro": 0.81}},
    )
    data = report.model_dump()
    assert data["classification"]["accuracy"] == 0.8
    assert "english" in data["classification"]["by_language"]


def test_schema_metadata_fields() -> None:
    """Verify that language, document_condition, and difficulty metadata are supported with defaults."""
    c_case = ClassificationTestCase(
        case_id="case_meta_01",
        file_name="meta.pdf",
        expected_document_type=DocumentType.MARKSHEET,
        language="marathi",
        document_condition="scanned",
        difficulty="hard",
    )
    assert c_case.language == "marathi"
    assert c_case.document_condition == "scanned"
    assert c_case.difficulty == "hard"

    m_case = MatchingTestCase(
        case_id="match_meta_01",
        field_name="name",
        value_a="अमित पाटील",
        value_b="अमित पाटील",
        expected_status=MatchStatus.MATCH,
        language="marathi",
        document_condition="clean",
        difficulty="easy",
    )
    assert m_case.language == "marathi"
    assert m_case.value_a == "अमित पाटील"

    i_case = InstructionTestCase(
        case_id="inst_meta_01",
        instruction_text="उत्पन्न प्रमाणपत्र आवश्यक आहे.",
        expected_requirement_types=["required_document"],
        language="marathi",
    )
    assert i_case.language == "marathi"
    assert i_case.document_condition == "clean"

    e_case = FieldExtractionTestCase(
        case_id="ext_meta_01",
        document_type=DocumentType.INCOME_CERTIFICATE,
        document_text="आय प्रमाण पत्र",
        expected_fields={"name": "राजेश शर्मा"},
        language="hindi",
    )
    assert e_case.language == "hindi"
    assert e_case.difficulty == "easy"
