"""Tests for document preprocessing pipeline (PDF, JPG, PNG)."""

from pathlib import Path
import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter

from ai.exceptions import (
    CorruptedDocumentError,
    DocumentNotFoundError,
    UnsupportedDocumentError,
)
from ai.preprocessing.document_loader import DocumentLoader
from ai.preprocessing.image_processor import ImageProcessor
from ai.preprocessing.models import PreprocessedDocument
from ai.preprocessing.pdf_processor import PDFProcessor


def _create_minimal_text_pdf(path: Path, text: str) -> None:
    """Helper to generate a clean, valid text-based PDF without external tools."""
    content = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET"
    stream_bytes = content.encode("latin1")
    stream_len = len(stream_bytes)

    # Calculate exact byte offsets for cross-reference table
    header = b"%PDF-1.4\n"
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
        b"endobj\n"
    )
    obj4_header = f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin1")
    obj4_body = stream_bytes + b"\nendstream\nendobj\n"
    obj4 = obj4_header + obj4_body
    obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

    offsets = [0]
    curr = len(header)
    offsets.append(curr)
    curr += len(obj1)
    offsets.append(curr)
    curr += len(obj2)
    offsets.append(curr)
    curr += len(obj3)
    offsets.append(curr)
    curr += len(obj4)
    offsets.append(curr)

    xref = f"xref\n0 6\n0000000000 65535 f \n".encode("latin1")
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode("latin1")

    xref_offset = curr + len(obj5)
    trailer = (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "latin1"
        )
    )

    pdf_bytes = header + obj1 + obj2 + obj3 + obj4 + obj5 + xref + trailer
    with open(path, "wb") as f:
        f.write(pdf_bytes)


def _create_scanned_pdf(path: Path, pages: int = 1) -> None:
    """Helper to generate an image-only scanned PDF using Pillow."""
    images = [
        Image.new("RGB", (200, 200), color=(100 + i * 20, 100, 150))
        for i in range(pages)
    ]
    if len(images) == 1:
        images[0].save(path, "PDF")
    else:
        images[0].save(path, "PDF", save_all=True, append_images=images[1:])


def test_valid_jpg_loading(tmp_path: Path) -> None:
    """Test loading and preprocessing of a valid JPG image."""
    img_path = tmp_path / "test_photo.jpg"
    img = Image.new("RGB", (300, 400), color=(255, 0, 0))
    img.save(img_path, "JPEG")

    processor = ImageProcessor()
    doc = processor.process(img_path)

    assert isinstance(doc, PreprocessedDocument)
    assert doc.file_name == "test_photo.jpg"
    assert doc.file_type in ["jpg", "jpeg"]
    assert doc.mime_type == "image/jpeg"
    assert doc.page_count == 1
    assert len(doc.images) == 1
    assert doc.images[0].size == (300, 400)
    assert doc.images[0].mode == "RGB"
    assert doc.requires_vision_processing is True
    assert doc.has_usable_text is False


def test_valid_png_loading(tmp_path: Path) -> None:
    """Test loading and preprocessing of a valid PNG image with RGBA conversion."""
    png_path = tmp_path / "test_signature.png"
    img = Image.new("RGBA", (250, 150), color=(0, 255, 0, 128))
    img.save(png_path, "PNG")

    loader = DocumentLoader()
    doc = loader.load(png_path)

    assert doc.file_type == "png"
    assert doc.mime_type == "image/png"
    assert doc.page_count == 1
    assert len(doc.images) == 1
    assert doc.images[0].mode == "RGB"  # Converted to consistent RGB
    assert doc.metadata["width"] == 250
    assert doc.metadata["height"] == 150
    assert doc.metadata["original_mode"] == "RGBA"


def test_invalid_image_handling(tmp_path: Path) -> None:
    """Corrupt image files must raise CorruptedDocumentError."""
    bad_img = tmp_path / "corrupt.jpg"
    bad_img.write_bytes(b"not an image binary payload")

    processor = ImageProcessor()
    with pytest.raises(CorruptedDocumentError):
        processor.process(bad_img)


def test_pdf_text_extraction(tmp_path: Path) -> None:
    """Selectable PDF text should be extracted and usable text detected."""
    pdf_path = tmp_path / "application_form.pdf"
    sample_text = "PreFlight Scholarship Form: Candidate Name Priti Ahire."
    _create_minimal_text_pdf(pdf_path, sample_text)

    processor = PDFProcessor()
    doc = processor.process(pdf_path)

    assert doc.file_type == "pdf"
    assert doc.mime_type == "application/pdf"
    assert doc.page_count == 1
    assert doc.full_text is not None
    assert "Priti Ahire" in doc.full_text
    assert doc.has_usable_text is True
    assert doc.requires_vision_processing is False


def test_pdf_page_count(tmp_path: Path) -> None:
    """Verify accurate page count on multi-page PDFs."""
    base_pdf = tmp_path / "single.pdf"
    _create_minimal_text_pdf(base_pdf, "Sample page text")

    multi_pdf = tmp_path / "multi.pdf"
    reader = PdfReader(str(base_pdf))
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    writer.add_page(reader.pages[0])
    writer.add_page(reader.pages[0])
    with open(multi_pdf, "wb") as f:
        writer.write(f)

    processor = PDFProcessor()
    doc = processor.process(multi_pdf)

    assert doc.page_count == 3
    assert len(doc.pages) == 3
    assert len(doc.page_texts) == 3


def test_scanned_image_pdf_handling(tmp_path: Path) -> None:
    """Image-only scanned PDFs must flag requires_vision_processing and extract images."""
    scanned_path = tmp_path / "scanned_marksheet.pdf"
    _create_scanned_pdf(scanned_path, pages=2)

    processor = PDFProcessor()
    doc = processor.process(scanned_path)

    assert doc.page_count == 2
    assert doc.has_usable_text is False
    assert doc.requires_vision_processing is True
    assert len(doc.images) >= 1  # Embedded page images extracted


def test_unsupported_file_extension(tmp_path: Path) -> None:
    """Unsupported document types must raise UnsupportedDocumentError."""
    unsupported = tmp_path / "notes.docx"
    unsupported.write_text("Hello world")

    loader = DocumentLoader()
    with pytest.raises(UnsupportedDocumentError):
        loader.load(unsupported)


def test_missing_file() -> None:
    """Non-existent files must raise DocumentNotFoundError."""
    loader = DocumentLoader()
    with pytest.raises(DocumentNotFoundError):
        loader.load("D:/non_existent_folder/missing_file.pdf")


def test_unified_loader_routing(tmp_path: Path) -> None:
    """DocumentLoader must route PDFs to PDF processor and images to Image processor."""
    pdf_file = tmp_path / "doc.pdf"
    _create_minimal_text_pdf(pdf_file, "PreFlight Application Verification")

    jpg_file = tmp_path / "aadhaar.jpg"
    img = Image.new("RGB", (100, 100), color=(10, 20, 30))
    img.save(jpg_file, "JPEG")

    loader = DocumentLoader()

    doc_pdf = loader.load(pdf_file)
    assert doc_pdf.file_type == "pdf"

    doc_jpg = loader.load(jpg_file)
    assert doc_jpg.file_type in ["jpg", "jpeg"]


def test_basic_metadata_preservation(tmp_path: Path) -> None:
    """Metadata such as file sizes, dimensions, and page info are preserved."""
    img_file = tmp_path / "meta_test.png"
    img = Image.new("RGB", (320, 240), color="blue")
    img.save(img_file, "PNG")

    loader = DocumentLoader()
    doc = loader.load(img_file)

    assert doc.metadata["width"] == 320
    assert doc.metadata["height"] == 240
    assert doc.metadata["file_size_bytes"] > 0
    assert len(doc.pages) == 1
    assert doc.pages[0].metadata["width"] == 320
