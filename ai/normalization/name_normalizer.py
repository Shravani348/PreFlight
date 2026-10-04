"""Name normalizer for scholarship application documents."""

import re
from typing import Optional


class NameNormalizer:
    """Normalizes person names for consistent cross-document matching."""

    def normalize(self, name: Optional[str]) -> Optional[str]:
        """Normalize a raw person name string.

        Rules:
        - Convert to lowercase.
        - Strip leading and trailing whitespace.
        - Replace common separators/punctuation (hyphens, dots, commas, slashes, underscores) with spaces.
        - Collapse repeated whitespace into a single space.
        - Preserve meaningful name tokens and initials without guessing or expanding.
        - Return None for empty, whitespace-only, or punctuation-only strings.
        - Do not reorder names or infer missing parts.
        """
        if name is None:
            return None
        if not isinstance(name, str):
            name = str(name)

        raw = name.strip()
        if not raw:
            return None

        # Replace separators and common punctuation with space
        cleaned = re.sub(r"[\-.,/\\_'\"]", " ", raw)
        # Replace any remaining non-alphanumeric punctuation (keeping word characters and spaces)
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        cleaned = cleaned.lower()

        tokens = cleaned.split()
        if not tokens:
            return None

        return " ".join(tokens)


def normalize_name(name: Optional[str]) -> Optional[str]:
    """Helper function to normalize a person name."""
    return NameNormalizer().normalize(name)
