"""
vectorstore.py – FAISS vector store management
Handles: create, add documents, persist, load, list, delete by doc_id
Persistence: Supabase Storage (FAISS index) + Supabase Postgres (metadata)
"""
import os
from typing import List, Optional, Dict

from langchain.schema import Document
from langchain_community.vectorstores import FAISS

from backend.config import VECTORSTORE_PATH
from backend.embeddings import get_embeddings
import backend.supabase_store as supa

FAISS_INDEX_FILE = os.path.join(VECTORSTORE_PATH, "faiss_index")

_vectorstore: Optional[FAISS] = None


def load_vectorstore() -> Optional[FAISS]:
    """Load FAISS index — from memory, local disk, or Supabase (in that order)."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    # Try local disk first (already downloaded this session)
    if os.path.exists(FAISS_INDEX_FILE):
        _vectorstore = FAISS.load_local(
            FAISS_INDEX_FILE,
            get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        return _vectorstore

    # Try fetching from Supabase
    try:
        if supa.download_index():
            _vectorstore = FAISS.load_local(
                FAISS_INDEX_FILE,
                get_embeddings(),
                allow_dangerous_deserialization=True,
            )
    except Exception:
        pass

    return _vectorstore


def get_vectorstore() -> Optional[FAISS]:
    return load_vectorstore()


def add_documents(docs: List[Document], doc_id: str, filename: str) -> None:
    """Add chunked documents to FAISS, persist locally, then sync to Supabase."""
    global _vectorstore
    embeddings = get_embeddings()

    if _vectorstore is None:
        _vectorstore = FAISS.from_documents(docs, embeddings)
    else:
        _vectorstore.add_documents(docs)

    _vectorstore.save_local(FAISS_INDEX_FILE)

    # Sync to Supabase — upsert with ready=True only after everything succeeds
    supa.upload_index()
    supa.upsert_document(doc_id, filename, len(docs), ready=True)


def list_documents() -> List[Dict]:
    """Return list of indexed documents from Supabase Postgres."""
    try:
        return supa.fetch_documents()
    except Exception:
        return []


def delete_document(doc_id: str) -> bool:
    try:
        supa.remove_document(doc_id)
        return True
    except Exception:
        return False


def index_exists() -> bool:
    return load_vectorstore() is not None
