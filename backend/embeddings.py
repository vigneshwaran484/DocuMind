"""
embeddings.py – Singleton HuggingFace embedding wrapper for LangChain
"""
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from backend.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Load and cache the HuggingFace sentence-transformers model.
    Downloaded on first call, cached in memory afterward.
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
