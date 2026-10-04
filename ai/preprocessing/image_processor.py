"""Image processing module for JPG, JPEG, and PNG document formats."""

import os
from pathlib import Path
from typing import Dict, Union
from PIL import Image, ImageOps, UnidentifiedImageError

from ai.exceptions import CorruptedDocumentError, DocumentNotFoundError, UnsupportedDocumentError
from ai.preprocessing.models import PreprocessedDocument, PreprocessedPage


class ImageProcessor:
    """Validates, converts, and extracts metadata from image files (JPG, JPEG, PNG)."""

    SUPPORTED_IMAGE_TYPES: Dict[str, str] = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }

    def process(self, file_path: Union[str, Path]) -> PreprocessedDocument:
        """Process an image file and return a PreprocessedDocument structure."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise DocumentNotFoundError(f"Image file does not exist: {path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_IMAGE_TYPES:
            raise UnsupportedDocumentError(
                f"Unsupported image format: '{ext}'. Supported formats: {', '.join(sorted(self.SUPPORTED_IMAGE_TYPES.keys()))}"
            )

        try:
            with Image.open(path) as img:
                # Verify that it is a valid, readable image without corrupt header
                img.verify()

            # Re-open after verify() to access pixels and safely convert mode
            with Image.open(path) as img:
                img_format = img.format or ext.lstrip(".").upper()
                orig_mode = img.mode

                # Apply EXIF orientation transposition if present (e.g. smartphone camera orientation)
                transposed_img = ImageOps.exif_transpose(img)
                if transposed_img is None:
                    transposed_img = img

                width, height = transposed_img.size

                # Safe conversion to consistent RGB representation without destructive resizing
                if transposed_img.mode != "RGB":
                    rgb_img = transposed_img.convert("RGB")
                else:
                    rgb_img = transposed_img.copy()
        except (UnidentifiedImageError, OSError, Exception) as exc:
            raise CorruptedDocumentError(
                f"Cannot open or read image file '{path.name}': {exc}"
            ) from exc

        file_size = os.path.getsize(path)
        mime_type = self.SUPPORTED_IMAGE_TYPES[ext]
        clean_type = ext.lstrip(".")

        page = PreprocessedPage(
            page_number=1,
            text=None,
            images=[rgb_img],
            metadata={
                "width": width,
                "height": height,
                "original_mode": orig_mode,
                "format": img_format,
            },
        )

        return PreprocessedDocument(
            file_path=str(path),
            file_name=path.name,
            file_type=clean_type,
            mime_type=mime_type,
            page_count=1,
            full_text=None,
            page_texts=[],
            pages=[page],
            images=[rgb_img],
            has_usable_text=False,
            requires_vision_processing=True,
            metadata={
                "file_size_bytes": file_size,
                "width": width,
                "height": height,
                "original_mode": orig_mode,
                "format": img_format,
            },
        )
