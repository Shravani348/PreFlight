"""Name normalizer for scholarship application documents."""

import unicodedata
from typing import Optional


class NameNormalizer:
    """Normalizes person names for consistent cross-document matching."""

    def normalize(self, name: Optional[str]) -> Optional[str]:
        """Normalize a raw person name string.

        Rules:
        - Convert to lowercase.
        - Normalize Unicode sequences to canonical NFC representation.
        - Strip leading and trailing whitespace.
        - Replace punctuation and separators (hyphens, dots, commas, slashes, underscores) with spaces.
        - Preserve valid Indic/Devanagari characters, combining marks (matras), viramas, and conjuncts.
        - Collapse repeated whitespace into a single space.
        - Preserve meaningful name tokens and initials without guessing or expanding.
        - Return None for empty, whitespace-only, or punctuation-only strings.
        - Do not reorder names or infer missing parts.
        """
        if name is None:
            return None
        if not isinstance(name, str):
            name = str(name)

        raw = unicodedata.normalize("NFC", name).strip()
        if not raw:
            return None

        # Filter characters: preserve Letters (L), Numbers (N), Combining Marks (M), and spaces.
        # Replace punctuation, symbols, and formatting controls with spaces.
        chars = []
        for c in raw:
            cat = unicodedata.category(c)
            if cat.startswith(("L", "N", "M")) or c.isspace():
                chars.append(c)
            else:
                chars.append(" ")

        cleaned = "".join(chars).lower()
        tokens = cleaned.split()
        if not tokens:
            return None

        return " ".join(tokens)


def normalize_name(name: Optional[str]) -> Optional[str]:
    """Helper function to normalize a person name."""
    return NameNormalizer().normalize(name)
