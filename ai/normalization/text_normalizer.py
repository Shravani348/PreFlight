"""Text normalizer for general text fields and identifiers."""

import re
from typing import Optional


class TextNormalizer:
    """General text cleaning and canonicalization while preserving identifiers and numbers."""

    def normalize(self, text: Optional[str]) -> Optional[str]:
        """Normalize general text input.

        Rules:
        - Convert to lowercase.
        - Strip leading and trailing whitespace.
        - Collapse multiple spaces, tabs, and newlines into a single space.
        - Normalize typographical variations (curly quotes to straight quotes, en/em dashes to hyphens).
        - Preserve meaningful identifiers (e.g., 'ABC-001/2025'), numbers, currency, and structural separators.
        - Return None for None, empty string, or whitespace-only inputs.
        """
        if text is None:
            return None
        if not isinstance(text, str):
            text = str(text)

        raw = text.strip()
        if not raw:
            return None

        # Replace non-breaking spaces and zero-width spaces
        cleaned = raw.replace("\u00a0", " ").replace("\u200b", "")

        # Normalize typographical quotes and dashes
        cleaned = cleaned.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        cleaned = cleaned.replace("–", "-").replace("—", "-")

        # Convert to lowercase
        cleaned = cleaned.lower()

        # Collapse whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        if not cleaned:
            return None

        return cleaned


def normalize_text(text: Optional[str]) -> Optional[str]:
    """Helper function to normalize general text."""
    return TextNormalizer().normalize(text)
