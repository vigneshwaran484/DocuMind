"""
routers/documents.py – Document management endpoints
GET    /api/documents         – List current user's indexed documents
DELETE /api/documents/{doc_id} – Remove a document entry
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.vectorstore import list_documents, delete_document
from backend.auth import get_current_user

router = APIRouter()


@router.get("/documents")
async def get_documents(user=Depends(get_current_user)):
    docs = list_documents(user.id)
    return {"success": True, "documents": docs, "total": len(docs)}


@router.delete("/documents/{doc_id}")
async def remove_document(doc_id: str, user=Depends(get_current_user)):
    success = delete_document(doc_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return {"success": True, "message": f"Document '{doc_id}' removed."}
