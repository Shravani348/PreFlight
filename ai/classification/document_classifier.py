"""Document classifier placeholder."""

from typing import Any


class DocumentClassifier:
    """Classifies document types (e.g. ID card, Marksheet, Certificate)."""

    def classify(self, document_content: Any) -> Any:
        """Classify a given document."""
        raise NotImplementedError
