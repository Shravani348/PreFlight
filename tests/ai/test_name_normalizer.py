"""Unit and regression tests for NameNormalizer focusing on Indic Unicode preservation."""

import unicodedata
import pytest

from ai.normalization.name_normalizer import NameNormalizer, normalize_name


# ==============================================================================
# 1. INDIC UNICODE PRESERVATION TESTS
# ==============================================================================

def test_indic_names_preserve_combining_marks_and_vowel_signs() -> None:
    """Verify that Devanagari vowel signs (matras), viramas, and conjuncts are intact."""
    normalizer = NameNormalizer()

    # Vowel sign AA (ा), II (ी)
    assert normalizer.normalize("पाटील") == "पाटील"
    assert normalizer.normalize("पाटिल") == "पाटिल"

    # Virama / Halant (्) in conjunct 'प्र' and vowel sign II (ी)
    assert normalizer.normalize("प्रीती") == "प्रीती"

    # Multi-token Devanagari names
    assert normalizer.normalize("शशिकांत अहिरे") == "शशिकांत अहिरे"
    assert normalizer.normalize("अमित पाटील") == "अमित पाटील"
    assert normalizer.normalize("स्नेहा देशमुख") == "स्नेहा देशमुख"

    # Compound conjunct words
    assert normalizer.normalize("गुणपत्रिका") == "गुणपत्रिका"
    assert normalizer.normalize("उत्पन्न") == "उत्पन्न"


def test_indic_canonical_unicode_equivalence() -> None:
    """Verify that canonically equivalent Unicode forms (NFD vs NFC) normalize identically."""
    normalizer = NameNormalizer()

    # Marathi name with Devanagari letter containing canonical Nukta decomposition (e.g. ऱ \u0931 -> र \u0930 + ़ \u093c)
    sample = "बा\u0931ू पाटील"
    decomposed_nfd = unicodedata.normalize("NFD", sample)
    composed_nfc = unicodedata.normalize("NFC", sample)

    # In raw form, NFD and NFC have different byte lengths and code points
    assert decomposed_nfd != composed_nfc

    # Both must normalize to identical canonical representation
    norm_nfd = normalizer.normalize(decomposed_nfd)
    norm_nfc = normalizer.normalize(composed_nfc)

    assert norm_nfd == norm_nfc
    assert norm_nfd == "बाऱू पाटील"



def test_indic_whitespace_normalization() -> None:
    """Verify leading, trailing, and internal irregular whitespace normalization with Devanagari."""
    normalizer = NameNormalizer()

    raw = "  प्रीती   अहिरे  "
    assert normalizer.normalize(raw) == "प्रीती अहिरे"

    tab_newline = "अमित \t\n  पाटील"
    assert normalizer.normalize(tab_newline) == "अमित पाटील"


def test_indic_punctuation_handling() -> None:
    """Verify punctuation around Devanagari names is stripped without damaging Indic letters/marks."""
    normalizer = NameNormalizer()

    assert normalizer.normalize("प्रीती, अहिरे.") == "प्रीती अहिरे"
    assert normalizer.normalize("पाटील / अमित") == "पाटील अमित"
    assert normalizer.normalize("स्नेहा_देशमुख") == "स्नेहा देशमुख"
    assert normalizer.normalize("-शशिकांत अहिरे-") == "शशिकांत अहिरे"


def test_mixed_script_preservation() -> None:
    """Verify mixed Latin and Devanagari scripts survive normalization without corruption."""
    normalizer = NameNormalizer()

    raw = "Priti प्रीती Ahire अहिरे"
    expected = "priti प्रीती ahire अहिरे"
    assert normalizer.normalize(raw) == expected


# ==============================================================================
# 2. ENGLISH AND GENERAL REGRESSION TESTS
# ==============================================================================

def test_english_baseline_preservation() -> None:
    """Verify that all existing English normalization behaviors remain intact."""
    normalizer = NameNormalizer()

    assert normalizer.normalize("Priti Shashikant Ahire") == "priti shashikant ahire"
    assert normalizer.normalize("PRITI SHASHIKANT AHIRE") == "priti shashikant ahire"
    assert normalizer.normalize("   Priti Ahire   ") == "priti ahire"
    assert normalizer.normalize("Priti    Shashikant    Ahire") == "priti shashikant ahire"
    assert normalizer.normalize("Priti, Ahire.") == "priti ahire"
    assert normalizer.normalize("Ahire / Priti") == "ahire priti"
    assert normalizer.normalize("Priti_Ahire") == "priti ahire"
    assert normalizer.normalize("Priti-Shashikant Ahire") == "priti shashikant ahire"
    assert normalizer.normalize("Priti S. Ahire") == "priti s ahire"
    assert normalizer.normalize("S. K. Sharma") == "s k sharma"


def test_empty_and_punctuation_only_inputs() -> None:
    """Verify None/empty/punctuation-only contracts."""
    normalizer = NameNormalizer()

    assert normalizer.normalize(None) is None
    assert normalizer.normalize("") is None
    assert normalizer.normalize("   ") is None
    assert normalizer.normalize("... --- ,,,") is None
    assert normalizer.normalize("-") is None
    assert normalizer.normalize("   .   ") is None


def test_helper_function() -> None:
    """Verify normalize_name module-level helper function."""
    assert normalize_name("प्रीती अहिरे") == "प्रीती अहिरे"
    assert normalize_name("Priti Ahire") == "priti ahire"
    assert normalize_name(None) is None
