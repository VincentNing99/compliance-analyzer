"""
LlamaParse integration for document extraction.

Uses LlamaParse for high-quality PDF and document parsing with
support for tables, images, and complex layouts.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from llama_parse import LlamaParse
from tenacity import retry, stop_after_attempt, wait_exponential

from compliance_auditor.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    """Represents a parsed document from LlamaParse."""

    filename: str
    text: str
    pages: list[str] = field(default_factory=list)
    page_count: int = 0
    metadata: dict = field(default_factory=dict)


class LlamaCloudParser:
    """
    Document parser using LlamaParse.

    Supports PDF, DOCX, PPTX, and other document formats with
    high-quality extraction including tables and images.
    """

    def __init__(self):
        """Initialize the LlamaParse parser."""
        settings = get_settings()

        self.parser = LlamaParse(
            api_key=settings.llama_cloud_api_key,
            result_type=settings.llama_parse_result_type,
            language=settings.llama_parse_language,
            verbose=settings.log_level == "DEBUG",
        )

        logger.info("LlamaCloudParser initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def parse(self, file_path: str | Path) -> ParsedDocument:
        """
        Parse a document file.

        Args:
            file_path: Path to the document file

        Returns:
            ParsedDocument with extracted text and metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Parsing document: {file_path.name}")

        # Parse using LlamaParse
        documents = self.parser.load_data(str(file_path))

        # Combine all pages/sections
        pages = [doc.text for doc in documents]
        full_text = "\n\n".join(pages)

        # Extract metadata from first document if available
        metadata = {}
        if documents and hasattr(documents[0], "metadata"):
            metadata = dict(documents[0].metadata)
        metadata["source_path"] = str(file_path)

        return ParsedDocument(
            filename=file_path.name,
            text=full_text,
            pages=pages,
            page_count=len(pages),
            metadata=metadata,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def parse_bytes(self, file_bytes: bytes, filename: str = "document.pdf") -> ParsedDocument:
        """
        Parse a document from bytes.

        Args:
            file_bytes: Document content as bytes
            filename: Name to assign to the document

        Returns:
            ParsedDocument with extracted text and metadata
        """
        logger.info(f"Parsing document from bytes: {filename}")

        # LlamaParse can handle bytes directly with extra_info
        documents = self.parser.load_data(
            file_bytes,
            extra_info={"file_name": filename},
        )

        pages = [doc.text for doc in documents]
        full_text = "\n\n".join(pages)

        metadata = {"source": "bytes", "filename": filename}
        if documents and hasattr(documents[0], "metadata"):
            metadata.update(dict(documents[0].metadata))

        return ParsedDocument(
            filename=filename,
            text=full_text,
            pages=pages,
            page_count=len(pages),
            metadata=metadata,
        )

    def parse_multiple(self, file_paths: list[str | Path]) -> list[ParsedDocument]:
        """
        Parse multiple documents.

        Args:
            file_paths: List of paths to document files

        Returns:
            List of ParsedDocument objects
        """
        results = []
        for path in file_paths:
            try:
                doc = self.parse(path)
                results.append(doc)
            except Exception as e:
                logger.error(f"Failed to parse {path}: {e}")
                raise

        return results
