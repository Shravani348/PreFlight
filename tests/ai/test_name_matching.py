"""Regression and unit tests for hardened NameMatcher."""

import pytest

from ai.matching.name_matcher import NameMatcher, compare_names
from ai.schemas.comparison import MatchStatus


def test_name_exact_match() -> None:
    """Exact identical name strings produce MATCH with score 1.0."""
    matcher = NameMatcher()
    finding = matcher.compare("Priti Shashikant Ahire", "Priti Shashikant Ahire")
    assert finding.status == MatchStatus.MATCH
    assert finding.similarity_score == 1.0
    assert finding.needs_verification is False


def test_name_formatting_variation() -> None:
    """Formatting variations (punctuation and whitespace) produce MATCH after normalization."""
    matcher = NameMatcher()
    finding = matcher.compare("Priti S. Ahire", "Priti S Ahire")
    assert finding.status == MatchStatus.MATCH
    assert finding.similarity_score == 1.0
    assert finding.needs_verification is False


def test_name_family_member_subset_critical_vulnerability() -> None:
    """CRITICAL SAFETY REGRESSION: Shorter family-member name must NEVER be MATCH or LIKELY_MATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("Shashikant Ahire", "Priti Shashikant Ahire")

    # MUST NOT be MATCH or LIKELY_MATCH
    assert finding.status not in (MatchStatus.MATCH, MatchStatus.LIKELY_MATCH)
    assert finding.status == MatchStatus.VERIFICATION_REQUIRED
    assert finding.needs_verification is True

    # Similarity score must not be falsely reported as perfect 1.0
    assert finding.similarity_score is not None
    assert finding.similarity_score < 1.0
    assert "subset" in finding.explanation.lower()
    assert "family-member" in finding.explanation.lower()


def test_name_different_individuals() -> None:
    """Completely different names produce MISMATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("Priti Shashikant Ahire", "Rahul Vijay Patil")
    assert finding.status == MatchStatus.MISMATCH
    assert finding.similarity_score is not None
    assert finding.similarity_score < 0.75
    assert finding.needs_verification is False


def test_name_similar_spelling_variation() -> None:
    """Minor regional spelling/transliteration variations produce LIKELY_MATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("Pooja Suresh Patil", "Pooja Suresh Patle")
    assert finding.status == MatchStatus.LIKELY_MATCH
    assert finding.similarity_score is not None
    assert finding.similarity_score >= 0.90
    assert finding.needs_verification is True


def test_name_other_subset_cases_generic_family() -> None:
    """Generic subset names (patronymic or generational confusion) require verification."""
    matcher = NameMatcher()

    # Case 1: Father/Son confusion
    f1 = matcher.compare("Rahul Patil", "Amit Rahul Patil")
    assert f1.status == MatchStatus.VERIFICATION_REQUIRED
    assert f1.similarity_score is not None
    assert f1.similarity_score < 1.0
    assert f1.needs_verification is True

    # Case 2: Mother/Daughter confusion
    f2 = matcher.compare("Anita Sharma", "Sunita Anita Sharma")
    assert f2.status == MatchStatus.VERIFICATION_REQUIRED
    assert f2.similarity_score is not None
    assert f2.similarity_score < 1.0
    assert f2.needs_verification is True


def test_name_initials_preservation() -> None:
    """Initials align with full names without generating false mismatches."""
    matcher = NameMatcher()

    # Middle initial
    f1 = matcher.compare("Priti S. Ahire", "Priti Shashikant Ahire")
    assert f1.status in (MatchStatus.LIKELY_MATCH, MatchStatus.VERIFICATION_REQUIRED)
    assert f1.similarity_score is not None
    assert f1.similarity_score >= 0.75
    assert f1.needs_verification is True

    # Multi-token initials (First + Middle initials)
    f2 = matcher.compare("P. S. Ahire", "Priti Shashikant Ahire")
    assert f2.status == MatchStatus.VERIFICATION_REQUIRED
    assert f2.similarity_score is not None
    assert f2.similarity_score >= 0.75
    assert f2.needs_verification is True


def test_name_honorific_stripping() -> None:
    """Titles and honorifics (Ms., Shri, etc.) do not prevent exact matches."""
    matcher = NameMatcher()
    f1 = matcher.compare("Ms. Priti S. Ahire", "Priti S. Ahire")
    assert f1.status == MatchStatus.MATCH
    assert f1.similarity_score == 1.0

    f2 = matcher.compare("Shri Shashikant Ahire", "Shashikant Ahire")
    assert f2.status == MatchStatus.MATCH
    assert f2.similarity_score == 1.0


def test_name_token_reordering() -> None:
    """Surname-first reordering produces exact MATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("Ahire Priti Shashikant", "Priti Shashikant Ahire")
    assert finding.status == MatchStatus.MATCH
    assert finding.similarity_score == 1.0
    assert finding.needs_verification is False


def test_name_single_token_vs_full_name() -> None:
    """Single surname token against a full 3-token name produces MISMATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("Ahire", "Priti Shashikant Ahire")
    assert finding.status == MatchStatus.MISMATCH
    assert finding.needs_verification is False


def test_devanagari_exact_match() -> None:
    """Exact identical Devanagari names produce MATCH with score 1.0."""
    matcher = NameMatcher()
    finding = matcher.compare("अमित पाटील", "अमित पाटील")
    assert finding.status == MatchStatus.MATCH
    assert finding.similarity_score == 1.0
    assert finding.needs_verification is False


def test_devanagari_spelling_variation() -> None:
    """Devanagari spelling variations (e.g. पाटील vs पाटिल) require human verification."""
    matcher = NameMatcher()
    finding = matcher.compare("अमित पाटील", "अमित पाटिल")
    # Must not be an unverified false match; should require verification
    assert finding.status != MatchStatus.MISMATCH
    assert finding.status in (MatchStatus.LIKELY_MATCH, MatchStatus.VERIFICATION_REQUIRED)
    assert finding.needs_verification is True
    assert finding.similarity_score is not None
    assert finding.similarity_score >= 0.75


def test_devanagari_family_member_subset_safety() -> None:
    """CRITICAL SAFETY: Father vs applicant Devanagari name must NEVER be MATCH or LIKELY_MATCH."""
    matcher = NameMatcher()
    finding = matcher.compare("शशिकांत अहिरे", "प्रीती शशिकांत अहिरे")

    # MUST NOT be MATCH or LIKELY_MATCH
    assert finding.status not in (MatchStatus.MATCH, MatchStatus.LIKELY_MATCH)
    assert finding.status == MatchStatus.VERIFICATION_REQUIRED
    assert finding.needs_verification is True
    assert finding.similarity_score is not None
    assert finding.similarity_score < 1.0
    assert "subset" in finding.explanation.lower()
