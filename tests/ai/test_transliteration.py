"""Unit tests for deterministic Devanagari to Latin transliteration helper."""

import pytest
from ai.matching.transliteration import (
    is_cross_script,
    is_devanagari,
    is_latin,
    transliterate_devanagari_to_latin,
)


def test_transliteration_minimum_required_names() -> None:
    """Verify minimum required test names from specification."""
    assert transliterate_devanagari_to_latin("प्रीती") == "priti"
    assert transliterate_devanagari_to_latin("प्रीति") == "priti"
    assert transliterate_devanagari_to_latin("अमित") == "amit"
    assert transliterate_devanagari_to_latin("अहिरे") == "ahire"
    assert transliterate_devanagari_to_latin("शशिकांत") == "shashikant"
    assert transliterate_devanagari_to_latin("पाटील") == "patil"


def test_transliteration_common_hindi_marathi_names() -> None:
    """Verify common Hindi and Marathi personal name transliterations."""
    assert transliterate_devanagari_to_latin("सुरेश") == "suresh"
    assert transliterate_devanagari_to_latin("राहुल") == "rahul"
    assert transliterate_devanagari_to_latin("पूजा") == "puja"
    assert transliterate_devanagari_to_latin("स्नेहा") == "sneha"
    assert transliterate_devanagari_to_latin("देशमुख") == "deshmukh"
    assert transliterate_devanagari_to_latin("पवार") == "pawar"
    assert transliterate_devanagari_to_latin("संजय") == "sanjay"
    assert transliterate_devanagari_to_latin("अंबर") == "ambar"


def test_transliteration_determinism() -> None:
    """Output must be strictly deterministic across repeated calls."""
    name = "प्रीती शशिकांत अहिरे"
    first = transliterate_devanagari_to_latin(name)
    for _ in range(10):
        assert transliterate_devanagari_to_latin(name) == first


def test_transliteration_empty_and_whitespace_safety() -> None:
    """Empty, None, or whitespace-only inputs return safe string."""
    assert transliterate_devanagari_to_latin("") == ""
    assert transliterate_devanagari_to_latin(None) == ""
    assert transliterate_devanagari_to_latin("   ") == ""


def test_transliteration_latin_passthrough() -> None:
    """Latin strings pass through completely unchanged without corruption."""
    assert transliterate_devanagari_to_latin("Priti Ahire") == "Priti Ahire"
    assert transliterate_devanagari_to_latin("Amit Patil") == "Amit Patil"
    assert transliterate_devanagari_to_latin("priti ahire") == "priti ahire"


def test_transliteration_unsupported_characters_safe() -> None:
    """Unsupported characters, punctuation, digits, or other scripts do not crash."""
    assert transliterate_devanagari_to_latin("12345") == "12345"
    assert transliterate_devanagari_to_latin("Hello! 123") == "Hello! 123"
    assert transliterate_devanagari_to_latin("अमित (Patil)") == "amit (Patil)"
    assert transliterate_devanagari_to_latin("测试") == "测试"


def test_script_detection_helpers() -> None:
    """Verify is_devanagari, is_latin, and is_cross_script heuristics."""
    assert is_devanagari("प्रीती अहिरे") is True
    assert is_devanagari("Priti Ahire") is False
    assert is_devanagari("") is False

    assert is_latin("Priti Ahire") is True
    assert is_latin("प्रीती अहिरे") is False
    assert is_latin("") is False

    # Cross script
    assert is_cross_script("Priti Ahire", "प्रीती अहिरे") is True
    assert is_cross_script("प्रीती अहिरे", "Priti Ahire") is True
    assert is_cross_script("Amit Patil", "अमित पाटील") is True

    # Same script
    assert is_cross_script("Priti Ahire", "Priti Ahire") is False
    assert is_cross_script("अमित पाटील", "अमित पाटील") is False
    assert is_cross_script("", "Priti Ahire") is False
