"""
config.py – Centralised configuration loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K: int = int(os.getenv("TOP_K", "4"))
VECTORSTORE_PATH: str = os.getenv("VECTORSTORE_PATH", "./vectorstore")
UPLOADS_PATH: str = os.getenv("UPLOADS_PATH", "./uploads")

# Ensure directories exist
os.makedirs(VECTORSTORE_PATH, exist_ok=True)
os.makedirs(UPLOADS_PATH, exist_ok=True)
