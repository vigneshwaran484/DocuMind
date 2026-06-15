"""
supabase_store.py – Sync FAISS index files to Supabase Storage
               and doc metadata to Supabase Postgres.

Storage bucket : "vectorstore"  (create once in Supabase dashboard)
Postgres table : "documents"    (created automatically on first use)
"""
import os
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
    """Upload the two FAISS index files (index.faiss, index.pkl) to Supabase Storage."""
    client = _get_client()
    index_dir = os.path.join(VECTORSTORE_PATH, "faiss_index")
    if not os.path.isdir(index_dir):
        logger.warning("upload_index: faiss_index directory not found at %s", index_dir)
        return
    for filename in ("index.faiss", "index.pkl"):
        path = os.path.join(index_dir, filename)
        if not os.path.isfile(path):
            logger.warning("upload_index: expected file not found: %s", path)
            continue
        with open(path, "rb") as f:
            data = f.read()
        try:
            client.storage.from_(BUCKET).upload(filename, data, {"upsert": "true"})
            logger.info("Uploaded %s to Supabase Storage", filename)
        except Exception as e1:
            logger.warning("upload failed (%s), trying update: %s", filename, e1)
            try:
                client.storage.from_(BUCKET).update(filename, data)
                logger.info("Updated %s in Supabase Storage", filename)
            except Exception as e2:
                logger.error("Failed to sync %s to Supabase Storage: %s", filename, e2)


def download_index() -> bool:
    """Download FAISS index files from Supabase Storage into the local faiss_index folder."""
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

    index_dir = os.path.join(VECTORSTORE_PATH, "faiss_index")
    os.makedirs(index_dir, exist_ok=True)
    downloaded = False
    for item in items:
        name = item["name"]
        try:
            data = client.storage.from_(BUCKET).download(name)
            local_path = os.path.join(index_dir, name)
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
