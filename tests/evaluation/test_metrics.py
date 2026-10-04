"""Tests for mathematical evaluation metrics."""

import pytest

from ai.schemas.comparison import MatchStatus
from ai.schemas.document import DocumentType
from evaluation.metrics import (
    _safe_divide,
    calculate_classification_metrics,
    calculate_extraction_metrics,
    calculate_instruction_metrics,
    calculate_matching_metrics,
)


def test_safe_divide() -> None:
    """Verify safe division returns default when denominator is 0."""
    assert _safe_divide(10.0, 2.0) == 5.0
    assert _safe_divide(5.0, 0.0, default=0.0) == 0.0
    assert _safe_divide(5.0, 0.0, default=1.0) == 1.0


# ==============================================================================
# CLASSIFICATION METRICS TESTS
# ==============================================================================

def test_classification_metrics_empty() -> None:
    """Verify classification metrics on empty predictions list."""
    metrics = calculate_classification_metrics([])
    assert metrics.total_cases == 0
    assert metrics.correct == 0
    assert metrics.accuracy == 0.0
    assert metrics.precision_macro == 0.0
    assert metrics.recall_macro == 0.0
    assert metrics.f1_macro == 0.0


def test_classification_metrics_perfect() -> None:
    """Verify classification metrics on 100% correct predictions."""
    preds = [
        (DocumentType.APPLICATION_FORM, DocumentType.APPLICATION_FORM),
        (DocumentType.MARKSHEET, DocumentType.MARKSHEET),
        (DocumentType.INCOME_CERTIFICATE, DocumentType.INCOME_CERTIFICATE),
    ]
    metrics = calculate_classification_metrics(preds)
    assert metrics.total_cases == 3
    assert metrics.correct == 3
    assert metrics.accuracy == 1.0
    assert metrics.precision_macro == 1.0
    assert metrics.recall_macro == 1.0
    assert metrics.f1_macro == 1.0


def test_classification_metrics_partial() -> None:
    """Verify classification metrics on partial correct predictions."""
    preds = [
        (DocumentType.APPLICATION_FORM, DocumentType.APPLICATION_FORM),  # TP for app_form
        (DocumentType.MARKSHEET, DocumentType.APPLICATION_FORM),        # FP marksheet, FN app_form
        (DocumentType.MARKSHEET, DocumentType.MARKSHEET),                # TP marksheet
    ]
    metrics = calculate_classification_metrics(preds)
    assert metrics.total_cases == 3
    assert metrics.correct == 2
    assert pytest.approx(metrics.accuracy, 0.01) == 0.6667
    assert 0.0 < metrics.precision_macro <= 1.0
    assert 0.0 < metrics.recall_macro <= 1.0
    assert 0.0 < metrics.f1_macro <= 1.0


def test_classification_metrics_all_mismatches() -> None:
    """Verify classification metrics when all predictions are incorrect."""
    preds = [
        (DocumentType.MARKSHEET, DocumentType.APPLICATION_FORM),
        (DocumentType.APPLICATION_FORM, DocumentType.MARKSHEET),
    ]
    metrics = calculate_classification_metrics(preds)
    assert metrics.total_cases == 2
    assert metrics.correct == 0
    assert metrics.accuracy == 0.0


# ==============================================================================
# MATCHING METRICS TESTS
# ==============================================================================

def test_matching_metrics_empty() -> None:
    """Verify matching metrics on empty predictions list."""
    metrics = calculate_matching_metrics([])
    assert metrics.total_cases == 0
    assert metrics.accuracy == 0.0
    assert metrics.false_matches == 0
    assert metrics.false_mismatches == 0


def test_matching_metrics_perfect() -> None:
    """Verify matching metrics on 100% correct matching pairs."""
    preds = [
        (MatchStatus.MATCH, MatchStatus.MATCH),
        (MatchStatus.MISMATCH, MatchStatus.MISMATCH),
        (MatchStatus.MISSING, MatchStatus.MISSING),
    ]
    metrics = calculate_matching_metrics(preds)
    assert metrics.total_cases == 3
    assert metrics.correct == 3
    assert metrics.accuracy == 1.0
    assert metrics.false_matches == 0
    assert metrics.false_mismatches == 0


def test_matching_metrics_false_positive_and_negative() -> None:
    """Verify tracking of high-risk false matches (FP) and false mismatches (FN)."""
    preds = [
        # Predicted MATCH when expected MISMATCH -> False match (dangerous!)
        (MatchStatus.MATCH, MatchStatus.MISMATCH),
        # Predicted LIKELY_MATCH when expected MISMATCH -> False match
        (MatchStatus.LIKELY_MATCH, MatchStatus.MISMATCH),
        # Predicted MISMATCH when expected MATCH -> False mismatch
        (MatchStatus.MISMATCH, MatchStatus.MATCH),
        # Correct MATCH
        (MatchStatus.MATCH, MatchStatus.MATCH),
    ]
    metrics = calculate_matching_metrics(preds)
    assert metrics.total_cases == 4
    assert metrics.correct == 1
    assert metrics.accuracy == 0.25
    assert metrics.false_matches == 2
    assert metrics.false_mismatches == 1


# ==============================================================================
# INSTRUCTION METRICS TESTS
# ==============================================================================

def test_instruction_metrics_empty() -> None:
    """Verify instruction metrics on empty input."""
    metrics = calculate_instruction_metrics([])
    assert metrics.total_cases == 0
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0


def test_instruction_metrics_perfect() -> None:
    """Verify instruction metrics on complete alignment."""
    preds = [
        (["required_document", "file_format"], ["required_document", "file_format"]),
        (["file_size"], ["file_size"]),
    ]
    metrics = calculate_instruction_metrics(preds)
    assert metrics.total_cases == 2
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0


def test_instruction_metrics_partial() -> None:
    """Verify instruction metrics with extraneous and missed requirements."""
    preds = [
        (["required_document", "extraneous"], ["required_document", "file_format"]),
    ]
    # TP: 1 (required_document), FP: 1 (extraneous), FN: 1 (file_format)
    # Precision: 1/2 = 0.5, Recall: 1/2 = 0.5, F1 = 0.5
    metrics = calculate_instruction_metrics(preds)
    assert metrics.total_cases == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5


# ==============================================================================
# EXTRACTION METRICS TESTS
# ==============================================================================

def test_extraction_metrics_empty() -> None:
    """Verify extraction metrics on empty field list."""
    metrics = calculate_extraction_metrics([])
    assert metrics.total_fields == 0
    assert metrics.exact_match_rate == 0.0
    assert metrics.normalized_match_rate == 0.0
    assert metrics.missing_fields == 0


def test_extraction_metrics_exact_and_normalized() -> None:
    """Verify exact matching vs normalization benefit."""
    preds = [
        # (pred_original, pred_normalized, expected_val)
        ("Priti Ahire", "priti ahire", "priti ahire"),        # exact match (case insensitive) and norm match
        ("15/08/2004", "2004-08-15", "2004-08-15"),          # normalized match only
        (None, None, "Mandatory Field"),                     # missing field
        (None, None, None),                                  # correctly absent field
    ]
    metrics = calculate_extraction_metrics(preds)
    assert metrics.total_fields == 4
    assert metrics.missing_fields == 1
    assert metrics.normalized_matches == 3
