"""Image processing placeholder."""

from typing import Any


class ImageProcessor:
    """Handles image preprocessing, resizing, and format checks."""

    def process(self, file_path: str) -> Any:
        """Process an image file."""
        raise NotImplementedError
