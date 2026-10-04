"""Comprehensive unit tests for scholarship document normalization layer."""

import pytest
from ai.normalization import (
    DateNormalizer,
    DocumentNormalizer,
    NameNormalizer,
    TextNormalizer,
    normalize_date,
    normalize_extracted_document,
    normalize_name,
    normalize_text,
)
from ai.schemas.document import DocumentType, Evidence
from ai.schemas.extraction import ExtractedDocument, ExtractedField


# ==============================================================================
# 1. NAME NORMALIZATION TESTS (1 - 10)
# ==============================================================================

def test_name_normal() -> None:
    """1. Normal name normalization to lowercase single-spaced form."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("Priti Shashikant Ahire") == "priti shashikant ahire"
    assert normalize_name("Rahul Ramesh Sharma") == "rahul ramesh sharma"


def test_name_uppercase() -> None:
    """2. Uppercase name normalization."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("PRITI SHASHIKANT AHIRE") == "priti shashikant ahire"


def test_name_leading_trailing_whitespace() -> None:
    """3. Stripping leading and trailing whitespace."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("   Priti Ahire   ") == "priti ahire"


def test_name_repeated_whitespace() -> None:
    """4. Collapsing repeated internal whitespace characters."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("Priti    Shashikant    Ahire") == "priti shashikant ahire"
    assert normalizer.normalize("Priti \t\n  Ahire") == "priti ahire"


def test_name_punctuation() -> None:
    """5. Common punctuation and separator normalization."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("Priti, Ahire.") == "priti ahire"
    assert normalizer.normalize("Ahire / Priti") == "ahire priti"
    assert normalizer.normalize("Priti_Ahire") == "priti ahire"


def test_name_hyphenated() -> None:
    """6. Hyphenated names converted to separate tokens."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("Priti-Shashikant Ahire") == "priti shashikant ahire"


def test_name_initials() -> None:
    """7. Initials preserved without expansion or guessing."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("Priti S. Ahire") == "priti s ahire"
    assert normalizer.normalize("S. K. Sharma") == "s k sharma"


def test_name_empty_string() -> None:
    """8. Empty and whitespace-only strings return None."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("") is None
    assert normalizer.normalize("   ") is None


def test_name_none() -> None:
    """9. None input safely returns None."""
    normalizer = NameNormalizer()
    assert normalizer.normalize(None) is None


def test_name_punctuation_only() -> None:
    """10. Punctuation-only input returns None."""
    normalizer = NameNormalizer()
    assert normalizer.normalize("... --- ,,,") is None
    assert normalizer.normalize("   .   ") is None
    assert normalizer.normalize("-") is None


# ==============================================================================
# 2. DATE NORMALIZATION TESTS (11 - 19)
# ==============================================================================

def test_date_iso() -> None:
    """11. ISO date format normalization."""
    normalizer = DateNormalizer()
    assert normalizer.normalize("2005-05-01") == "2005-05-01"
    assert normalizer.normalize("2005/05/01") == "2005-05-01"
    assert normalizer.normalize("2005.05.01") == "2005-05-01"


def test_date_dd_mm_yyyy() -> None:
    """12. DD/MM/YYYY numeric date normalization."""
    normalizer = DateNormalizer(dayfirst=True)
    assert normalizer.normalize("01/05/2005") == "2005-05-01"
    assert normalizer.normalize("25/12/2005") == "2005-12-25"


def test_date_dd_dash_mm_dash_yyyy() -> None:
    """13. DD-MM-YYYY numeric date normalization."""
    normalizer = DateNormalizer(dayfirst=True)
    assert normalizer.normalize("01-05-2005") == "2005-05-01"
    assert normalizer.normalize("15-08-2005") == "2005-08-15"


def test_date_textual() -> None:
    """14. Textual month format normalization."""
    normalizer = DateNormalizer()
    assert normalizer.normalize("1 May 2005") == "2005-05-01"
    assert normalizer.normalize("May 1, 2005") == "2005-05-01"
    assert normalizer.normalize("01 May 2005") == "2005-05-01"
    assert normalizer.normalize("1st May 2005") == "2005-05-01"
    assert normalizer.normalize("01-May-2005") == "2005-05-01"


def test_date_invalid_string() -> None:
    """15. Invalid date string returns None."""
    normalizer = DateNormalizer()
    assert normalizer.normalize("not a date") is None
    assert normalizer.normalize("99/99/9999") is None
    assert normalizer.normalize("abc/def/2005") is None


def test_date_impossible_date() -> None:
    """16. Impossible calendar dates return None."""
    normalizer = DateNormalizer()
    assert normalizer.normalize("31/02/2005") is None  # Feb 31 does not exist
    assert normalizer.normalize("29/02/2005") is None  # 2005 is not a leap year
    assert normalizer.normalize("31/04/2005") is None  # April has only 30 days


def test_date_none() -> None:
    """17. None input returns None."""
    normalizer = DateNormalizer()
    assert normalizer.normalize(None) is None


def test_date_empty_string() -> None:
    """18. Empty and whitespace-only strings return None."""
    normalizer = DateNormalizer()
    assert normalizer.normalize("") is None
    assert normalizer.normalize("   ") is None


def test_date_ambiguous_handling() -> None:
    """19. Ambiguous date handling with strict ambiguity rejection and configured resolution."""
    normalizer_strict = DateNormalizer(strict_ambiguity=True)
    normalizer_lenient = DateNormalizer(strict_ambiguity=False, dayfirst=True)

    # 05/06/2005 is ambiguous (June 5 vs May 6)
    assert normalizer_strict.is_ambiguous("05/06/2005") is True
    assert normalizer_strict.normalize("05/06/2005") is None

    # Lenient day-first interpretation (Indian standard) resolves to June 5
    assert normalizer_lenient.normalize("05/06/2005") == "2005-06-05"

    # Unambiguous date (day > 12) is never rejected
    assert normalizer_strict.is_ambiguous("25/06/2005") is False
    assert normalizer_strict.normalize("25/06/2005") == "2005-06-25"


# ==============================================================================
# 3. TEXT NORMALIZATION TESTS (20 - 25)
# ==============================================================================

def test_text_whitespace_normalization() -> None:
    """20. Text whitespace stripping and collapsing."""
    normalizer = TextNormalizer()
    assert normalizer.normalize("  Nashik,   Maharashtra  ") == "nashik, maharashtra"
    assert normalizer.normalize("Line 1\n\nLine 2\tTab") == "line 1 line 2 tab"


def test_text_lowercase() -> None:
    """21. Converting general text to lowercase."""
    normalizer = TextNormalizer()
    assert normalizer.normalize("MAHARASHTRA STATE BOARD") == "maharashtra state board"


def test_text_punctuation_handling() -> None:
    """22. Punctuation handling preserving delimiters and standardizing typography."""
    normalizer = TextNormalizer()
    # Curly quotes and en/em dashes are converted to standard ASCII
    raw = "“PreFlight” – Document: ‘Approved’"
    assert normalizer.normalize(raw) == '"preflight" - document: \'approved\''


def test_text_preserving_meaningful_content() -> None:
    """23. Preserving meaningful content, currency, and amounts."""
    normalizer = TextNormalizer()
    raw = "  Annual   Family Income: Rs. 2,50,000  "
    assert normalizer.normalize(raw) == "annual family income: rs. 2,50,000"


def test_text_preserving_numbers_identifiers() -> None:
    """24. Preserving certificate IDs, roll numbers, and structural slashes/hyphens."""
    normalizer = TextNormalizer()
    assert normalizer.normalize("ABC-001/2025") == "abc-001/2025"
    assert normalizer.normalize("MH/14/2023/12345") == "mh/14/2023/12345"
    assert normalizer.normalize("ROLL-NO: 987654") == "roll-no: 987654"


def test_text_none_and_empty() -> None:
    """25. None and empty text safely return None."""
    normalizer = TextNormalizer()
    assert normalizer.normalize(None) is None
    assert normalizer.normalize("") is None
    assert normalizer.normalize("   ") is None


# ==============================================================================
# 4. EXTRACTED DOCUMENT INTEGRATION TESTS (26 - 34)
# ==============================================================================

def test_document_normalize_name_field() -> None:
    """26. Normalizing applicant name in ExtractedDocument."""
    doc = ExtractedDocument(
        document_id="doc_01",
        name=ExtractedField(field_name="name", original=" Priti S. Ahire ", confidence=0.95),
    )
    normalized_doc = normalize_extracted_document(doc)
    assert normalized_doc.name.normalized == "priti s ahire"
    assert normalized_doc.name.original == " Priti S. Ahire "


def test_document_normalize_dob() -> None:
    """27. Normalizing date of birth field to ISO YYYY-MM-DD."""
    doc = ExtractedDocument(
        document_id="doc_02",
        date_of_birth=ExtractedField(field_name="date_of_birth", original="01/05/2005", confidence=0.92),
    )
    normalized_doc = normalize_extracted_document(doc)
    assert normalized_doc.date_of_birth.normalized == "2005-05-01"
    assert normalized_doc.date_of_birth.original == "01/05/2005"


def test_document_normalize_address() -> None:
    """28. Normalizing address field with TextNormalizer."""
    doc = ExtractedDocument(
        document_id="doc_03",
        address=ExtractedField(
            field_name="address",
            original="  Nashik, Maharashtra - 422003  ",
            confidence=0.88,
        ),
    )
    normalized_doc = normalize_extracted_document(doc)
    assert normalized_doc.address.normalized == "nashik, maharashtra - 422003"
    assert normalized_doc.address.original == "  Nashik, Maharashtra - 422003  "


def test_document_normalize_father_mother_names() -> None:
    """29. Normalizing father and mother names with NameNormalizer."""
    doc = ExtractedDocument(
        document_id="doc_04",
        father_name=ExtractedField(field_name="father_name", original="SHASHIKANT AHIRE"),
        mother_name=ExtractedField(field_name="mother_name", original="  Surekha   Ahire  "),
    )
    normalized_doc = normalize_extracted_document(doc)
    assert normalized_doc.father_name.normalized == "shashikant ahire"
    assert normalized_doc.mother_name.normalized == "surekha ahire"


def test_document_preserve_original_values() -> None:
    """30. Original values are never overwritten or mutated."""
    raw_name = " PRITI   S.   AHIRE "
    raw_dob = "15-08-2005"
    doc = ExtractedDocument(
        document_id="doc_05",
        name=ExtractedField(field_name="name", original=raw_name),
        date_of_birth=ExtractedField(field_name="date_of_birth", original=raw_dob),
    )
    normalized_doc = normalize_extracted_document(doc)
    assert normalized_doc.name.original == raw_name
    assert normalized_doc.date_of_birth.original == raw_dob


def test_document_preserve_confidence() -> None:
    """31. Confidence score is preserved exactly."""
    doc = ExtractedDocument(
        document_id="doc_06",
        name=ExtractedField(field_name="name", original="Priti Ahire", confidence=0.967),
    )
    normalized_doc = normalize_extracted_document(doc)
    assert normalized_doc.name.confidence == 0.967


def test_document_preserve_evidence() -> None:
    """32. Evidence list is completely preserved without alteration."""
    evidence = [Evidence(source_document="app.pdf", page_number=1, snippet="Applicant: Priti Ahire")]
    doc = ExtractedDocument(
        document_id="doc_07",
        name=ExtractedField(field_name="name", original="Priti Ahire", evidence=evidence),
    )
    normalized_doc = normalize_extracted_document(doc)
    assert len(normalized_doc.name.evidence) == 1
    assert normalized_doc.name.evidence[0].source_document == "app.pdf"
    assert normalized_doc.name.evidence[0].snippet == "Applicant: Priti Ahire"


def test_document_safely_handle_additional_fields() -> None:
    """33. Safely handle various additional_fields types (strings, lists, dicts, numbers)."""
    doc = ExtractedDocument(
        document_id="doc_08",
        additional_fields={
            "course": ExtractedField(field_name="course", original="  B.Tech Computer Engineering  "),
            "subjects": ExtractedField(field_name="subjects", original=[" MATHEMATICS ", " PHYSICS "]),
            "metadata": ExtractedField(field_name="metadata", original={"issued_by": " TEHSILDAR "}),
            "rank": ExtractedField(field_name="rank", original=42),
            "passing_date": ExtractedField(field_name="passing_date", original="01/06/2023"),
            "empty_val": ExtractedField(field_name="empty_val", original=None),
        },
    )
    normalized_doc = normalize_extracted_document(doc)
    assert normalized_doc.additional_fields["course"].normalized == "b.tech computer engineering"
    assert normalized_doc.additional_fields["subjects"].normalized == ["mathematics", "physics"]
    assert normalized_doc.additional_fields["metadata"].normalized == {"issued_by": "tehsildar"}
    assert normalized_doc.additional_fields["rank"].normalized == 42
    assert normalized_doc.additional_fields["passing_date"].normalized == "2023-06-01"
    assert normalized_doc.additional_fields["empty_val"].normalized is None


def test_document_multiple_fields_normalized_together() -> None:
    """34. Full ExtractedDocument with all standard scholarship fields normalized in one pass."""
    doc = ExtractedDocument(
        document_id="doc_scholarship_01",
        document_type=DocumentType.APPLICATION_FORM,
        name=ExtractedField(field_name="name", original=" PRITI S. AHIRE ", confidence=0.98),
        date_of_birth=ExtractedField(field_name="date_of_birth", original="01/05/2005", confidence=0.95),
        father_name=ExtractedField(field_name="father_name", original=" SHASHIKANT AHIRE ", confidence=0.92),
        mother_name=ExtractedField(field_name="mother_name", original=" SUREKHA AHIRE ", confidence=0.90),
        address=ExtractedField(field_name="address", original=" 123 Main Road, Nashik ", confidence=0.85),
        certificate_number=ExtractedField(field_name="certificate_number", original=" CERT-2025/99 ", confidence=0.99),
        issue_date=ExtractedField(field_name="issue_date", original="10/01/2025", confidence=0.94),
        marks=ExtractedField(field_name="marks", original=" 480/500 ", confidence=0.91),
        percentage=ExtractedField(field_name="percentage", original=" 96.0% ", confidence=0.93),
    )
    normalized = normalize_extracted_document(doc)

    assert normalized.name.normalized == "priti s ahire"
    assert normalized.date_of_birth.normalized == "2005-05-01"
    assert normalized.father_name.normalized == "shashikant ahire"
    assert normalized.mother_name.normalized == "surekha ahire"
    assert normalized.address.normalized == "123 main road, nashik"
    assert normalized.certificate_number.normalized == "cert-2025/99"
    assert normalized.issue_date.normalized == "2025-01-10"
    assert normalized.marks.normalized == "480/500"
    assert normalized.percentage.normalized == "96.0%"
