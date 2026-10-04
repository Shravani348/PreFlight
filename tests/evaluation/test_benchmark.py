"""Tests for benchmark runner execution and fixture loading."""

import json
from pathlib import Path
import pytest

from evaluation.benchmark import (
    run_all_benchmarks,
    run_classification_benchmark,
    run_extraction_benchmark,
    run_instruction_benchmark,
    run_matching_benchmark,
)
from evaluation.fixtures.dataset import (
    CLASSIFICATION_CASES,
    EXTRACTION_CASES,
    INSTRUCTION_CASES,
    MATCHING_CASES,
)
from evaluation.schemas import (
    BenchmarkReport,
    ClassificationTestCase,
    FieldExtractionTestCase,
    InstructionTestCase,
    MatchingTestCase,
)


def test_fixture_dataset_counts() -> None:
    """Verify synthetic dataset fixture case counts satisfy requirements."""
    assert len(CLASSIFICATION_CASES) >= 10
    assert len(MATCHING_CASES) >= 10
    assert len(INSTRUCTION_CASES) >= 5
    assert len(EXTRACTION_CASES) >= 4


def test_classification_benchmark_execution() -> None:
    """Verify classification benchmark executes and computes non-empty metrics."""
    metrics = run_classification_benchmark()
    assert metrics.total_cases == len(CLASSIFICATION_CASES)
    assert 0.0 <= metrics.accuracy <= 1.0
    assert 0.0 <= metrics.precision_macro <= 1.0
    assert 0.0 <= metrics.recall_macro <= 1.0
    assert 0.0 <= metrics.f1_macro <= 1.0
    assert metrics.correct > 0


def test_matching_benchmark_execution() -> None:
    """Verify matching benchmark executes and tracks error cases."""
    metrics = run_matching_benchmark()
    assert metrics.total_cases == len(MATCHING_CASES)
    assert 0.0 <= metrics.accuracy <= 1.0
    assert metrics.false_matches >= 0
    assert metrics.false_mismatches >= 0
    assert metrics.correct > 0


def test_instruction_benchmark_execution() -> None:
    """Verify instruction extraction benchmark executes."""
    metrics = run_instruction_benchmark()
    assert metrics.total_cases == len(INSTRUCTION_CASES)
    assert 0.0 <= metrics.precision <= 1.0
    assert 0.0 <= metrics.recall <= 1.0
    assert 0.0 <= metrics.f1 <= 1.0


def test_extraction_benchmark_execution() -> None:
    """Verify field extraction and normalization benchmark executes."""
    metrics = run_extraction_benchmark()
    assert metrics.total_fields > 0
    assert 0.0 <= metrics.exact_match_rate <= 1.0
    assert 0.0 <= metrics.normalized_match_rate <= 1.0
    # Normalization should yield greater or equal match rate than raw exact match
    assert metrics.normalized_match_rate >= metrics.exact_match_rate


def test_benchmark_determinism() -> None:
    """Verify benchmark produces identical results across consecutive runs."""
    report_1 = run_all_benchmarks()
    report_2 = run_all_benchmarks()

    assert report_1.classification is not None and report_2.classification is not None
    assert report_1.classification.accuracy == report_2.classification.accuracy
    assert report_1.classification.f1_macro == report_2.classification.f1_macro

    assert report_1.matching is not None and report_2.matching is not None
    assert report_1.matching.accuracy == report_2.matching.accuracy
    assert report_1.matching.false_matches == report_2.matching.false_matches

    assert report_1.instructions is not None and report_2.instructions is not None
    assert report_1.instructions.f1 == report_2.instructions.f1

    assert report_1.extraction is not None and report_2.extraction is not None
    assert report_1.extraction.normalized_match_rate == report_2.extraction.normalized_match_rate


def test_json_fixtures_validity() -> None:
    """Verify that all exported JSON fixtures are valid and match Pydantic schemas."""
    base_dir = Path("evaluation/fixtures")

    # 1. Classification JSON fixtures
    class_files = list((base_dir / "classification").glob("*.json"))
    assert len(class_files) >= 10
    for cf in class_files:
        with open(cf, "r", encoding="utf-8") as f:
            data = json.load(f)
            case = ClassificationTestCase.model_validate(data)
            assert case.case_id

    # 2. Matching JSON fixtures
    match_files = list((base_dir / "matching").glob("*.json"))
    assert len(match_files) >= 10
    for mf in match_files:
        with open(mf, "r", encoding="utf-8") as f:
            data = json.load(f)
            case = MatchingTestCase.model_validate(data)
            assert case.case_id

    # 3. Instruction JSON fixtures
    inst_files = list((base_dir / "instructions").glob("*.json"))
    assert len(inst_files) >= 5
    for inf in inst_files:
        with open(inf, "r", encoding="utf-8") as f:
            data = json.load(f)
            case = InstructionTestCase.model_validate(data)
            assert case.case_id

    # 4. Extraction JSON fixtures
    ext_files = list((base_dir / "extraction").glob("*.json"))
    assert len(ext_files) >= 4
    for ef in ext_files:
        with open(ef, "r", encoding="utf-8") as f:
            data = json.load(f)
            case = FieldExtractionTestCase.model_validate(data)
            assert case.case_id
