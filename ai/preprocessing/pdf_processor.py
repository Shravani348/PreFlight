"""PDF processing module for selectable and scanned document extraction."""

import os
from pathlib import Path
from typing import List, Union
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from PIL import Image

from ai.exceptions import CorruptedDocumentError, DocumentNotFoundError
from ai.preprocessing.models import PreprocessedDocument, PreprocessedPage


class PDFProcessor:
    """Extracts selectable text, page counts, and embedded page images from PDFs."""

    USABLE_TEXT_THRESHOLD: int = 30

    def process(self, file_path: Union[str, Path]) -> PreprocessedDocument:
        """Process a PDF file and return a PreprocessedDocument structure."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise DocumentNotFoundError(f"PDF file does not exist: {path}")

        try:
            reader = PdfReader(str(path))
            page_count = len(reader.pages)
        except (PdfReadError, Exception) as exc:
            raise CorruptedDocumentError(
                f"Failed to read PDF document: {path.name}. Error: {exc}"
            ) from exc

        if page_count == 0:
            raise CorruptedDocumentError(f"PDF document contains 0 pages: {path.name}")

        page_texts: List[str] = []
        preprocessed_pages: List[PreprocessedPage] = []
        all_images: List[Image.Image] = []

        for idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            page_texts.append(page_text)

            page_images: List[Image.Image] = []
            try:
                for img_obj in page.images:
                    try:
                        pil_img = img_obj.image.convert("RGB")
                        page_images.append(pil_img)
                        all_images.append(pil_img)
                    except Exception:
                        continue
            except Exception:
                pass

            preprocessed_pages.append(
                PreprocessedPage(
                    page_number=idx,
                    text=page_text.strip() if page_text.strip() else None,
                    images=page_images,
                    metadata={
                        "char_count": len(page_text),
                        "extracted_image_count": len(page_images),
                    },
                )
            )

        full_text = "\n\n".join(t for t in page_texts if t.strip()).strip() or None
        has_usable_text = bool(full_text and len(full_text) >= self.USABLE_TEXT_THRESHOLD)
        requires_vision_processing = (not has_usable_text) or (len(all_images) > 0)

        file_size = os.path.getsize(path)

        return PreprocessedDocument(
            file_path=str(path),
            file_name=path.name,
            file_type="pdf",
            mime_type="application/pdf",
            page_count=page_count,
            full_text=full_text,
            page_texts=page_texts,
            pages=preprocessed_pages,
            images=all_images,
            has_usable_text=has_usable_text,
            requires_vision_processing=requires_vision_processing,
            metadata={
                "file_size_bytes": file_size,
                "is_encrypted": reader.is_encrypted,
                "total_extracted_images": len(all_images),
            },
        )
