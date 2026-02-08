"""Document management API routes."""
import tempfile
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Query, HTTPException

from ..schemas import DocType, DocumentListResponse, UploadResponse, DeleteResponse
from ..services import get_document_list, upload_document, delete_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    type: DocType = Query(..., description="Document type: 'regulation' or 'company_doc'")
):
    """
    List all documents of a given type.

    - **type**: Either 'regulation' (compliance docs) or 'company_doc' (internal docs)

    Returns list of document IDs.
    """
    docs = get_document_list(type.value)
    return DocumentListResponse(documents=docs, doc_type=type)


@router.post("", response_model=UploadResponse)
async def upload_document_endpoint(
    file: UploadFile = File(..., description="Document file to upload"),
    type: DocType = Query(..., description="Document type: 'regulation' or 'company_doc'")
):
    """
    Upload and index a document.

    - **file**: PDF, DOCX, DOC, TXT, or PPTX file
    - **type**: Either 'regulation' (compliance docs) or 'company_doc' (internal docs)

    The document will be parsed and added to the vector index for search.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Save uploaded file to temp location
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        # Use original filename for doc_id
        original_path = Path(file.filename)
        tmp_path_with_name = tmp_path.parent / original_path.name
        tmp_path.rename(tmp_path_with_name)

        success, message, doc_id = upload_document(tmp_path_with_name, type.value)

        if not success:
            raise HTTPException(status_code=500, detail=message)

        return UploadResponse(success=success, message=message, doc_id=doc_id)

    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        if tmp_path_with_name.exists():
            tmp_path_with_name.unlink(missing_ok=True)


@router.delete("/{doc_id}", response_model=DeleteResponse)
async def delete_document_endpoint(
    doc_id: str,
    type: DocType = Query(..., description="Document type: 'regulation' or 'company_doc'")
):
    """
    Delete a document from the index.

    - **doc_id**: The document ID to delete (usually the filename without extension)
    - **type**: Either 'regulation' (compliance docs) or 'company_doc' (internal docs)
    """
    success, message = delete_document(doc_id, type.value)

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return DeleteResponse(success=success, message=message)
