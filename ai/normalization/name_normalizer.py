"""Name normalizer placeholder."""


class NameNormalizer:
    """Normalizes person names for consistent cross-document matching."""

    def normalize(self, name: str) -> str:
        """Normalize a raw name string."""
        raise NotImplementedError
