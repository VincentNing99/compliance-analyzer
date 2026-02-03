"""
PDF Parser module - Extract text from PDF documents.

Uses PyMuPDF (fitz) for text extraction with pytesseract OCR fallback
for scanned documents.
"""

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    """Represents a parsed PDF document."""

    filename: str
    text: str
    pages: list[str] = field(default_factory=list)
    page_count: int = 0
    metadata: dict = field(default_factory=dict)


class PDFParser:
    """
    Extracts text from PDF files.

    Uses PyMuPDF for native text extraction. Falls back to OCR
    (pytesseract) for pages that appear to be scanned images.
    """

    def __init__(self, ocr_enabled: bool = True):
        """
        Initialize the PDF parser.

        Args:
            ocr_enabled: Whether to use OCR for scanned pages (default True)
        """
        self.ocr_enabled = ocr_enabled

    def parse(self, pdf_path: str | Path) -> ParsedDocument:
        """
        Parse a PDF file and extract text.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ParsedDocument with extracted text and metadata
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        logger.info(f"Parsing PDF: {pdf_path.name}")

        doc = fitz.open(pdf_path)
        pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # If no text extracted, try OCR
            if not text.strip() and self.ocr_enabled:
                logger.debug(f"Page {page_num + 1}: No text found, trying OCR")
                text = self._ocr_page(page)

            pages.append(text)

        doc.close()

        full_text = "\n\n".join(pages)

        return ParsedDocument(
            filename=pdf_path.name,
            text=full_text,
            pages=pages,
            page_count=len(pages),
            metadata={"source_path": str(pdf_path)},
        )

    def parse_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> ParsedDocument:
        """
        Parse PDF from bytes (useful for file uploads).

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Name to assign to the document

        Returns:
            ParsedDocument with extracted text and metadata
        """
        logger.info(f"Parsing PDF from bytes: {filename}")

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if not text.strip() and self.ocr_enabled:
                logger.debug(f"Page {page_num + 1}: No text found, trying OCR")
                text = self._ocr_page(page)

            pages.append(text)

        doc.close()

        full_text = "\n\n".join(pages)

        return ParsedDocument(
            filename=filename,
            text=full_text,
            pages=pages,
            page_count=len(pages),
            metadata={"source": "bytes"},
        )

    def _ocr_page(self, page: fitz.Page) -> str:
        """
        Perform OCR on a PDF page.

        Args:
            page: PyMuPDF page object

        Returns:
            Extracted text from OCR
        """
        # Render page to image at 300 DPI for better OCR accuracy
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")

        # Convert to PIL Image for pytesseract
        image = Image.open(io.BytesIO(img_bytes))

        # Run OCR
        text = pytesseract.image_to_string(image)

        return text
