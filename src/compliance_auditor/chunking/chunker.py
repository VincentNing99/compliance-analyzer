"""
Document Chunker module - Split documents into smaller pieces.

Chunks documents with configurable size and overlap to prepare
them for embedding and vector storage.
"""

import logging
from dataclasses import dataclass, field

from compliance_auditor.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk from a document."""

    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict = field(default_factory=dict)


class DocumentChunker:
    """
    Splits documents into overlapping chunks.

    Overlap ensures that context isn't lost at chunk boundaries.
    """

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        """
        Initialize the chunker.

        Args:
            chunk_size: Characters per chunk (default from config)
            chunk_overlap: Overlap between chunks (default from config)
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size

            # Don't cut in the middle of a word - find the last space
            if end < len(text):
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        start_char=start,
                        end_char=end,
                        metadata={**metadata, "chunk_index": chunk_index},
                    )
                )
                chunk_index += 1

            # Move start position, accounting for overlap
            start = end - self.chunk_overlap
            if start <= chunks[-1].start_char if chunks else 0:
                # Prevent infinite loop if overlap is too large
                start = end

        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks

    def chunk_document(
        self, text: str, filename: str, doc_type: str = "unknown"
    ) -> list[Chunk]:
        """
        Chunk a document with filename metadata.

        Args:
            text: Document text
            filename: Source filename
            doc_type: Type of document (regulation, company_doc)

        Returns:
            List of Chunk objects with document metadata
        """
        return self.chunk(
            text,
            metadata={
                "filename": filename,
                "doc_type": doc_type,
            },
        )
