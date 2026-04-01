"""
vectorstore.py – FAISS vector store management
Handles: create, add documents, persist, load, list, delete by doc_id
"""
import os
import json
import pickle
from typing import List, Optional, Dict

from langchain.schema import Document
from langchain_community.vectorstores import FAISS

from backend.config import VECTORSTORE_PATH
from backend.embeddings import get_embeddings

FAISS_INDEX_FILE = os.path.join(VECTORSTORE_PATH, "faiss_index")
METADATA_FILE = os.path.join(VECTORSTORE_PATH, "doc_metadata.json")

_vectorstore: Optional[FAISS] = None


def _save_metadata(metadata: Dict):
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)


def _load_metadata() -> Dict:
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}


def load_vectorstore() -> Optional[FAISS]:
    """Load FAISS index from disk if it exists."""
    global _vectorstore
    if _vectorstore is None and os.path.exists(FAISS_INDEX_FILE):
        _vectorstore = FAISS.load_local(
            FAISS_INDEX_FILE,
            get_embeddings(),
            allow_dangerous_deserialization=True,
        )
    return _vectorstore


def get_vectorstore() -> Optional[FAISS]:
    return load_vectorstore()


def add_documents(docs: List[Document], doc_id: str, filename: str) -> None:
    """Add chunked documents to FAISS index and persist."""
    global _vectorstore
    embeddings = get_embeddings()

    if _vectorstore is None:
        _vectorstore = FAISS.from_documents(docs, embeddings)
    else:
        _vectorstore.add_documents(docs)

    _vectorstore.save_local(FAISS_INDEX_FILE)

    # Save metadata
    metadata = _load_metadata()
    metadata[doc_id] = {
        "filename": filename,
        "doc_id": doc_id,
        "chunk_count": len(docs),
    }
    _save_metadata(metadata)


def list_documents() -> List[Dict]:
    """Return list of indexed documents."""
    metadata = _load_metadata()
    return list(metadata.values())


def delete_document(doc_id: str) -> bool:
    """
    Remove a document from metadata.
    Note: FAISS doesn't support per-document deletion natively;
    we rebuild the index from remaining docs on next ingestion.
    """
    metadata = _load_metadata()
    if doc_id not in metadata:
        return False
    metadata.pop(doc_id)
    _save_metadata(metadata)
    return True


def index_exists() -> bool:
    return os.path.exists(FAISS_INDEX_FILE)
