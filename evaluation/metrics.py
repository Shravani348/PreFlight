"""Mathematical metric calculators for document classification, matching, and extraction."""

from typing import Dict, List, Optional, Set, Tuple

from ai.schemas.comparison import MatchStatus
from ai.schemas.document import DocumentType
from evaluation.schemas import (
    ClassificationMetrics,
    ExtractionMetrics,
    InstructionMetrics,
    MatchingMetrics,
)


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0.0:
        return default
    return numerator / denominator


def calculate_classification_metrics(
    predictions: List[Tuple[DocumentType, DocumentType]],
) -> ClassificationMetrics:
    """Calculate multiclass classification accuracy, macro-precision, recall, and F1.

    Args:
        predictions: List of tuples where each element is (predicted_type, expected_type).

    Returns:
        ClassificationMetrics containing aggregate and per-class metrics.
    """
    total = len(predictions)
    if total == 0:
        return ClassificationMetrics(
            total_cases=0,
            correct=0,
            accuracy=0.0,
            precision_macro=0.0,
            recall_macro=0.0,
            f1_macro=0.0,
            per_class_metrics={},
        )

    correct_count = sum(1 for pred, exp in predictions if pred == exp)
    accuracy = round(_safe_divide(correct_count, total), 4)

    # Collect unique classes present in either expected or predicted
    all_classes: Set[DocumentType] = set()
    for pred, exp in predictions:
        all_classes.add(pred)
        all_classes.add(exp)

    per_class: Dict[str, Dict[str, float]] = {}
    precisions: List[float] = []
    recalls: List[float] = []
    f1s: List[float] = []

    for cls in sorted(all_classes, key=lambda c: c.value):
        cls_key = cls.value
        tp = sum(1 for pred, exp in predictions if pred == cls and exp == cls)
        fp = sum(1 for pred, exp in predictions if pred == cls and exp != cls)
        fn = sum(1 for pred, exp in predictions if pred != cls and exp == cls)

        p = round(_safe_divide(tp, tp + fp), 4)
        r = round(_safe_divide(tp, tp + fn), 4)
        f1 = round(_safe_divide(2 * p * r, p + r), 4)

        per_class[cls_key] = {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}
        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)

    macro_p = round(_safe_divide(sum(precisions), len(precisions)), 4) if precisions else 0.0
    macro_r = round(_safe_divide(sum(recalls), len(recalls)), 4) if recalls else 0.0
    macro_f1 = round(_safe_divide(sum(f1s), len(f1s)), 4) if f1s else 0.0

    return ClassificationMetrics(
        total_cases=total,
        correct=correct_count,
        accuracy=accuracy,
        precision_macro=macro_p,
        recall_macro=macro_r,
        f1_macro=macro_f1,
        per_class_metrics=per_class,
    )


def calculate_matching_metrics(
    predictions: List[Tuple[MatchStatus, MatchStatus]],
) -> MatchingMetrics:
    """Calculate accuracy, macro-F1, false matches, and false mismatches for matching outcomes.

    Args:
        predictions: List of tuples where each element is (predicted_status, expected_status).

    Returns:
        MatchingMetrics: Aggregated matching performance metrics.
    """
    total = len(predictions)
    if total == 0:
        return MatchingMetrics(
            total_cases=0,
            correct=0,
            accuracy=0.0,
            precision_macro=0.0,
            recall_macro=0.0,
            f1_macro=0.0,
            false_matches=0,
            false_mismatches=0,
        )

    correct_count = sum(1 for pred, exp in predictions if pred == exp)
    accuracy = round(_safe_divide(correct_count, total), 4)

    # Specific matching safety counts
    # False match: predicted match/likely_match when expected was mismatch
    positive_statuses = {MatchStatus.MATCH, MatchStatus.LIKELY_MATCH}
    false_matches = sum(
        1 for pred, exp in predictions
        if pred in positive_statuses and exp == MatchStatus.MISMATCH
    )
    # False mismatch: predicted mismatch when expected was match/likely_match
    false_mismatches = sum(
        1 for pred, exp in predictions
        if pred == MatchStatus.MISMATCH and exp in positive_statuses
    )

    all_statuses: Set[MatchStatus] = set()
    for pred, exp in predictions:
        all_statuses.add(pred)
        all_statuses.add(exp)

    precisions: List[float] = []
    recalls: List[float] = []
    f1s: List[float] = []

    for status in sorted(all_statuses, key=lambda s: s.value):
        tp = sum(1 for pred, exp in predictions if pred == status and exp == status)
        fp = sum(1 for pred, exp in predictions if pred == status and exp != status)
        fn = sum(1 for pred, exp in predictions if pred != status and exp == status)

        p = round(_safe_divide(tp, tp + fp), 4)
        r = round(_safe_divide(tp, tp + fn), 4)
        f1 = round(_safe_divide(2 * p * r, p + r), 4)

        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)

    macro_p = round(_safe_divide(sum(precisions), len(precisions)), 4) if precisions else 0.0
    macro_r = round(_safe_divide(sum(recalls), len(recalls)), 4) if recalls else 0.0
    macro_f1 = round(_safe_divide(sum(f1s), len(f1s)), 4) if f1s else 0.0

    return MatchingMetrics(
        total_cases=total,
        correct=correct_count,
        accuracy=accuracy,
        precision_macro=macro_p,
        recall_macro=macro_r,
        f1_macro=macro_f1,
        false_matches=false_matches,
        false_mismatches=false_mismatches,
    )


def calculate_instruction_metrics(
    predictions: List[Tuple[List[str], List[str]]],
) -> InstructionMetrics:
    """Calculate precision, recall, and F1 for extracted instruction requirements.

    Args:
        predictions: List of tuples where each element is (predicted_req_types, expected_req_types).

    Returns:
        InstructionMetrics: Aggregate precision, recall, and F1.
    """
    total = len(predictions)
    if total == 0:
        return InstructionMetrics(total_cases=0, precision=0.0, recall=0.0, f1=0.0)

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for pred_list, exp_list in predictions:
        pred_set = set(pred_list)
        exp_set = set(exp_list)

        tp = len(pred_set.intersection(exp_set))
        fp = len(pred_set.difference(exp_set))
        fn = len(exp_set.difference(pred_set))

        total_tp += tp
        total_fp += fp
        total_fn += fn

    p = round(_safe_divide(total_tp, total_tp + total_fp, default=1.0 if total_tp == 0 and total_fp == 0 else 0.0), 4)
    r = round(_safe_divide(total_tp, total_tp + total_fn, default=1.0 if total_tp == 0 and total_fn == 0 else 0.0), 4)
    f1 = round(_safe_divide(2 * p * r, p + r), 4)

    return InstructionMetrics(
        total_cases=total,
        precision=p,
        recall=r,
        f1=f1,
    )


def calculate_extraction_metrics(
    predictions: List[Tuple[Optional[str], Optional[str], Optional[str]]],
) -> ExtractionMetrics:
    """Calculate exact match, normalized match, and missing field rates for field extraction.

    Args:
        predictions: List of tuples (predicted_original, predicted_normalized, expected_value).

    Returns:
        ExtractionMetrics: Aggregate extraction match rates.
    """
    total = len(predictions)
    if total == 0:
        return ExtractionMetrics(
            total_fields=0,
            exact_matches=0,
            normalized_matches=0,
            missing_fields=0,
            exact_match_rate=0.0,
            normalized_match_rate=0.0,
        )

    exact = 0
    normalized = 0
    missing = 0

    for pred_orig, pred_norm, exp_val in predictions:
        if exp_val is None:
            if pred_orig is None:
                exact += 1
                normalized += 1
            continue

        if pred_orig is None:
            missing += 1
            continue

        if str(pred_orig).strip().lower() == str(exp_val).strip().lower():
            exact += 1

        if pred_norm is not None and str(pred_norm).strip().lower() == str(exp_val).strip().lower():
            normalized += 1
        elif str(pred_orig).strip().lower() == str(exp_val).strip().lower():
            normalized += 1

    return ExtractionMetrics(
        total_fields=total,
        exact_matches=exact,
        normalized_matches=normalized,
        missing_fields=missing,
        exact_match_rate=round(_safe_divide(exact, total), 4),
        normalized_match_rate=round(_safe_divide(normalized, total), 4),
    )
