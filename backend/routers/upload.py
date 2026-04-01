"""
routers/upload.py – Document upload and ingestion endpoint
POST /api/upload
"""
import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from backend.config import UPLOADS_PATH
from backend.ingest import ingest_document
from backend.vectorstore import add_documents

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document, parse it, embed it, and store in FAISS."""
    # Validate extension
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Save to disk temporarily
    save_path = os.path.join(UPLOADS_PATH, filename)
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Ingest and index
    try:
        chunks, doc_id = ingest_document(save_path, filename)
        add_documents(chunks, doc_id, filename)
    except ValueError as e:
        os.remove(save_path)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

    return JSONResponse({
        "success": True,
        "message": f"'{filename}' indexed successfully.",
        "doc_id": doc_id,
        "chunk_count": len(chunks),
        "filename": filename,
    })
