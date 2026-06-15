"""
routers/upload.py – Document upload and ingestion endpoint
POST /api/upload
"""
import os
import shutil
import logging
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from backend.config import UPLOADS_PATH
from backend.ingest import ingest_document
from backend.vectorstore import add_documents

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _ingest_in_background(save_path: str, filename: str):
    try:
        logger.info("Background ingest started for %s", filename)
        chunks, doc_id = ingest_document(save_path, filename)
        logger.info("Ingested %d chunks for %s", len(chunks), filename)
        add_documents(chunks, doc_id, filename)
        logger.info("Successfully indexed %s (doc_id=%s)", filename, doc_id)
    except Exception as e:
        logger.error("Background ingest FAILED for %s: %s", filename, e, exc_info=True)
        if os.path.exists(save_path):
            os.remove(save_path)


@router.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a document, save it, then index it in the background to avoid timeout."""
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    save_path = os.path.join(UPLOADS_PATH, filename)
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    background_tasks.add_task(_ingest_in_background, save_path, filename)

    return JSONResponse({
        "success": True,
        "message": f"'{filename}' received and is being indexed. It will appear in your document list shortly.",
        "filename": filename,
    })
