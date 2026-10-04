"""Document loader placeholder."""

from typing import Any


class DocumentLoader:
    """Loads documents from disk or memory for downstream processing."""

    def load(self, file_path: str) -> Any:
        """Load document content."""
        raise NotImplementedError
