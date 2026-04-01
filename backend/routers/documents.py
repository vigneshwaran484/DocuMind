"""
routers/documents.py – Document management endpoints
GET    /api/documents         – List all indexed documents
DELETE /api/documents/{doc_id} – Remove a document entry from metadata
"""
from fastapi import APIRouter, HTTPException
from backend.vectorstore import list_documents, delete_document

router = APIRouter()


@router.get("/documents")
async def get_documents():
    """Return a list of all indexed documents."""
    docs = list_documents()
    return {"success": True, "documents": docs, "total": len(docs)}


@router.delete("/documents/{doc_id}")
async def remove_document(doc_id: str):
    """Remove a document's metadata from the index."""
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return {"success": True, "message": f"Document '{doc_id}' removed from index."}
