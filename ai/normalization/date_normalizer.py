"""Date normalizer for scholarship application documents."""

import datetime
import re
from typing import Optional

MONTH_NAME_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


class DateNormalizer:
    """Normalizes various date formats to ISO-8601 (YYYY-MM-DD)."""

    def __init__(self, dayfirst: bool = True, strict_ambiguity: bool = False):
        self.dayfirst = dayfirst
        self.strict_ambiguity = strict_ambiguity

    def is_ambiguous(self, raw_date: Optional[str]) -> bool:
        """Check if a numeric date string is ambiguous between DD/MM and MM/DD."""
        if not raw_date or not isinstance(raw_date, str):
            return False
        raw = raw_date.strip()
        match = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", raw)
        if match:
            p1, p2 = int(match.group(1)), int(match.group(2))
            return p1 <= 12 and p2 <= 12 and p1 != p2
        return False

    def normalize(
        self,
        raw_date: Optional[str],
        strict_ambiguity: Optional[bool] = None,
        dayfirst: Optional[bool] = None,
    ) -> Optional[str]:
        """Normalize a raw date string to YYYY-MM-DD.

        Args:
            raw_date: The date string to normalize.
            strict_ambiguity: If True, reject dates where DD/MM vs MM/DD is ambiguous.
                              Defaults to self.strict_ambiguity.
            dayfirst: If True, interpret ambiguous dates as day-first (Indian standard).
                      Defaults to self.dayfirst.

        Returns:
            Normalized date string in 'YYYY-MM-DD' format, or None if invalid or ambiguous.
        """
        if raw_date is None:
            return None
        if not isinstance(raw_date, str):
            raw_date = str(raw_date)

        raw = raw_date.strip()
        if not raw:
            return None

        is_strict = self.strict_ambiguity if strict_ambiguity is None else strict_ambiguity
        use_dayfirst = self.dayfirst if dayfirst is None else dayfirst

        # 1. ISO format: YYYY-MM-DD or YYYY/MM/DD or YYYY.MM.DD
        iso_match = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", raw)
        if iso_match:
            y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            return self._format_date(y, m, d)

        # 2. Numeric date formats: DD/MM/YYYY or MM/DD/YYYY
        num_match = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", raw)
        if num_match:
            p1 = int(num_match.group(1))
            p2 = int(num_match.group(2))
            year = int(num_match.group(3))

            # Check ambiguity
            if p1 <= 12 and p2 <= 12 and p1 != p2:
                if is_strict:
                    return None
                if use_dayfirst:
                    day, month = p1, p2
                else:
                    month, day = p1, p2
            elif p1 > 12 and p2 <= 12:
                day, month = p1, p2
            elif p2 > 12 and p1 <= 12:
                month, day = p1, p2
            elif p1 == p2 and p1 <= 12:
                day, month = p1, p2
            else:
                return None

            return self._format_date(year, month, day)

        # 3. Textual formats:
        # e.g., "1 May 2005", "01 May 2005", "1st May 2005", "1-May-2005"
        text_dmy = re.match(r"^(\d{1,2})(?:st|nd|rd|th)?[\s\-,.]+(\w+)[\s\-,.]+(\d{4})$", raw, re.IGNORECASE)
        if text_dmy:
            day = int(text_dmy.group(1))
            month_str = text_dmy.group(2).lower()
            year = int(text_dmy.group(3))
            month = MONTH_NAME_MAP.get(month_str)
            if month:
                return self._format_date(year, month, day)

        # e.g., "May 1, 2005", "May 01 2005", "May 1st, 2005"
        text_mdy = re.match(r"^(\w+)[\s\-,.]+(\d{1,2})(?:st|nd|rd|th)?[\s\-,.]+(\d{4})$", raw, re.IGNORECASE)
        if text_mdy:
            month_str = text_mdy.group(1).lower()
            day = int(text_mdy.group(2))
            year = int(text_mdy.group(3))
            month = MONTH_NAME_MAP.get(month_str)
            if month:
                return self._format_date(year, month, day)

        # e.g., "2005 May 1", "2005, May 01"
        text_ymd = re.match(r"^(\d{4})[\s\-,.]+(\w+)[\s\-,.]+(\d{1,2})(?:st|nd|rd|th)?$", raw, re.IGNORECASE)
        if text_ymd:
            year = int(text_ymd.group(1))
            month_str = text_ymd.group(2).lower()
            day = int(text_ymd.group(3))
            month = MONTH_NAME_MAP.get(month_str)
            if month:
                return self._format_date(year, month, day)

        return None

    def _format_date(self, year: int, month: int, day: int) -> Optional[str]:
        """Validate and return formatted YYYY-MM-DD string, or None if invalid."""
        try:
            d = datetime.date(year, month, day)
            return d.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            return None


def normalize_date(
    raw_date: Optional[str],
    strict_ambiguity: bool = False,
    dayfirst: bool = True,
) -> Optional[str]:
    """Helper function to normalize a date string."""
    return DateNormalizer(dayfirst=dayfirst, strict_ambiguity=strict_ambiguity).normalize(raw_date)
