"""
Shared business logic for the Compliance Auditor API.

This module contains the core functionality that was previously in app.py,
now extracted so it can be used by the FastAPI routes.
"""
import logging
from pathlib import Path
from typing import Generator
from functools import lru_cache

from llama_index.llms.gemini import Gemini
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator

from compliance_auditor.config import get_settings
from compliance_auditor.llama_cloud import LlamaCloudParser, LlamaCloudIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Singleton Instances
# =============================================================================

@lru_cache
def get_parser() -> LlamaCloudParser:
    """Get singleton parser instance."""
    return LlamaCloudParser()


@lru_cache
def get_index() -> LlamaCloudIndex:
    """Get singleton index instance."""
    return LlamaCloudIndex()


# =============================================================================
# Document Operations
# =============================================================================

def get_document_list(doc_type: str) -> list[str]:
    """
    Get list of document IDs for a given type.

    Args:
        doc_type: "regulation" or "company_doc"

    Returns:
        List of document IDs
    """
    try:
        index = get_index()
        docs = index.get_all_documents(doc_type)
        return docs if docs else []
    except Exception:
        logger.exception("Error getting document list")
        return []


def upload_document(file_path: Path, doc_type: str) -> tuple[bool, str, str | None]:
    """
    Upload and index a document.

    Args:
        file_path: Path to the uploaded file
        doc_type: "regulation" or "company_doc"

    Returns:
        Tuple of (success, message, doc_id or None)
    """
    try:
        doc_id = file_path.stem
        index = get_index()
        index.add_document_from_file(file_path, doc_id, doc_type)
        return True, f"Uploaded '{doc_id}' successfully", doc_id
    except Exception as e:
        logger.exception("Error uploading document")
        return False, f"Error: {str(e)}", None


def delete_document(doc_id: str, doc_type: str) -> tuple[bool, str]:
    """
    Delete a document from the index.

    Args:
        doc_id: Document ID to delete
        doc_type: "regulation" or "company_doc"

    Returns:
        Tuple of (success, message)
    """
    try:
        index = get_index()
        index.delete_document(doc_id, doc_type)
        return True, f"Deleted '{doc_id}'"
    except Exception as e:
        logger.exception("Error deleting document")
        return False, f"Error: {str(e)}"


# =============================================================================
# Document Retrieval & Analysis
# =============================================================================

def retrieve_document_context_with_status(
    selected_compliance: list[str],
    selected_internal: list[str],
    user_query: str | None = None
) -> Generator[tuple[str, dict], None, None]:
    """
    Multi-step retrieval with status updates.

    This is the core analysis function that:
    1. Retrieves all content from selected internal documents
    2. Extracts requirements from those documents using Gemini LLM
    3. Queries the compliance index for each requirement using hybrid search

    Args:
        selected_compliance: List of selected compliance document IDs
        selected_internal: List of selected internal document IDs
        user_query: Optional user query for context

    Yields:
        Tuple of (status_message, partial_result_dict)
    """
    settings = get_settings()
    index = get_index()
    gemini_llm = Gemini(model="gemini-3-pro-preview", api_key=settings.google_api_key)

    result = {
        "internal_content": "",
        "compliance_results": [],
        "requirements": [],
    }

    # Step 1: Get FULL content from internal documents
    if selected_internal:
        yield "**Step 1/3:** Retrieving internal documents...", result
        try:
            company_docs_index, _ = index._get_or_create_index("company_doc")
            internal_filters = MetadataFilters(
                filters=[
                    MetadataFilter(
                        key="doc_id",
                        operator=FilterOperator.IN,
                        value=selected_internal
                    )
                ]
            )
            retriever = company_docs_index.as_retriever(
                similarity_top_k=100,  # LlamaCloud max is 100
                filters=internal_filters,
            )
            nodes = retriever.retrieve("Return all content from documents")
            result["internal_content"] = "\n\n".join([node.text for node in nodes])
            logger.info(f"Retrieved {len(nodes)} chunks from internal docs")
            yield f"**Step 1/3:** Retrieved {len(nodes)} chunks from internal documents", result
        except Exception as e:
            logger.error(f"Error retrieving internal docs: {e}")
            result["internal_content"] = f"Error retrieving internal documents: {e}"
            yield f"**Error:** {e}", result

    # Step 2: Extract requirements from internal documents
    if result["internal_content"] and selected_compliance:
        yield "**Step 2/3:** Extracting requirements from internal documents...", result
        try:
            extraction_prompt = f"""Extract all specific requirements, policies, or procedures from this document.

IMPORTANT RULES:
- Extract each requirement EXACTLY as written - do NOT summarize or shorten
- Preserve all details, conditions, and qualifications
- Return as a numbered list, one requirement per line

Document:
{result["internal_content"][:8000]}

Requirements (verbatim, complete sentences):"""

            logger.info("Extracting requirements from internal docs...")
            extraction_response = gemini_llm.complete(extraction_prompt)
            requirements_text = str(extraction_response)

            requirements = []
            for line in requirements_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    clean_req = line.lstrip('0123456789.-) ').strip()
                    if clean_req:
                        requirements.append(clean_req)

            result["requirements"] = requirements
            logger.info(f"Extracted {len(requirements)} requirements")

            # Show extracted requirements
            req_list = "\n".join([
                f"  {i+1}. {req[:80]}{'...' if len(req) > 80 else ''}"
                for i, req in enumerate(requirements)
            ])
            yield f"**Step 2/3:** Extracted {len(requirements)} requirements:\n{req_list}", result

            # Step 3: Query compliance index for each requirement
            if requirements:
                regulations_index, _ = index._get_or_create_index("regulation")
                compliance_filters = MetadataFilters(
                    filters=[
                        MetadataFilter(
                            key="doc_id",
                            operator=FilterOperator.IN,
                            value=selected_compliance
                        )
                    ]
                )
                # Use hybrid search (dense + sparse) with reranking
                compliance_retriever = regulations_index.as_retriever(
                    dense_similarity_top_k=5,
                    sparse_similarity_top_k=5,
                    alpha=0.5,
                    enable_reranking=True,
                    rerank_top_n=3,
                    filters=compliance_filters,
                )

                for i, req in enumerate(requirements):
                    try:
                        yield (
                            f"**Step 3/3:** Querying compliance for requirement "
                            f"{i+1}/{len(requirements)}...\n\n**Requirement:** {req}",
                            result
                        )
                        logger.info(f"Querying compliance for requirement {i+1}: {req[:50]}...")

                        nodes = compliance_retriever.retrieve(req)

                        if nodes:
                            compliance_info = "\n\n".join([
                                f"**[{node.metadata.get('doc_id', 'Unknown')}]** "
                                f"(score: {node.score:.2f})\n{node.text}"
                                for node in nodes
                            ])
                        else:
                            compliance_info = "No matching regulations found."

                        result["compliance_results"].append({
                            "requirement": req,
                            "compliance_info": compliance_info
                        })

                        yield (
                            f"**Step 3/3:** Requirement {i+1}/{len(requirements)} complete\n\n"
                            f"**Requirement:** {req}\n\n"
                            f"**Compliance Result:**\n{compliance_info[:500]}"
                            f"{'...' if len(compliance_info) > 500 else ''}",
                            result
                        )
                    except Exception as e:
                        logger.error(f"Error querying compliance for requirement: {e}")
                        result["compliance_results"].append({
                            "requirement": req,
                            "compliance_info": f"Error querying compliance: {e}"
                        })
                        yield f"**Step 3/3:** Requirement {i+1} - Error: {e}", result

        except Exception as e:
            logger.error(f"Error in requirement extraction/compliance query: {e}")
            yield f"**Error:** {e}", result

    yield "**Complete:** Analysis ready", result
