"""Date normalizer placeholder."""

from typing import Optional


class DateNormalizer:
    """Normalizes various date formats to ISO-8601."""

    def normalize(self, raw_date: str) -> Optional[str]:
        """Normalize a raw date string."""
        raise NotImplementedError
