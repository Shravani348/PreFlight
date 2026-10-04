"""Tests for prompt security, untrusted data handling, and prompt-injection defense."""

import pytest
from ai.extraction.prompts import (
    SYSTEM_EXTRACTION_PROMPT,
    get_extraction_prompt,
)
from ai.schemas.document import DocumentType


def test_system_prompt_untrusted_data_directive() -> None:
    """System extraction prompt must explicitly designate document content as untrusted data."""
    lowered = SYSTEM_EXTRACTION_PROMPT.lower()
    assert "untrusted" in lowered
    assert "data" in lowered


def test_system_prompt_instruction_override_defense() -> None:
    """System prompt must instruct model never to follow instructions embedded in documents."""
    lowered = SYSTEM_EXTRACTION_PROMPT.lower()
    has_instruction_defense = (
        ("never follow" in lowered or "do not follow" in lowered)
        and ("instructions" in lowered or "commands" in lowered or "directives" in lowered)
    )
    assert has_instruction_defense
    assert "ignore prompt injection" in lowered or "prompt injection" in lowered


def test_system_prompt_extract_only_requested_fields() -> None:
    """Prompt must restrict model to extracting only requested fields without executing actions."""
    lowered = SYSTEM_EXTRACTION_PROMPT.lower()
    assert "extract only" in lowered
    assert "requested fields" in lowered


def test_system_prompt_no_hallucination_null() -> None:
    """Prompt must require null for missing data and forbid ungrounded inferences."""
    lowered = SYSTEM_EXTRACTION_PROMPT.lower()
    assert "null" in lowered
    assert "never infer" in lowered or "do not infer" in lowered


def test_get_extraction_prompt_includes_safety_header_for_all_types() -> None:
    """Every document-specific prompt must inherit the untrusted data & security directives."""
    for doc_type in DocumentType:
        prompt = get_extraction_prompt(doc_type)
        lowered = prompt.lower()
        assert "untrusted data" in lowered, f"DocumentType {doc_type} missing untrusted data directive"
        assert "null" in lowered, f"DocumentType {doc_type} missing null directive"
        assert "requested fields" in lowered or "fields to extract" in lowered


def test_get_extraction_prompt_preserves_specific_fields() -> None:
    """Specialized extraction prompts maintain their target scholarship field schemas."""
    app_prompt = get_extraction_prompt(DocumentType.APPLICATION_FORM)
    assert "name" in app_prompt
    assert "date_of_birth" in app_prompt

    marksheet_prompt = get_extraction_prompt(DocumentType.MARKSHEET)
    assert "marks" in marksheet_prompt
    assert "percentage" in marksheet_prompt

    income_prompt = get_extraction_prompt(DocumentType.INCOME_CERTIFICATE)
    assert "certificate_number" in income_prompt
    assert "annual_income" in income_prompt
