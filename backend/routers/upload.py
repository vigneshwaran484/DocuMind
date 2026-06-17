"""
routers/upload.py – Document upload and ingestion endpoint
POST /api/upload
"""
import os
import shutil
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from backend.config import UPLOADS_PATH
from backend.ingest import ingest_document
from backend.vectorstore import add_documents
from backend.auth import get_current_user
import backend.supabase_store as supa

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _ingest_in_background(save_path: str, filename: str, doc_id: str, user_id: str):
    try:
        print(f"[INGEST] Starting for {filename} user={user_id}", flush=True)
        chunks, _ = ingest_document(save_path, filename, doc_id=doc_id)
        print(f"[INGEST] {len(chunks)} chunks parsed for {filename}", flush=True)
        add_documents(chunks, doc_id, filename, user_id)
        print(f"[INGEST] Done: {filename} for user {user_id}", flush=True)
    except Exception as e:
        import traceback
        print(f"[INGEST ERROR] {filename}: {e}\n{traceback.format_exc()}", flush=True)
        try:
            supa.remove_document(doc_id, user_id)
        except Exception:
            pass
        if os.path.exists(save_path):
            os.remove(save_path)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    user_id = user.id
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    import hashlib, time
    doc_id = hashlib.md5(f"{user_id}{filename}{time.time()}".encode()).hexdigest()[:12]

    user_upload_dir = os.path.join(UPLOADS_PATH, user_id)
    os.makedirs(user_upload_dir, exist_ok=True)
    save_path = os.path.join(user_upload_dir, filename)

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    try:
        supa.upsert_document(doc_id, filename, user_id, chunk_count=0, ready=False)
    except Exception as e:
        print(f"[UPLOAD] Pre-insert warning: {e}", flush=True)

    background_tasks.add_task(_ingest_in_background, save_path, filename, doc_id, user_id)

    return JSONResponse({
        "success": True,
        "message": f"'{filename}' received and is being indexed.",
        "filename": filename,
        "doc_id": doc_id,
    })
