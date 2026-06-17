"""
supabase_store.py – Per-user Supabase Storage (FAISS) + Postgres (metadata).

Storage layout : vectorstore/{user_id}/index.faiss
                               {user_id}/index.pkl
Postgres table : documents  (doc_id, user_id, filename, chunk_count, ready, created_at)
"""
import os
import logging
from typing import List, Dict, Optional

from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, VECTORSTORE_PATH

logger = logging.getLogger(__name__)

BUCKET = "vectorstore"
TABLE = "documents"

_anon_client: Optional[Client] = None
_service_client: Optional[Client] = None


def _get_anon_client() -> Client:
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _anon_client


def _get_service_client() -> Client:
    """Service role client — bypasses RLS, used for all backend writes/reads."""
    global _service_client
    if _service_client is None:
        key = SUPABASE_SERVICE_KEY or SUPABASE_KEY
        _service_client = create_client(SUPABASE_URL, key)
    return _service_client


def test_connection() -> dict:
    result = {"url": SUPABASE_URL or "(not set)", "db": False, "storage": False, "errors": []}
    try:
        client = _get_service_client()
    except Exception as e:
        result["errors"].append(str(e))
        return result
    try:
        client.table(TABLE).select("doc_id").limit(1).execute()
        result["db"] = True
    except Exception as e:
        result["errors"].append(f"DB error: {e}")
    try:
        client.storage.from_(BUCKET).list()
        result["storage"] = True
    except Exception as e:
        result["errors"].append(f"Storage error: {e}")
    return result


# ── FAISS index sync ──────────────────────────────────────────────────────────

def _local_index_dir(user_id: str) -> str:
    path = os.path.join(VECTORSTORE_PATH, user_id, "faiss_index")
    os.makedirs(path, exist_ok=True)
    return path


def upload_index(user_id: str) -> None:
    """Upload the user's FAISS index files to Supabase Storage."""
    client = _get_service_client()
    index_dir = _local_index_dir(user_id)
    for filename in ("index.faiss", "index.pkl"):
        path = os.path.join(index_dir, filename)
        if not os.path.isfile(path):
            logger.warning("upload_index: missing %s for user %s", filename, user_id)
            continue
        with open(path, "rb") as f:
            data = f.read()
        storage_path = f"{user_id}/{filename}"
        try:
            client.storage.from_(BUCKET).upload(storage_path, data, {"upsert": "true"})
            logger.info("Uploaded %s for user %s", filename, user_id)
        except Exception as e1:
            try:
                client.storage.from_(BUCKET).update(storage_path, data)
                logger.info("Updated %s for user %s", filename, user_id)
            except Exception as e2:
                logger.error("Failed to sync %s for user %s: %s", filename, user_id, e2)


def download_index(user_id: str) -> bool:
    """Download the user's FAISS index files from Supabase Storage."""
    client = _get_service_client()
    try:
        items = client.storage.from_(BUCKET).list(user_id)
    except Exception as e:
        logger.error("download_index: failed to list %s: %s", user_id, e)
        return False

    if not items:
        logger.info("download_index: no files found for user %s", user_id)
        return False

    index_dir = _local_index_dir(user_id)
    downloaded = False
    for item in items:
        name = item["name"]
        storage_path = f"{user_id}/{name}"
        try:
            data = client.storage.from_(BUCKET).download(storage_path)
            with open(os.path.join(index_dir, name), "wb") as f:
                f.write(data)
            logger.info("Downloaded %s for user %s", name, user_id)
            downloaded = True
        except Exception as e:
            logger.error("Failed to download %s for user %s: %s", name, user_id, e)
    return downloaded


# ── Metadata (Postgres) ───────────────────────────────────────────────────────

def upsert_document(doc_id: str, filename: str, user_id: str, chunk_count: int = 0, ready: bool = False) -> None:
    client = _get_service_client()
    try:
        client.table(TABLE).upsert({
            "doc_id": doc_id,
            "user_id": user_id,
            "filename": filename,
            "chunk_count": chunk_count,
            "ready": ready,
        }).execute()
        logger.info("Upserted doc %s for user %s ready=%s", filename, user_id, ready)
    except Exception as e:
        logger.error("Failed to upsert doc %s: %s", filename, e)
        raise


def remove_document(doc_id: str, user_id: str) -> None:
    client = _get_service_client()
    try:
        client.table(TABLE).delete().eq("doc_id", doc_id).eq("user_id", user_id).execute()
        logger.info("Deleted doc %s for user %s", doc_id, user_id)
    except Exception as e:
        logger.error("Failed to delete doc %s: %s", doc_id, e)
        raise


def fetch_documents(user_id: str) -> List[Dict]:
    client = _get_service_client()
    try:
        res = client.table(TABLE).select("*").eq("user_id", user_id).execute()
        return res.data or []
    except Exception as e:
        logger.error("fetch_documents failed for user %s: %s", user_id, e)
        return []
