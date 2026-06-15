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
import backend.supabase_store as supa

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _ingest_in_background(save_path: str, filename: str, doc_id: str):
    try:
        print(f"[INGEST] Starting background ingest for {filename} doc_id={doc_id}", flush=True)
        chunks, _ = ingest_document(save_path, filename, doc_id=doc_id)
        print(f"[INGEST] Parsed {len(chunks)} chunks for {filename}", flush=True)
        add_documents(chunks, doc_id, filename)
        print(f"[INGEST] Successfully indexed {filename}", flush=True)
    except Exception as e:
        import traceback
        print(f"[INGEST ERROR] {filename}: {e}\n{traceback.format_exc()}", flush=True)
        try:
            supa.remove_document(doc_id)
        except Exception:
            pass
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

    import hashlib, time
    doc_id = hashlib.md5(f"{filename}{time.time()}".encode()).hexdigest()[:12]

    save_path = os.path.join(UPLOADS_PATH, filename)
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Pre-insert as not-ready so the sidebar shows "indexing" state
    try:
        supa.upsert_document(doc_id, filename, chunk_count=0, ready=False)
    except Exception as e:
        logger.warning("Could not pre-insert doc metadata: %s", e)

    background_tasks.add_task(_ingest_in_background, save_path, filename, doc_id)

    return JSONResponse({
        "success": True,
        "message": f"'{filename}' received and is being indexed.",
        "filename": filename,
        "doc_id": doc_id,
    })
