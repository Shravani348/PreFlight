"""Comprehensive unit tests for AI confidence and verification layer."""

import pytest
from ai.schemas.comparison import ComparisonFinding, MatchStatus
from ai.schemas.document import ClassificationResult, DocumentType, Evidence
from ai.schemas.extraction import ExtractedDocument, ExtractedField
from ai.verification import (
    ConfidenceLevel,
    ConfidenceService,
    ConfidenceThresholds,
    VerificationItem,
    VerificationResult,
    VerificationService,
)


# ==============================================================================
# 1. BASIC CONFIDENCE THRESHOLD TESTS (1 - 6 + Threshold Validation)
# ==============================================================================

def test_confidence_level_0_95_is_high() -> None:
    """1. 0.95 maps to HIGH_CONFIDENCE."""
    service = ConfidenceService()
    assert service.get_confidence_level(0.95) == ConfidenceLevel.HIGH_CONFIDENCE


def test_confidence_level_0_90_is_high() -> None:
    """2. 0.90 (exact boundary) maps to HIGH_CONFIDENCE."""
    service = ConfidenceService()
    assert service.get_confidence_level(0.90) == ConfidenceLevel.HIGH_CONFIDENCE


def test_confidence_level_0_89_is_medium() -> None:
    """3. 0.89 maps to MEDIUM_CONFIDENCE."""
    service = ConfidenceService()
    assert service.get_confidence_level(0.89) == ConfidenceLevel.MEDIUM_CONFIDENCE


def test_confidence_level_0_75_is_medium() -> None:
    """4. 0.75 (exact boundary) maps to MEDIUM_CONFIDENCE."""
    service = ConfidenceService()
    assert service.get_confidence_level(0.75) == ConfidenceLevel.MEDIUM_CONFIDENCE


def test_confidence_level_0_74_is_low() -> None:
    """5. 0.74 maps to LOW_CONFIDENCE."""
    service = ConfidenceService()
    assert service.get_confidence_level(0.74) == ConfidenceLevel.LOW_CONFIDENCE


def test_confidence_level_0_00_is_low() -> None:
    """6. 0.00 maps to LOW_CONFIDENCE."""
    service = ConfidenceService()
    assert service.get_confidence_level(0.00) == ConfidenceLevel.LOW_CONFIDENCE


def test_threshold_validation_rejects_invalid_ranges() -> None:
    """Extra: Threshold validation enforces 0 <= medium < high <= 1."""
    with pytest.raises(ValueError):
        ConfidenceService(high_threshold=0.70, medium_threshold=0.85)

    with pytest.raises(ValueError):
        ConfidenceService(high_threshold=0.80, medium_threshold=0.80)


# ==============================================================================
# 2. MISSING VALUES TESTS (7 - 10)
# ==============================================================================

def test_missing_original_and_normalized_value() -> None:
    """7. Missing original and normalized values produce MISSING level and needs_verification=True."""
    service = ConfidenceService()
    field = ExtractedField(field_name="name", original=None, normalized=None, confidence=0.98)
    item = service.evaluate_field(field)
    assert item.confidence_level == ConfidenceLevel.MISSING
    assert item.confidence is None
    assert item.needs_verification is True
    assert "missing" in item.reason.lower()


def test_missing_normalized_with_present_original() -> None:
    """8. Present original with missing normalized evaluates based on extraction confidence."""
    service = ConfidenceService()
    field = ExtractedField(field_name="name", original="Priti Ahire", normalized=None, confidence=0.95)
    item = service.evaluate_field(field)
    assert item.confidence_level == ConfidenceLevel.HIGH_CONFIDENCE
    assert item.needs_verification is False


def test_missing_confidence() -> None:
    """9. Missing confidence produces MISSING level and flags verification."""
    service = ConfidenceService()
    field = ExtractedField(field_name="name", original="Priti Ahire", normalized="priti ahire", confidence=None)
    item = service.evaluate_field(field)
    assert item.confidence_level == ConfidenceLevel.MISSING
    assert item.confidence is None
    assert item.needs_verification is True
    assert "no confidence score" in item.reason.lower()


def test_completely_missing_field() -> None:
    """10. None field passed to evaluate_field produces safe MISSING item."""
    service = ConfidenceService()
    item = service.evaluate_field(None, field_name="date_of_birth", source="app_form")
    assert item.field_name == "date_of_birth"
    assert item.confidence_level == ConfidenceLevel.MISSING
    assert item.confidence is None
    assert item.needs_verification is True
    assert "missing" in item.reason.lower()


# ==============================================================================
# 3. EXTRACTION VERIFICATION TESTS (11 - 15)
# ==============================================================================

def test_high_confidence_extracted_name() -> None:
    """11. High confidence name produces needs_verification=False."""
    service = ConfidenceService()
    field = ExtractedField(
        field_name="name",
        original="Priti Shashikant Ahire",
        normalized="priti shashikant ahire",
        confidence=0.97,
    )
    item = service.evaluate_field(field)
    assert item.confidence_level == ConfidenceLevel.HIGH_CONFIDENCE
    assert item.needs_verification is False
    assert item.confidence == 0.97


def test_medium_confidence_dob() -> None:
    """12. Medium confidence DOB flags needs_verification=True."""
    service = ConfidenceService()
    field = ExtractedField(
        field_name="date_of_birth",
        original="01/05/2005",
        normalized="2005-05-01",
        confidence=0.82,
    )
    item = service.evaluate_field(field)
    assert item.confidence_level == ConfidenceLevel.MEDIUM_CONFIDENCE
    assert item.needs_verification is True
    assert "medium confidence" in item.reason.lower()


def test_low_confidence_father_name() -> None:
    """13. Low confidence father name flags needs_verification=True."""
    service = ConfidenceService()
    field = ExtractedField(
        field_name="father_name",
        original="Shashikant Ahire",
        normalized="shashikant ahire",
        confidence=0.54,
    )
    item = service.evaluate_field(field)
    assert item.confidence_level == ConfidenceLevel.LOW_CONFIDENCE
    assert item.needs_verification is True
    assert "low confidence" in item.reason.lower()


def test_multiple_fields_in_one_document() -> None:
    """14. Evaluates all present fields in an ExtractedDocument."""
    service = ConfidenceService()
    doc = ExtractedDocument(
        document_id="doc_multi",
        name=ExtractedField(field_name="name", original="Priti", normalized="priti", confidence=0.96),
        date_of_birth=ExtractedField(field_name="date_of_birth", original="2005", normalized="2005-01-01", confidence=0.80),
        father_name=ExtractedField(field_name="father_name", original="Shashi", normalized="shashi", confidence=0.50),
    )
    items = service.evaluate_document(doc)
    assert len(items) == 3
    levels = [i.confidence_level for i in items]
    assert levels == [
        ConfidenceLevel.HIGH_CONFIDENCE,
        ConfidenceLevel.MEDIUM_CONFIDENCE,
        ConfidenceLevel.LOW_CONFIDENCE,
    ]


def test_evidence_preserved_in_verification_item() -> None:
    """15. Evidence list is completely preserved in VerificationItem."""
    service = ConfidenceService()
    evidence_list = [
        Evidence(source_document="app.pdf", page_number=1, snippet="Applicant: Priti Ahire")
    ]
    field = ExtractedField(
        field_name="name",
        original="Priti Ahire",
        normalized="priti ahire",
        confidence=0.92,
        evidence=evidence_list,
    )
    item = service.evaluate_field(field)
    assert len(item.evidence) == 1
    assert item.evidence[0].source_document == "app.pdf"
    assert item.evidence[0].snippet == "Applicant: Priti Ahire"


# ==============================================================================
# 4. CLASSIFICATION VERIFICATION TESTS (16 - 20)
# ==============================================================================

def test_high_confidence_classification() -> None:
    """16. High confidence classification does not need verification by default."""
    service = ConfidenceService()
    classification = ClassificationResult(
        document_type=DocumentType.APPLICATION_FORM,
        confidence=0.96,
        needs_verification=False,
    )
    item = service.evaluate_classification(classification)
    assert item.confidence_level == ConfidenceLevel.HIGH_CONFIDENCE
    assert item.needs_verification is False


def test_medium_confidence_classification() -> None:
    """17. Medium confidence classification flags verification."""
    service = ConfidenceService()
    classification = ClassificationResult(
        document_type=DocumentType.MARKSHEET,
        confidence=0.82,
        needs_verification=False,
    )
    item = service.evaluate_classification(classification)
    assert item.confidence_level == ConfidenceLevel.MEDIUM_CONFIDENCE
    assert item.needs_verification is True
    assert "uncertain" in item.reason.lower()


def test_low_confidence_classification() -> None:
    """18. Low confidence classification flags verification."""
    service = ConfidenceService()
    classification = ClassificationResult(
        document_type=DocumentType.INCOME_CERTIFICATE,
        confidence=0.55,
        needs_verification=False,
    )
    item = service.evaluate_classification(classification)
    assert item.confidence_level == ConfidenceLevel.LOW_CONFIDENCE
    assert item.needs_verification is True


def test_unknown_document_type() -> None:
    """19. UNKNOWN document type always requires human verification."""
    service = ConfidenceService()
    classification = ClassificationResult(
        document_type=DocumentType.UNKNOWN,
        confidence=0.99,  # High confidence of being unknown
        needs_verification=False,
    )
    item = service.evaluate_classification(classification)
    assert item.needs_verification is True
    assert "unknown" in item.reason.lower()


def test_existing_needs_verification_flag_preserved() -> None:
    """20. Existing needs_verification=True from classifier is preserved despite high confidence."""
    service = ConfidenceService()
    classification = ClassificationResult(
        document_type=DocumentType.CASTE_CERTIFICATE,
        confidence=0.98,
        needs_verification=True,  # e.g. flagged by secondary heuristic
    )
    item = service.evaluate_classification(classification)
    assert item.confidence_level == ConfidenceLevel.HIGH_CONFIDENCE
    assert item.needs_verification is True


# ==============================================================================
# 5. MATCHING VERIFICATION TESTS (21 - 25)
# ==============================================================================

def test_matching_status_match() -> None:
    """21. MATCH status requires no verification."""
    service = ConfidenceService()
    finding = ComparisonFinding(
        field_name="name",
        source_document="app",
        comparison_document="aadhaar",
        similarity_score=1.0,
        status=MatchStatus.MATCH,
        needs_verification=False,
    )
    item = service.evaluate_finding(finding)
    assert item.confidence_level == ConfidenceLevel.HIGH_CONFIDENCE
    assert item.needs_verification is False


def test_matching_status_likely_match() -> None:
    """22. LIKELY_MATCH status requires verification."""
    service = ConfidenceService()
    finding = ComparisonFinding(
        field_name="name",
        source_document="app",
        comparison_document="aadhaar",
        similarity_score=0.92,
        status=MatchStatus.LIKELY_MATCH,
        needs_verification=True,
    )
    item = service.evaluate_finding(finding)
    assert item.confidence_level == ConfidenceLevel.MEDIUM_CONFIDENCE
    assert item.needs_verification is True


def test_matching_status_verification_required() -> None:
    """23. VERIFICATION_REQUIRED status requires verification."""
    service = ConfidenceService()
    finding = ComparisonFinding(
        field_name="name",
        source_document="app",
        comparison_document="aadhaar",
        similarity_score=0.85,
        status=MatchStatus.VERIFICATION_REQUIRED,
        needs_verification=True,
    )
    item = service.evaluate_finding(finding)
    assert item.confidence_level == ConfidenceLevel.MEDIUM_CONFIDENCE
    assert item.needs_verification is True


def test_matching_status_mismatch() -> None:
    """24. MISMATCH status requires verification without rejecting."""
    service = ConfidenceService()
    finding = ComparisonFinding(
        field_name="date_of_birth",
        source_document="app",
        comparison_document="marksheet",
        similarity_score=0.0,
        status=MatchStatus.MISMATCH,
        needs_verification=False,
    )
    item = service.evaluate_finding(finding)
    assert item.confidence_level == ConfidenceLevel.LOW_CONFIDENCE
    assert item.needs_verification is True
    assert "do not match" in item.reason.lower()


def test_matching_status_missing() -> None:
    """25. MISSING status produces MISSING confidence level and flags verification."""
    service = ConfidenceService()
    finding = ComparisonFinding(
        field_name="father_name",
        source_document="app",
        comparison_document="marksheet",
        similarity_score=None,
        status=MatchStatus.MISSING,
        needs_verification=False,
    )
    item = service.evaluate_finding(finding)
    assert item.confidence_level == ConfidenceLevel.MISSING
    assert item.confidence is None
    assert item.needs_verification is True


# ==============================================================================
# 6. AGGREGATE VERIFICATION RESULT TESTS (26 - 30)
# ==============================================================================

def test_aggregate_multiple_documents() -> None:
    """26. Evaluates multiple documents and aggregates item counts."""
    service = ConfidenceService()
    doc1 = ExtractedDocument(
        document_id="doc1",
        name=ExtractedField(field_name="name", original="A", normalized="a", confidence=0.95),
    )
    doc2 = ExtractedDocument(
        document_id="doc2",
        name=ExtractedField(field_name="name", original="B", normalized="b", confidence=0.60),
    )
    result = service.evaluate_documents([doc1, doc2])
    assert len(result.items) == 2
    assert result.high_confidence_count == 1
    assert result.low_confidence_count == 1
    assert result.verification_required is True


def test_deterministic_ordering_across_inputs() -> None:
    """27. Input permutation yields deterministic item ordering."""
    service = ConfidenceService()
    doc_b = ExtractedDocument(
        document_id="doc_b",
        name=ExtractedField(field_name="name", original="B", normalized="b", confidence=0.95),
    )
    doc_a = ExtractedDocument(
        document_id="doc_a",
        name=ExtractedField(field_name="name", original="A", normalized="a", confidence=0.95),
    )
    res1 = service.evaluate_documents([doc_b, doc_a])
    res2 = service.evaluate_documents([doc_a, doc_b])

    assert [i.source for i in res1.items] == ["doc_a", "doc_b"]
    assert [i.source for i in res2.items] == ["doc_a", "doc_b"]


def test_deterministic_repeated_output() -> None:
    """28. Running evaluation repeatedly produces identical VerificationResult."""
    service = ConfidenceService()
    doc = ExtractedDocument(
        document_id="doc1",
        name=ExtractedField(field_name="name", original="Priti", normalized="priti", confidence=0.88),
    )
    res1 = service.evaluate_documents([doc])
    res2 = service.evaluate_documents([doc])

    assert res1.model_dump() == res2.model_dump()


def test_aggregate_counts_are_accurate() -> None:
    """29. All category counts sum to total items."""
    service = ConfidenceService()
    doc = ExtractedDocument(
        document_id="d1",
        name=ExtractedField(field_name="name", original="A", normalized="a", confidence=0.95),      # HIGH
        date_of_birth=ExtractedField(field_name="dob", original="B", normalized="b", confidence=0.80), # MED
        father_name=ExtractedField(field_name="fn", original="C", normalized="c", confidence=0.50),  # LOW
        mother_name=ExtractedField(field_name="mn", original=None, normalized=None, confidence=None),  # MISSING
    )
    res = service.evaluate_documents([doc])
    assert res.high_confidence_count == 1
    assert res.medium_confidence_count == 1
    assert res.low_confidence_count == 1
    assert res.missing_count == 1
    assert len(res.items) == 4


def test_verification_required_true_when_any_item_requires_verification() -> None:
    """30. verification_required is True if at least one item requires verification, False if none."""
    service = ConfidenceService()
    doc_clean = ExtractedDocument(
        document_id="clean",
        name=ExtractedField(field_name="name", original="A", normalized="a", confidence=0.99),
    )
    res_clean = service.evaluate_documents([doc_clean])
    assert res_clean.verification_required is False

    doc_uncertain = ExtractedDocument(
        document_id="uncertain",
        name=ExtractedField(field_name="name", original="A", normalized="a", confidence=0.70),
    )
    res_uncertain = service.evaluate_documents([doc_clean, doc_uncertain])
    assert res_uncertain.verification_required is True


# ==============================================================================
# 7. SAFETY BOUNDARY TESTS (31 - 34)
# ==============================================================================

def test_mismatch_does_not_produce_rejection() -> None:
    """31. Mismatch only requests verification without application rejection or decision."""
    service = ConfidenceService()
    finding = ComparisonFinding(
        field_name="name",
        source_document="app",
        comparison_document="aadhaar",
        similarity_score=0.10,
        status=MatchStatus.MISMATCH,
        needs_verification=False,
    )
    item = service.evaluate_finding(finding)
    assert item.needs_verification is True
    # Ensure no decision, approval, or rejection attributes exist
    assert not hasattr(item, "decision")
    assert not hasattr(item, "status")
    assert not hasattr(item, "application_status")
    assert "reject" not in item.reason.lower()


def test_low_confidence_does_not_produce_rejection() -> None:
    """32. Low confidence flags human verification without rejecting."""
    service = ConfidenceService()
    field = ExtractedField(field_name="name", original="Priti", normalized="priti", confidence=0.10)
    item = service.evaluate_field(field)
    assert item.needs_verification is True
    assert not hasattr(item, "is_rejected")
    assert "reject" not in item.reason.lower()


def test_missing_field_does_not_produce_rejection() -> None:
    """33. Missing field flags verification without making final application decision."""
    service = ConfidenceService()
    item = service.evaluate_field(None, field_name="caste_certificate")
    assert item.needs_verification is True
    assert "reject" not in item.reason.lower()


def test_no_confidence_invented_for_missing_values() -> None:
    """34. Confidence remains None for missing values."""
    service = ConfidenceService()
    field = ExtractedField(field_name="address", original=None, normalized=None, confidence=None)
    item = service.evaluate_field(field)
    assert item.confidence is None
    assert item.confidence_level == ConfidenceLevel.MISSING
