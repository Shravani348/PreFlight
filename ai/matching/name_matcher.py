"""Name matcher placeholder."""


class NameMatcher:
    """Compares person names across documents and computes similarity scores."""

    def compare(self, name_a: str, name_b: str) -> float:
        """Calculate similarity score between two normalized names."""
        raise NotImplementedError
