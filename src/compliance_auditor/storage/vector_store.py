"""
Vector Store module - ChromaDB operations for document storage and retrieval.

Stores document embeddings and enables fast similarity search.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from compliance_auditor.config import get_settings

logger = logging.getLogger(__name__)

# Collection names
REGULATIONS_COLLECTION = "regulations"
COMPANY_DOCS_COLLECTION = "company_docs"


@dataclass
class SearchResult:
    """Represents a search result from the vector store."""

    text: str
    score: float
    metadata: dict
    doc_id: str


class VectorStore:
    """
    ChromaDB-based vector storage for document embeddings.

    Maintains two collections:
    - regulations: Regulatory documents (GDPR, HIPAA, etc.)
    - company_docs: Company policies to check for compliance
    """

    def __init__(self, persist_directory: str | None = None):
        """
        Initialize the vector store.

        Args:
            persist_directory: Where to store the database (default from config)
        """
        settings = get_settings()
        persist_dir = persist_directory or settings.chroma_persist_directory

        # Ensure directory exists
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collections
        self.regulations = self.client.get_or_create_collection(
            name=REGULATIONS_COLLECTION,
            metadata={"description": "Regulatory documents"},
        )
        self.company_docs = self.client.get_or_create_collection(
            name=COMPANY_DOCS_COLLECTION,
            metadata={"description": "Company policy documents"},
        )

        logger.info(f"VectorStore initialized at {persist_dir}")

    def _get_collection(self, doc_type: str) -> chromadb.Collection:
        """Get the appropriate collection for a document type."""
        if doc_type == "regulation":
            return self.regulations
        elif doc_type == "company_doc":
            return self.company_docs
        else:
            raise ValueError(f"Unknown doc_type: {doc_type}")

    def add_document(
        self,
        doc_id: str,
        doc_type: str,
        chunks: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> None:
        """
        Add a document's chunks to the vector store.

        Args:
            doc_id: Unique identifier for the document
            doc_type: Type of document ("regulation" or "company_doc")
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts for each chunk
        """
        collection = self._get_collection(doc_type)

        # Generate unique IDs for each chunk
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

        # Add doc_id to metadata
        if metadatas is None:
            metadatas = [{"doc_id": doc_id} for _ in chunks]
        else:
            for m in metadatas:
                m["doc_id"] = doc_id

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        logger.info(f"Added {len(chunks)} chunks for document '{doc_id}' to {doc_type}")

    def search(
        self,
        query_embedding: list[float],
        doc_type: str,
        top_k: int = 5,
        filter_doc_id: str | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector
            doc_type: Collection to search ("regulation" or "company_doc")
            top_k: Number of results to return
            filter_doc_id: Optional filter to search only within a specific document

        Returns:
            List of SearchResult objects
        """
        collection = self._get_collection(doc_type)

        where_filter = {"doc_id": filter_doc_id} if filter_doc_id else None

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                search_results.append(
                    SearchResult(
                        text=doc,
                        score=1 - results["distances"][0][i],  # Convert distance to similarity
                        metadata=results["metadatas"][0][i],
                        doc_id=results["metadatas"][0][i].get("doc_id", ""),
                    )
                )

        return search_results

    def get_all_documents(self, doc_type: str) -> list[str]:
        """
        Get list of all document IDs in a collection.

        Args:
            doc_type: Collection to query

        Returns:
            List of unique document IDs
        """
        collection = self._get_collection(doc_type)
        results = collection.get(include=["metadatas"])

        doc_ids = set()
        for metadata in results["metadatas"]:
            if "doc_id" in metadata:
                doc_ids.add(metadata["doc_id"])

        return sorted(list(doc_ids))

    def delete_document(self, doc_id: str, doc_type: str) -> None:
        """
        Delete all chunks for a document.

        Args:
            doc_id: Document ID to delete
            doc_type: Collection to delete from
        """
        collection = self._get_collection(doc_type)

        # Get all chunk IDs for this document
        results = collection.get(where={"doc_id": doc_id}, include=[])

        if results["ids"]:
            collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks for document '{doc_id}'")
        else:
            logger.warning(f"No chunks found for document '{doc_id}'")

    def get_document_chunks(self, doc_id: str, doc_type: str) -> list[str]:
        """
        Get all chunks for a specific document.

        Args:
            doc_id: Document ID
            doc_type: Collection to query

        Returns:
            List of text chunks
        """
        collection = self._get_collection(doc_type)
        results = collection.get(
            where={"doc_id": doc_id},
            include=["documents"],
        )
        return results["documents"] if results["documents"] else []
