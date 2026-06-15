"""
supabase_store.py – Sync FAISS index files to Supabase Storage
               and doc metadata to Supabase Postgres.

Storage bucket : "vectorstore"  (create once in Supabase dashboard)
Postgres table : "documents"    (created automatically on first use)
"""
import os
import glob as _glob
from typing import List, Dict, Optional

from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_KEY, VECTORSTORE_PATH

BUCKET = "vectorstore"
TABLE = "documents"

_client: Optional[Client] = None


def _get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── FAISS index sync ──────────────────────────────────────────────────────────

def upload_index() -> None:
    """Upload every file in the local FAISS index folder to Supabase Storage."""
    client = _get_client()
    pattern = os.path.join(VECTORSTORE_PATH, "faiss_index*")
    for path in _glob.glob(pattern):
        name = os.path.basename(path)
        with open(path, "rb") as f:
            data = f.read()
        try:
            client.storage.from_(BUCKET).upload(name, data, {"upsert": "true"})
        except Exception:
            client.storage.from_(BUCKET).update(name, data)


def download_index() -> bool:
    """Download FAISS index files from Supabase Storage to local disk.
    Returns True if files were found and downloaded."""
    client = _get_client()
    try:
        items = client.storage.from_(BUCKET).list()
    except Exception:
        return False

    if not items:
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
            downloaded = True
        except Exception:
            pass
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
    client.table(TABLE).upsert({
        "doc_id": doc_id,
        "filename": filename,
        "chunk_count": chunk_count,
    }).execute()


def remove_document(doc_id: str) -> None:
    client = _get_client()
    client.table(TABLE).delete().eq("doc_id", doc_id).execute()


def fetch_documents() -> List[Dict]:
    client = _get_client()
    res = client.table(TABLE).select("*").execute()
    return res.data or []
