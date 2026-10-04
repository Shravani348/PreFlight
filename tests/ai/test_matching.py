"""Comprehensive test suite for cross-document matching and name comparison."""

import pytest
from ai.matching import (
    ComparisonFinding,
    CrossDocumentMatcher,
    MatchStatus,
    NameMatcher,
    compare_documents,
    compare_names,
)
from ai.schemas.document import DocumentType
from ai.schemas.extraction import ExtractedDocument, ExtractedField


# ==============================================================================
# 1. NAME MATCHING TESTS (1 - 9)
# ==============================================================================

def test_name_exact_normalized() -> None:
    """1. Exact normalized name produces MATCH with similarity 1.0."""
    matcher = NameMatcher()
    finding = matcher.compare("priti shashikant ahire", "priti shashikant ahire")
    assert finding.status == MatchStatus.MATCH
    assert finding.similarity_score == 1.0
    assert finding.needs_verification is False
    assert "matches exactly" in finding.explanation.lower()


def test_name_highly_similar() -> None:
    """2. Highly similar names produce LIKELY_MATCH with high similarity."""
    matcher = NameMatcher(likely_match_threshold=0.90)
    finding = matcher.compare("priti shashikant ahire", "priti s ahire")
    assert finding.status in (MatchStatus.LIKELY_MATCH, MatchStatus.VERIFICATION_REQUIRED)
    assert finding.similarity_score is not None
    assert finding.similarity_score >= 0.75
    assert finding.needs_verification is True


def test_name_initials() -> None:
    """3. Names with initials are compared via similarity without expanding initials."""
    matcher = NameMatcher()
    finding = matcher.compare("priti s ahire", "priti shashikant ahire")
    # Verified that original normalized inputs are untouched
    assert finding.normalized_source_value == "priti s ahire"
    assert finding.normalized_comparison_value == "priti shashikant ahire"
    assert finding.similarity_score is not None
    assert finding.status in (MatchStatus.LIKELY_MATCH, MatchStatus.VERIFICATION_REQUIRED)


def test_name_different() -> None:
    """4. Completely different names produce MISMATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("priti ahire", "rahul patil")
    assert finding.status == MatchStatus.MISMATCH
    assert finding.similarity_score is not None
    assert finding.similarity_score < 0.75
    assert finding.needs_verification is False
    assert "differ significantly" in finding.explanation.lower()


def test_name_missing_left_value() -> None:
    """5. Missing left name produces MISSING status."""
    matcher = NameMatcher()
    finding = matcher.compare(None, "priti ahire")
    assert finding.status == MatchStatus.MISSING
    assert finding.similarity_score is None
    assert finding.needs_verification is False


def test_name_missing_right_value() -> None:
    """6. Missing right name produces MISSING status."""
    matcher = NameMatcher()
    finding = matcher.compare("priti ahire", None)
    assert finding.status == MatchStatus.MISSING
    assert finding.similarity_score is None
    assert finding.needs_verification is False


def test_name_both_missing() -> None:
    """7. Both missing values produce MISSING status."""
    matcher = NameMatcher()
    finding = matcher.compare(None, None)
    assert finding.status == MatchStatus.MISSING
    assert finding.similarity_score is None
    assert finding.needs_verification is False


def test_name_similarity_score_range() -> None:
    """8. Similarity score is strictly between 0.0 and 1.0 or None."""
    matcher = NameMatcher()
    f1 = matcher.compare("priti ahire", "priti s ahire")
    assert 0.0 <= f1.similarity_score <= 1.0

    f2 = matcher.compare("priti ahire", "rahul patil")
    assert 0.0 <= f2.similarity_score <= 1.0

    f3 = matcher.compare(None, "priti ahire")
    assert f3.similarity_score is None


def test_name_configurable_thresholds() -> None:
    """9. Configurable thresholds adjust status boundaries."""
    # Stricter likely match threshold (0.95 instead of 0.90)
    strict_matcher = NameMatcher(likely_match_threshold=0.95, verification_threshold=0.80)
    finding = strict_matcher.compare("priti s ahire", "priti shashikant ahire")
    # Score is ~0.9167, which falls between 0.80 and 0.95 -> VERIFICATION_REQUIRED
    assert finding.status == MatchStatus.VERIFICATION_REQUIRED

    # Lenient threshold
    lenient_matcher = NameMatcher(likely_match_threshold=0.85, verification_threshold=0.60)
    finding_lenient = lenient_matcher.compare("priti s ahire", "priti shashikant ahire")
    assert finding_lenient.status == MatchStatus.LIKELY_MATCH


# ==============================================================================
# 2. DATE MATCHING TESTS (10 - 12)
# ==============================================================================

def test_date_same_dob() -> None:
    """10. Same normalized DOB produces MATCH with similarity 1.0."""
    matcher = CrossDocumentMatcher()
    finding = matcher.compare_date("2005-05-01", "2005-05-01", "doc_a", "doc_b")
    assert finding.status == MatchStatus.MATCH
    assert finding.similarity_score == 1.0
    assert finding.needs_verification is False
    assert "matches exactly" in finding.explanation.lower()


def test_date_different_dob() -> None:
    """11. Different normalized DOB produces MISMATCH with similarity 0.0."""
    matcher = CrossDocumentMatcher()
    finding = matcher.compare_date("2005-05-01", "2005-05-02", "doc_a", "doc_b")
    assert finding.status == MatchStatus.MISMATCH
    assert finding.similarity_score == 0.0
    assert finding.needs_verification is False
    assert "differs between" in finding.explanation.lower()


def test_date_missing_dob() -> None:
    """12. Missing DOB produces MISSING status without guessing."""
    matcher = CrossDocumentMatcher()
    finding = matcher.compare_date(None, "2005-05-01", "doc_a", "doc_b")
    assert finding.status == MatchStatus.MISSING
    assert finding.similarity_score is None


# ==============================================================================
# 3. FATHER / MOTHER NAME MATCHING TESTS (13 - 15)
# ==============================================================================

def test_parent_name_exact() -> None:
    """13. Exact father/mother name produces MATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("shashikant ahire", "shashikant ahire", field_name="father_name")
    assert finding.status == MatchStatus.MATCH
    assert finding.similarity_score == 1.0


def test_parent_name_similar() -> None:
    """14. Similar mother name produces LIKELY_MATCH or VERIFICATION_REQUIRED."""
    matcher = NameMatcher()
    finding = matcher.compare("surekha ahire", "surekha s ahire", field_name="mother_name")
    assert finding.status in (MatchStatus.LIKELY_MATCH, MatchStatus.VERIFICATION_REQUIRED)
    assert finding.needs_verification is True


def test_parent_name_mismatch() -> None:
    """15. Different father name produces MISMATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("shashikant ahire", "ramesh patil", field_name="father_name")
    assert finding.status == MatchStatus.MISMATCH
    assert finding.similarity_score < 0.75


# ==============================================================================
# 4. ADDRESS MATCHING TESTS (16 - 18)
# ==============================================================================

def test_address_exact_normalized() -> None:
    """16. Exact normalized address produces MATCH with similarity 1.0."""
    matcher = CrossDocumentMatcher()
    finding = matcher.compare_address("123 main road, nashik", "123 main road, nashik", "app", "aadhaar")
    assert finding.status == MatchStatus.MATCH
    assert finding.similarity_score == 1.0
    assert finding.needs_verification is False


def test_address_reasonably_similar() -> None:
    """17. Reasonably similar address produces review status."""
    matcher = CrossDocumentMatcher()
    finding = matcher.compare_address(
        "123 main road, nashik, maharashtra",
        "123 main rd, nashik, maharashtra 422003",
        "app",
        "aadhaar",
    )
    assert finding.status in (MatchStatus.LIKELY_MATCH, MatchStatus.VERIFICATION_REQUIRED)
    assert finding.needs_verification is True


def test_address_clearly_different() -> None:
    """18. Clearly different address produces MISMATCH."""
    matcher = CrossDocumentMatcher()
    finding = matcher.compare_address(
        "123 main road, nashik",
        "456 park lane, pune",
        "app",
        "aadhaar",
    )
    assert finding.status == MatchStatus.MISMATCH
    assert finding.similarity_score < 0.70


# ==============================================================================
# 5. CROSS-DOCUMENT MATCHING TESTS (19 - 25)
# ==============================================================================

def test_cross_doc_application_vs_aadhaar() -> None:
    """19. Application form vs Aadhaar matching name, DOB, and address."""
    doc_app = ExtractedDocument(
        document_id="app_01",
        document_type=DocumentType.APPLICATION_FORM,
        name=ExtractedField(field_name="name", original="Priti S Ahire", normalized="priti s ahire"),
        date_of_birth=ExtractedField(field_name="date_of_birth", original="01/05/2005", normalized="2005-05-01"),
        address=ExtractedField(field_name="address", original="Nashik", normalized="nashik"),
    )
    doc_aadhaar = ExtractedDocument(
        document_id="aadhaar_01",
        document_type=DocumentType.AADHAAR_OR_IDENTITY,
        name=ExtractedField(field_name="name", original="Priti Shashikant Ahire", normalized="priti shashikant ahire"),
        date_of_birth=ExtractedField(field_name="date_of_birth", original="01-05-2005", normalized="2005-05-01"),
        address=ExtractedField(field_name="address", original="Nashik", normalized="nashik"),
    )

    matcher = CrossDocumentMatcher()
    findings = matcher.match_documents([doc_app, doc_aadhaar])

    name_f = next(f for f in findings if f.field_name == "name")
    dob_f = next(f for f in findings if f.field_name == "date_of_birth")
    addr_f = next(f for f in findings if f.field_name == "address")

    assert name_f.status in (MatchStatus.LIKELY_MATCH, MatchStatus.VERIFICATION_REQUIRED)
    assert dob_f.status == MatchStatus.MATCH
    assert addr_f.status == MatchStatus.MATCH


def test_cross_doc_application_vs_marksheet() -> None:
    """20. Application form vs marksheet where marksheet lacks father name."""
    doc_app = ExtractedDocument(
        document_id="app_02",
        document_type=DocumentType.APPLICATION_FORM,
        name=ExtractedField(field_name="name", original="Priti Ahire", normalized="priti ahire"),
        father_name=ExtractedField(field_name="father_name", original="Shashikant", normalized="shashikant"),
    )
    doc_marksheet = ExtractedDocument(
        document_id="ms_01",
        document_type=DocumentType.MARKSHEET,
        name=ExtractedField(field_name="name", original="Priti Ahire", normalized="priti ahire"),
        father_name=None,
    )

    matcher = CrossDocumentMatcher()
    findings = matcher.match_documents([doc_app, doc_marksheet])

    name_f = next(f for f in findings if f.field_name == "name")
    father_f = next(f for f in findings if f.field_name == "father_name")

    assert name_f.status == MatchStatus.MATCH
    assert father_f.status == MatchStatus.MISSING


def test_cross_doc_application_vs_income_certificate() -> None:
    """21. Application form vs income certificate matching applicant and father name."""
    doc_app = ExtractedDocument(
        document_id="app_03",
        document_type=DocumentType.APPLICATION_FORM,
        name=ExtractedField(field_name="name", original="Priti Ahire", normalized="priti ahire"),
        father_name=ExtractedField(field_name="father_name", original="Shashikant Ahire", normalized="shashikant ahire"),
    )
    doc_income = ExtractedDocument(
        document_id="inc_01",
        document_type=DocumentType.INCOME_CERTIFICATE,
        name=ExtractedField(field_name="name", original="Priti Ahire", normalized="priti ahire"),
        father_name=ExtractedField(field_name="father_name", original="Shashikant Ahire", normalized="shashikant ahire"),
    )

    findings = compare_documents([doc_app, doc_income])
    assert all(f.status == MatchStatus.MATCH for f in findings if f.field_name in ("name", "father_name"))


def test_cross_doc_application_vs_caste_certificate() -> None:
    """22. Application form vs caste certificate matching applicant and father name."""
    doc_app = ExtractedDocument(
        document_id="app_04",
        document_type=DocumentType.APPLICATION_FORM,
        name=ExtractedField(field_name="name", original="Priti Ahire", normalized="priti ahire"),
        father_name=ExtractedField(field_name="father_name", original="Shashikant Ahire", normalized="shashikant ahire"),
    )
    doc_caste = ExtractedDocument(
        document_id="caste_01",
        document_type=DocumentType.CASTE_CERTIFICATE,
        name=ExtractedField(field_name="name", original="Priti Ahire", normalized="priti ahire"),
        father_name=ExtractedField(field_name="father_name", original="Shashikant Ahire", normalized="shashikant ahire"),
    )

    findings = compare_documents([doc_app, doc_caste])
    name_finding = next(f for f in findings if f.field_name == "name")
    assert name_finding.status == MatchStatus.MATCH


def test_cross_doc_multiple_documents() -> None:
    """23. Comparing 3 documents produces pairwise findings across all pairs."""
    docs = [
        ExtractedDocument(
            document_id="app_multi",
            document_type=DocumentType.APPLICATION_FORM,
            name=ExtractedField(field_name="name", normalized="priti ahire"),
        ),
        ExtractedDocument(
            document_id="aadhaar_multi",
            document_type=DocumentType.AADHAAR_OR_IDENTITY,
            name=ExtractedField(field_name="name", normalized="priti ahire"),
        ),
        ExtractedDocument(
            document_id="marksheet_multi",
            document_type=DocumentType.MARKSHEET,
            name=ExtractedField(field_name="name", normalized="priti ahire"),
        ),
    ]

    findings = compare_documents(docs, fields=["name"])
    # 3 documents -> 3 unique pairs: (app, aadhaar), (app, marksheet), (aadhaar, marksheet)
    assert len(findings) == 3
    assert all(f.status == MatchStatus.MATCH for f in findings)


def test_cross_doc_duplicate_prevention() -> None:
    """24. No duplicate comparisons: pairs (A, B) are generated without (B, A)."""
    docs = [
        ExtractedDocument(
            document_id="doc1",
            document_type=DocumentType.APPLICATION_FORM,
            name=ExtractedField(field_name="name", normalized="priti ahire"),
        ),
        ExtractedDocument(
            document_id="doc2",
            document_type=DocumentType.AADHAAR_OR_IDENTITY,
            name=ExtractedField(field_name="name", normalized="priti ahire"),
        ),
    ]

    findings = compare_documents(docs, fields=["name"])
    assert len(findings) == 1
    assert findings[0].source_document == "application_form"
    assert findings[0].comparison_document == "aadhaar_or_identity"


def test_cross_doc_deterministic_ordering() -> None:
    """25. Document input order permutation produces identical canonical findings."""
    doc_a = ExtractedDocument(
        document_id="doc_a",
        document_type=DocumentType.APPLICATION_FORM,
        name=ExtractedField(field_name="name", normalized="priti ahire"),
    )
    doc_b = ExtractedDocument(
        document_id="doc_b",
        document_type=DocumentType.AADHAAR_OR_IDENTITY,
        name=ExtractedField(field_name="name", normalized="priti ahire"),
    )

    findings_1 = compare_documents([doc_a, doc_b], fields=["name"])
    findings_2 = compare_documents([doc_b, doc_a], fields=["name"])

    assert len(findings_1) == len(findings_2)
    assert findings_1[0].source_document == findings_2[0].source_document
    assert findings_1[0].comparison_document == findings_2[0].comparison_document
    assert findings_1[0].status == findings_2[0].status


# ==============================================================================
# 6. FINDING ATTRIBUTES (26 - 31)
# ==============================================================================

def test_finding_correct_status() -> None:
    """26. Finding preserves correct MatchStatus enum instance."""
    finding = compare_names("priti ahire", "priti ahire")
    assert isinstance(finding.status, MatchStatus)
    assert finding.status == MatchStatus.MATCH


def test_finding_correct_similarity_score() -> None:
    """27. Finding preserves exact float similarity score."""
    finding = compare_names("priti ahire", "priti ahire")
    assert isinstance(finding.similarity_score, float)
    assert finding.similarity_score == 1.0


def test_finding_needs_verification() -> None:
    """28. needs_verification is True for uncertain matches and False for exact matches."""
    exact_f = compare_names("priti ahire", "priti ahire")
    assert exact_f.needs_verification is False

    fuzzy_f = compare_names("priti s ahire", "priti shashikant ahire")
    assert fuzzy_f.needs_verification is True


def test_finding_explanation() -> None:
    """29. Finding includes clear human-readable explanation."""
    finding = compare_names("priti ahire", "rahul patil")
    assert finding.explanation is not None
    assert len(finding.explanation) > 10
    assert "differ significantly" in finding.explanation


def test_finding_original_values_preserved() -> None:
    """30. Original unnormalized values are preserved in the finding."""
    matcher = NameMatcher()
    finding = matcher.compare(
        name_a="priti ahire",
        name_b="priti ahire",
        source_value="  PRITI AHIRE  ",
        comparison_value="Priti Ahire.",
    )
    assert finding.source_value == "  PRITI AHIRE  "
    assert finding.comparison_value == "Priti Ahire."


def test_finding_normalized_values_preserved() -> None:
    """31. Normalized values are preserved in the finding."""
    matcher = NameMatcher()
    finding = matcher.compare("priti ahire", "priti s ahire")
    assert finding.normalized_source_value == "priti ahire"
    assert finding.normalized_comparison_value == "priti s ahire"


# ==============================================================================
# 7. SAFETY CONSTRAINTS (32 - 34)
# ==============================================================================

def test_safety_no_final_decision() -> None:
    """32. Matcher does not generate READY/NOT READY or application-level decisions."""
    matcher = CrossDocumentMatcher()
    doc_a = ExtractedDocument(
        document_id="a",
        document_type=DocumentType.APPLICATION_FORM,
        name=ExtractedField(field_name="name", normalized="priti ahire"),
    )
    doc_b = ExtractedDocument(
        document_id="b",
        document_type=DocumentType.AADHAAR_OR_IDENTITY,
        name=ExtractedField(field_name="name", normalized="rahul patil"),
    )
    findings = matcher.match_documents([doc_a, doc_b])

    # Ensure findings only contain field-level statuses without decision fields
    for f in findings:
        assert f.status in MatchStatus
        assert not hasattr(f, "decision")
        assert not hasattr(f, "application_status")
        assert not hasattr(f, "risk_score")


def test_safety_no_guessing_missing_values() -> None:
    """33. Missing fields strictly remain MISSING without fabrication."""
    matcher = CrossDocumentMatcher()
    finding = matcher.compare_date(None, "2005-05-01", "app", "aadhaar")
    assert finding.status == MatchStatus.MISSING
    assert finding.similarity_score is None
    assert finding.normalized_source_value is None


def test_safety_no_initials_expansion() -> None:
    """34. Initials are not expanded or guessed as full names."""
    matcher = NameMatcher()
    finding = matcher.compare("priti s ahire", "priti shashikant ahire")
    # Finding preserves actual values without expanding "s" into "shashikant"
    assert finding.normalized_source_value == "priti s ahire"
    assert finding.normalized_comparison_value == "priti shashikant ahire"
