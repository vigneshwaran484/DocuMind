"""
supabase_store.py – Sync FAISS index files to Supabase Storage
               and doc metadata to Supabase Postgres.

Storage bucket : "vectorstore"  (create once in Supabase dashboard)
Postgres table : "documents"    (created automatically on first use)
"""
import os
import glob as _glob
import logging
from typing import List, Dict, Optional

from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_KEY, VECTORSTORE_PATH

logger = logging.getLogger(__name__)

BUCKET = "vectorstore"
TABLE = "documents"

_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set — add them to your .env file")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client created for %s", SUPABASE_URL)
    return _client


def test_connection() -> dict:
    """Test Supabase connectivity. Returns a dict with status and details."""
    result = {"url": SUPABASE_URL or "(not set)", "db": False, "storage": False, "errors": []}
    try:
        client = _get_client()
    except RuntimeError as e:
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

def upload_index() -> None:
    """Upload every file in the local FAISS index folder to Supabase Storage."""
    client = _get_client()
    pattern = os.path.join(VECTORSTORE_PATH, "faiss_index*")
    files = _glob.glob(pattern)
    if not files:
        logger.warning("upload_index: no faiss_index files found at %s", VECTORSTORE_PATH)
        return
    for path in files:
        name = os.path.basename(path)
        with open(path, "rb") as f:
            data = f.read()
        try:
            client.storage.from_(BUCKET).upload(name, data, {"upsert": "true"})
            logger.info("Uploaded %s to Supabase Storage", name)
        except Exception as e1:
            logger.warning("upload failed (%s), trying update: %s", name, e1)
            try:
                client.storage.from_(BUCKET).update(name, data)
                logger.info("Updated %s in Supabase Storage", name)
            except Exception as e2:
                logger.error("Failed to sync %s to Supabase Storage: %s", name, e2)


def download_index() -> bool:
    """Download FAISS index files from Supabase Storage to local disk."""
    try:
        client = _get_client()
    except RuntimeError as e:
        logger.error("download_index: %s", e)
        return False
    try:
        items = client.storage.from_(BUCKET).list()
    except Exception as e:
        logger.error("download_index: failed to list bucket: %s", e)
        return False

    if not items:
        logger.info("download_index: bucket is empty — no index to restore")
        return False

    os.makedirs(VECTORSTORE_PATH, exist_ok=True)
    downloaded = False
    for item in items:
        name = item["name"]
        try:
            data = client.storage.from_(BUCKET).download(name)
            local_path = os.path.join(VECTORSTORE_PATH, name)
            with open(local_path, "wb") as f:
                f.write(data)
            logger.info("Downloaded %s from Supabase Storage", name)
            downloaded = True
        except Exception as e:
            logger.error("Failed to download %s: %s", name, e)
    return downloaded


# ── Metadata (Postgres) ───────────────────────────────────────────────────────

def _ensure_table() -> None:
    """Create the documents table if it doesn't exist via RPC (best-effort)."""
    client = _get_client()
    try:
        client.table(TABLE).select("doc_id").limit(1).execute()
    except Exception:
        pass


def upsert_document(doc_id: str, filename: str, chunk_count: int) -> None:
    client = _get_client()
    try:
        client.table(TABLE).upsert({
            "doc_id": doc_id,
            "filename": filename,
            "chunk_count": chunk_count,
        }).execute()
        logger.info("Upserted document %s (%s) into Supabase", filename, doc_id)
    except Exception as e:
        logger.error("Failed to upsert document %s: %s", filename, e)
        raise


def remove_document(doc_id: str) -> None:
    client = _get_client()
    try:
        client.table(TABLE).delete().eq("doc_id", doc_id).execute()
        logger.info("Deleted document %s from Supabase", doc_id)
    except Exception as e:
        logger.error("Failed to delete document %s: %s", doc_id, e)
        raise


def fetch_documents() -> List[Dict]:
    try:
        client = _get_client()
        res = client.table(TABLE).select("*").execute()
        logger.info("Fetched %d documents from Supabase", len(res.data or []))
        return res.data or []
    except Exception as e:
        logger.error("fetch_documents failed: %s", e)
        return []
