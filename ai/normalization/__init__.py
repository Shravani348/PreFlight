"""Normalization package for PreFlight scholarship document extraction."""

from typing import Any, Dict, List, Optional
from ai.normalization.date_normalizer import DateNormalizer, normalize_date
from ai.normalization.name_normalizer import NameNormalizer, normalize_name
from ai.normalization.text_normalizer import TextNormalizer, normalize_text
from ai.schemas.extraction import ExtractedDocument, ExtractedField


class DocumentNormalizer:
    """Normalizes extracted fields in an ExtractedDocument without modifying originals."""

    def __init__(
        self,
        name_normalizer: Optional[NameNormalizer] = None,
        date_normalizer: Optional[DateNormalizer] = None,
        text_normalizer: Optional[TextNormalizer] = None,
    ):
        self.name_normalizer = name_normalizer or NameNormalizer()
        self.date_normalizer = date_normalizer or DateNormalizer()
        self.text_normalizer = text_normalizer or TextNormalizer()

    def normalize_field(
        self,
        field: Optional[ExtractedField],
        field_type: str = "text",
    ) -> Optional[ExtractedField]:
        """Populate the normalized value of an ExtractedField while preserving original, confidence, and evidence.

        Args:
            field: ExtractedField to normalize.
            field_type: One of 'name', 'date', 'text', or 'auto'.

        Returns:
            The ExtractedField with its `normalized` attribute populated, or None if field was None.
        """
        if field is None:
            return None

        orig = field.original
        if orig is None:
            field.normalized = None
            return field

        if field_type == "name":
            field.normalized = self.name_normalizer.normalize(orig)
        elif field_type == "date":
            field.normalized = self.date_normalizer.normalize(orig)
        elif field_type == "text":
            field.normalized = self._normalize_generic_value(orig)
        else:
            field.normalized = self._normalize_generic_value(orig)

        return field

    def _normalize_generic_value(self, val: Any) -> Any:
        """Safely normalize a generic value based on its Python data type."""
        if val is None:
            return None
        if isinstance(val, str):
            return self.text_normalizer.normalize(val)
        if isinstance(val, list):
            return [
                self.text_normalizer.normalize(item) if isinstance(item, str) else item
                for item in val
            ]
        if isinstance(val, dict):
            return {
                k: self.text_normalizer.normalize(v) if isinstance(v, str) else v
                for k, v in val.items()
            }
        # Numeric or boolean values are preserved as-is
        return val

    def normalize_document(self, document: ExtractedDocument) -> ExtractedDocument:
        """Populate normalized values across all extracted fields in an ExtractedDocument.

        Preserves all `original` values, confidence scores, and evidence intact.
        """
        # 1. Core Name Fields
        if document.name is not None:
            self.normalize_field(document.name, field_type="name")
        if document.father_name is not None:
            self.normalize_field(document.father_name, field_type="name")
        if document.mother_name is not None:
            self.normalize_field(document.mother_name, field_type="name")

        # 2. Core Date Fields
        if document.date_of_birth is not None:
            self.normalize_field(document.date_of_birth, field_type="date")
        if document.issue_date is not None:
            self.normalize_field(document.issue_date, field_type="date")
        if document.expiry_date is not None:
            self.normalize_field(document.expiry_date, field_type="date")

        # 3. Core Text & Numeric Fields
        if document.address is not None:
            self.normalize_field(document.address, field_type="text")
        if document.certificate_number is not None:
            self.normalize_field(document.certificate_number, field_type="text")
        if document.marks is not None:
            self.normalize_field(document.marks, field_type="text")
        if document.percentage is not None:
            self.normalize_field(document.percentage, field_type="text")

        # 4. Additional Fields
        name_keys = {"applicant_name", "candidate_name", "student_name", "guardian_name"}
        for key, field in document.additional_fields.items():
            if field is None:
                continue

            lowered_key = key.lower()
            if lowered_key in name_keys:
                self.normalize_field(field, field_type="name")
            elif "date" in lowered_key or "dob" in lowered_key:
                self.normalize_field(field, field_type="date")
            else:
                self.normalize_field(field, field_type="text")

        return document


def normalize_extracted_document(
    document: ExtractedDocument,
    name_normalizer: Optional[NameNormalizer] = None,
    date_normalizer: Optional[DateNormalizer] = None,
    text_normalizer: Optional[TextNormalizer] = None,
) -> ExtractedDocument:
    """Convenience function to normalize an ExtractedDocument."""
    normalizer = DocumentNormalizer(
        name_normalizer=name_normalizer,
        date_normalizer=date_normalizer,
        text_normalizer=text_normalizer,
    )
    return normalizer.normalize_document(document)


__all__ = [
    "DateNormalizer",
    "DocumentNormalizer",
    "NameNormalizer",
    "TextNormalizer",
    "normalize_date",
    "normalize_extracted_document",
    "normalize_name",
    "normalize_text",
]
