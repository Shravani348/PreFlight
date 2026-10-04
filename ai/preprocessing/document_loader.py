"""Unified document loader routing supported files to PDF and image processors."""

from pathlib import Path
from typing import Dict, Optional, Union

from ai.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    UnsupportedDocumentError,
)
from ai.preprocessing.image_processor import ImageProcessor
from ai.preprocessing.models import PreprocessedDocument
from ai.preprocessing.pdf_processor import PDFProcessor


class DocumentLoader:
    """Unified document loader routing supported files to PDF and image processors."""

    SUPPORTED_EXTENSIONS: Dict[str, str] = {
        ".pdf": "pdf",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
    }

    def __init__(
        self,
        pdf_processor: Optional[PDFProcessor] = None,
        image_processor: Optional[ImageProcessor] = None,
    ) -> None:
        self.pdf_processor = pdf_processor or PDFProcessor()
        self.image_processor = image_processor or ImageProcessor()

    def load(self, file_path: Union[str, Path]) -> PreprocessedDocument:
        """Load and preprocess a supported document (PDF, JPG, JPEG, PNG)."""
        if not file_path:
            raise DocumentNotFoundError("No document file path provided.")

        path = Path(file_path).resolve()
        if not path.exists():
            raise DocumentNotFoundError(f"Document file does not exist: {path}")

        if not path.is_file():
            raise DocumentProcessingError(f"Provided path is not a file: {path}")

        ext = path.suffix.lower()
        processor_type = self.SUPPORTED_EXTENSIONS.get(ext)

        if not processor_type:
            supported = ", ".join(sorted(self.SUPPORTED_EXTENSIONS.keys()))
            raise UnsupportedDocumentError(
                f"Unsupported document format '{ext}' for file '{path.name}'. Supported formats: {supported}"
            )

        if processor_type == "pdf":
            return self.pdf_processor.process(path)
        elif processor_type == "image":
            return self.image_processor.process(path)
        else:
            raise UnsupportedDocumentError(f"No processor available for format '{ext}'")
