"""
LlamaCloud Index for vector storage and retrieval.

Replaces local ChromaDB with LlamaCloud's managed vector index
for document storage, embedding, and semantic search.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from llama_index.indices.managed.llama_cloud import LlamaCloudIndex as LlamaIndex
from llama_index.core.schema import Document
from llama_index.llms.gemini import Gemini
from llama_index.core.llms import ChatMessage, MessageRole
from tenacity import retry, stop_after_attempt, wait_exponential

from compliance_auditor.config import get_settings
from compliance_auditor.llama_cloud.parser import ParsedDocument

logger = logging.getLogger(__name__)

# Global Gemini LLM instance
_gemini_llm = None


def get_gemini_llm() -> Gemini:
    """Get or create the Gemini LLM instance."""
    global _gemini_llm
    if _gemini_llm is None:
        settings = get_settings()
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        _gemini_llm = Gemini(model="gemini-2.5-flash", api_key=settings.google_api_key)
        logger.info("Gemini LLM initialized")
    return _gemini_llm


def chat_with_context(
    message: str,
    compliance_context: str,
    internal_context: str,
    chat_history: list[dict] | None = None,
) -> str:
    """
    Send a message to Gemini with document context.

    Args:
        message: User's message
        compliance_context: Retrieved content from compliance documents
        internal_context: Retrieved content from internal documents
        chat_history: Previous chat messages [{"role": "user/assistant", "content": "..."}]

    Returns:
        Assistant's response text
    """
    llm = get_gemini_llm()

    system_prompt = f"""You are a compliance analysis assistant. Your role is to:
1. Analyze internal requirement documents against compliance regulations
2. Identify compliance gaps and issues
3. Provide specific recommendations for achieving compliance

## COMPLIANCE DOCUMENTS:
{compliance_context if compliance_context else "No compliance documents selected."}

## INTERNAL REQUIREMENT DOCUMENTS:
{internal_context if internal_context else "No internal documents selected."}

When answering questions:
- Compare the internal documents against the compliance documents
- Reference specific sections from both document types
- Clearly state compliance status (Compliant / Partially Compliant / Non-Compliant)
- Identify specific gaps between internal requirements and compliance regulations
- Provide actionable recommendations
- If the user greets you or asks something unrelated, respond naturally but guide them back to compliance analysis"""

    # Build messages list
    messages = [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)]

    # Add chat history if provided
    if chat_history:
        for msg in chat_history:
            role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
            messages.append(ChatMessage(role=role, content=msg["content"]))

    # Add current user message
    messages.append(ChatMessage(role=MessageRole.USER, content=message))

    # Call Gemini
    response = llm.chat(messages)
    return response.message.content


def stream_chat_with_context(
    message: str,
    compliance_context: str,
    internal_context: str,
    chat_history: list[dict] | None = None,
):
    """
    Stream a chat response from Gemini with document context.

    Args:
        message: User's message
        compliance_context: Retrieved content from compliance documents
        internal_context: Retrieved content from internal documents
        chat_history: Previous chat messages

    Yields:
        Tokens from the response
    """
    llm = get_gemini_llm()

    system_prompt = f"""You are a compliance analysis assistant. Your role is to:
1. Analyze internal requirement documents against compliance regulations
2. Identify compliance gaps and issues
3. Provide specific recommendations for achieving compliance

## COMPLIANCE DOCUMENTS:
{compliance_context if compliance_context else "No compliance documents selected."}

## INTERNAL REQUIREMENT DOCUMENTS:
{internal_context if internal_context else "No internal documents selected."}

When answering questions:
- Compare the internal documents against the compliance documents
- Reference specific sections from both document types
- Clearly state compliance status (Compliant / Partially Compliant / Non-Compliant)
- Identify specific gaps between internal requirements and compliance regulations
- Provide actionable recommendations
- If the user greets you or asks something unrelated, respond naturally but guide them back to compliance analysis"""

    # Build messages list
    messages = [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)]

    # Add chat history if provided
    if chat_history:
        for msg in chat_history:
            role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
            messages.append(ChatMessage(role=role, content=msg["content"]))

    # Add current user message
    messages.append(ChatMessage(role=MessageRole.USER, content=message))

    # Stream response from Gemini
    response_stream = llm.stream_chat(messages)
    for chunk in response_stream:
        yield chunk.delta


# Index name suffixes for different document types
REGULATIONS_INDEX_SUFFIX = "-regulations"
COMPANY_DOCS_INDEX_SUFFIX = "-company-docs"


@dataclass
class SearchResult:
    """Represents a search result from the LlamaCloud index."""

    text: str
    score: float
    metadata: dict
    doc_id: str


class LlamaCloudIndex:
    """
    LlamaCloud-based vector storage for document embeddings.

    Maintains two indexes:
    - regulations: Regulatory documents (GDPR, HIPAA, etc.)
    - company_docs: Company policies to check for compliance

    LlamaCloud handles embedding generation and vector storage automatically.
    """

    def __init__(self):
        """Initialize the LlamaCloud index connections."""
        settings = get_settings()

        self.base_index_name = settings.llama_cloud_index_name
        self.project_name = settings.llama_cloud_project_name
        self.api_key = settings.llama_cloud_api_key

        # Set environment variable for LlamaCloud
        os.environ["LLAMA_CLOUD_API_KEY"] = self.api_key

        # Index names for different document types
        self.regulations_index_name = f"{self.base_index_name}{REGULATIONS_INDEX_SUFFIX}"
        self.company_docs_index_name = f"{self.base_index_name}{COMPANY_DOCS_INDEX_SUFFIX}"

        # Cache for index instances
        self._indexes: dict[str, LlamaIndex] = {}

        logger.info(
            f"LlamaCloudIndex initialized with base name: {self.base_index_name}"
        )

    def _get_index_name(self, doc_type: str) -> str:
        """Get the index name for a document type."""
        if doc_type == "regulation":
            return self.regulations_index_name
        elif doc_type == "company_doc":
            return self.company_docs_index_name
        else:
            raise ValueError(f"Unknown doc_type: {doc_type}")

    def _get_or_create_index(self, doc_type: str, document: Document | None = None) -> tuple[LlamaIndex, bool]:
        """
        Get or create a LlamaCloud index for the given document type.

        Args:
            doc_type: Type of documents ("regulation" or "company_doc")
            document: Optional document to create index with (required if index doesn't exist)

        Returns:
            Tuple of (LlamaCloudIndex instance, was_created)
            was_created is True if a new index was created with the document
        """
        index_name = self._get_index_name(doc_type)

        # Return cached index if available
        if index_name in self._indexes:
            return self._indexes[index_name], False

        # Try to connect to existing index, or create new one
        was_created = False
        try:
            index = LlamaIndex(
                name=index_name,
                project_name=self.project_name,
                api_key=self.api_key,
            )
            logger.info(f"Connected to existing index: {index_name}")
        except ValueError as e:
            if "Unknown index name" in str(e):
                # Index doesn't exist - create it
                if document is None:
                    raise ValueError(
                        f"Index '{index_name}' doesn't exist. "
                        "Please upload a document to create the index."
                    )
                logger.info(f"Creating new index: {index_name}")
                index = LlamaIndex.from_documents(
                    documents=[document],
                    name=index_name,
                    project_name=self.project_name,
                    api_key=self.api_key,
                )
                was_created = True
                logger.info(f"Created new index: {index_name}")
            else:
                raise

        # Cache the index
        self._indexes[index_name] = index
        return index, was_created

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def add_document(
        self,
        doc_id: str,
        doc_type: str,
        parsed_doc: ParsedDocument,
    ) -> None:
        """
        Add a parsed document to the LlamaCloud index.

        LlamaCloud handles chunking and embedding automatically.

        Args:
            doc_id: Unique identifier for the document
            doc_type: Type of document ("regulation" or "company_doc")
            parsed_doc: ParsedDocument from LlamaCloudParser
        """
        # Create a Document with metadata
        metadata = {
            "doc_id": doc_id,
            "doc_type": doc_type,
            "filename": parsed_doc.filename,
            "page_count": parsed_doc.page_count,
            **parsed_doc.metadata,
        }

        document = Document(
            text=parsed_doc.text,
            metadata=metadata,
            doc_id=doc_id,
        )

        # Get or create index (pass document in case index needs to be created)
        index, was_created = self._get_or_create_index(doc_type, document=document)

        # Only insert if index already existed
        if not was_created:
            index.insert(document)

        logger.info(
            f"Added document '{doc_id}' ({parsed_doc.filename}) to {doc_type} index"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def add_document_from_file(
        self,
        file_path: str | Path,
        doc_id: str,
        doc_type: str,
    ) -> None:
        """
        Add a document file to the index.

        Uses LlamaParse to extract text, then inserts into LlamaCloud index.

        Args:
            file_path: Path to the document file
            doc_id: Unique identifier for the document
            doc_type: Type of document ("regulation" or "company_doc")
        """
        from compliance_auditor.llama_cloud.parser import LlamaCloudParser

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Parse the document using LlamaParse
        parser = LlamaCloudParser()
        parsed_doc = parser.parse(file_path)

        # Create a Document for the index
        document = Document(
            text=parsed_doc.text,
            metadata={
                "doc_id": doc_id,
                "doc_type": doc_type,
                "filename": parsed_doc.filename,
                "page_count": parsed_doc.page_count,
            },
            doc_id=doc_id,
        )

        # Get or create index (pass document in case index needs to be created)
        index, was_created = self._get_or_create_index(doc_type, document=document)

        # Only insert if index already existed (from_documents already added the doc)
        if not was_created:
            index.insert(document)

        logger.info(f"Added file '{file_path.name}' as '{doc_id}' to {doc_type} index")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def search(
        self,
        query: str,
        doc_type: str,
        top_k: int = 5,
        filter_doc_id: str | None = None,
    ) -> list[SearchResult]:
        """
        Search for relevant chunks using semantic search.

        Args:
            query: Search query text
            doc_type: Collection to search ("regulation" or "company_doc")
            top_k: Number of results to return
            filter_doc_id: Optional filter to search only within a specific document

        Returns:
            List of SearchResult objects
        """
        index, _ = self._get_or_create_index(doc_type)

        # Build retriever with filters
        retriever = index.as_retriever(similarity_top_k=top_k)

        # Execute query
        nodes = retriever.retrieve(query)

        search_results = []
        for node in nodes:
            # Apply doc_id filter if specified
            if filter_doc_id:
                node_doc_id = node.metadata.get("doc_id", "")
                if node_doc_id != filter_doc_id:
                    continue

            search_results.append(
                SearchResult(
                    text=node.text,
                    score=node.score if node.score else 0.0,
                    metadata=dict(node.metadata) if node.metadata else {},
                    doc_id=node.metadata.get("doc_id", "") if node.metadata else "",
                )
            )

        return search_results[:top_k]

    def get_all_documents(self, doc_type: str) -> list[str]:
        """
        Get list of all document IDs in an index.

        Args:
            doc_type: Index to query

        Returns:
            List of unique document IDs
        """
        try:
            index, _ = self._get_or_create_index(doc_type)

            # Get all nodes and extract unique doc_ids
            doc_ids = set()

            # Query with a generic prompt to get all documents
            retriever = index.as_retriever(similarity_top_k=100)
            nodes = retriever.retrieve("list all documents")

            for node in nodes:
                if node.metadata and "doc_id" in node.metadata:
                    doc_ids.add(node.metadata["doc_id"])

            return sorted(list(doc_ids))
        except Exception as e:
            logger.warning(f"Could not retrieve all documents: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def delete_document(self, doc_id: str, doc_type: str) -> None:
        """
        Delete all data for a document from the index.

        Args:
            doc_id: Document ID to delete
            doc_type: Index to delete from
        """
        index, _ = self._get_or_create_index(doc_type)

        # Delete by doc_id
        index.delete_ref_doc(doc_id)

        logger.info(f"Deleted document '{doc_id}' from {doc_type} index")

    def as_query_engine(self, doc_type: str, **kwargs):
        """
        Get a query engine for RAG-style queries using Gemini LLM.

        Args:
            doc_type: Index to query
            **kwargs: Additional arguments passed to as_query_engine

        Returns:
            LlamaIndex query engine with Gemini LLM
        """
        index, _ = self._get_or_create_index(doc_type)
        llm = get_gemini_llm()
        return index.as_query_engine(llm=llm, **kwargs)

    def as_chat_engine(self, doc_type: str, **kwargs):
        """
        Get a chat engine for conversational RAG using Gemini LLM.

        Args:
            doc_type: Index to query
            **kwargs: Additional arguments passed to as_chat_engine

        Returns:
            LlamaIndex chat engine with Gemini LLM
        """
        index, _ = self._get_or_create_index(doc_type)
        llm = get_gemini_llm()
        return index.as_chat_engine(llm=llm, **kwargs)