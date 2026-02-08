"""Pydantic schemas for document endpoints."""
from enum import Enum
from pydantic import BaseModel


class DocType(str, Enum):
    """Document type enum - matches internal naming in llama_cloud."""
    regulation = "regulation"      # Compliance documents (GDPR, HIPAA, etc.)
    company_doc = "company_doc"    # Internal company documents


class DocumentListResponse(BaseModel):
    """Response when listing documents."""
    documents: list[str]  # List of document IDs
    doc_type: DocType


class UploadResponse(BaseModel):
    """Response after uploading a document."""
    success: bool
    message: str
    doc_id: str | None = None


class DeleteResponse(BaseModel):
    """Response after deleting a document."""
    success: bool
    message: str
