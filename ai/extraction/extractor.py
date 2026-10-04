"""Document extractor coordinating extraction flows."""

from typing import Any


class DocumentExtractor:
    """Coordinates extraction logic across documents."""

    def extract_document(self, document: Any) -> Any:
        """Extract key information from a document."""
        raise NotImplementedError
