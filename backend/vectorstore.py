"""
vectorstore.py – Per-user FAISS vector store management.
Each user has their own isolated FAISS index stored in Supabase Storage.
"""
import os
from typing import List, Optional, Dict

from langchain.schema import Document
from langchain_community.vectorstores import FAISS

from backend.config import VECTORSTORE_PATH
from backend.embeddings import get_embeddings
import backend.supabase_store as supa

# In-memory cache: user_id -> FAISS instance
_stores: Dict[str, FAISS] = {}


def _local_index_path(user_id: str) -> str:
    return os.path.join(VECTORSTORE_PATH, user_id, "faiss_index")


def load_vectorstore(user_id: str) -> Optional[FAISS]:
    """Load FAISS for a user — from memory, local disk, or Supabase."""
    if user_id in _stores:
        return _stores[user_id]

    local_path = _local_index_path(user_id)

    if os.path.exists(local_path):
        try:
            _stores[user_id] = FAISS.load_local(
                local_path, get_embeddings(), allow_dangerous_deserialization=True
            )
            return _stores[user_id]
        except Exception as e:
            print(f"[VS] Failed to load local index for {user_id}: {e}", flush=True)

    try:
        if supa.download_index(user_id):
            _stores[user_id] = FAISS.load_local(
                local_path, get_embeddings(), allow_dangerous_deserialization=True
            )
            return _stores[user_id]
    except Exception as e:
        print(f"[VS] Failed to download index for {user_id}: {e}", flush=True)

    return None


def get_vectorstore(user_id: str) -> Optional[FAISS]:
    return load_vectorstore(user_id)


def add_documents(docs: List[Document], doc_id: str, filename: str, user_id: str) -> None:
    """Embed and index documents for a user, then persist to Supabase."""
    embeddings = get_embeddings()

    if user_id in _stores:
        _stores[user_id].add_documents(docs)
    else:
        _stores[user_id] = FAISS.from_documents(docs, embeddings)

    local_path = _local_index_path(user_id)
    _stores[user_id].save_local(local_path)

    supa.upload_index(user_id)
    supa.upsert_document(doc_id, filename, user_id, chunk_count=len(docs), ready=True)


def list_documents(user_id: str) -> List[Dict]:
    try:
        return supa.fetch_documents(user_id)
    except Exception:
        return []


def delete_document(doc_id: str, user_id: str) -> bool:
    try:
        supa.remove_document(doc_id, user_id)
        return True
    except Exception:
        return False


def index_exists(user_id: str) -> bool:
    return get_vectorstore(user_id) is not None
