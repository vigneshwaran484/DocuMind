"""
ingest.py – Document parsing and chunking
Supports: PDF (.pdf), Word (.docx), Plain Text (.txt)
"""
import os
import uuid
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyMuPDFLoader
import docx
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


def _parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDFLoader."""
    loader = PyMuPDFLoader(file_path)
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


def _parse_docx(file_path: str) -> str:
    """Extract text from a Word (.docx) file."""
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def _parse_txt(file_path: str) -> str:
    """Read plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_document(file_path: str) -> str:
    """Parse a document based on its extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext == ".docx":
        return _parse_docx(file_path)
    elif ext in (".txt", ".md"):
        return _parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def ingest_document(file_path: str, filename: str, doc_id: str = None) -> List[Document]:
    """
    Parse a document file and split it into chunks.
    Returns a list of LangChain Document objects with metadata.
    """
    raw_text = parse_document(file_path)
    if not raw_text.strip():
        raise ValueError("Document appears to be empty or could not be parsed.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )

    if doc_id is None:
        doc_id = str(uuid.uuid4())

    chunks = splitter.create_documents(
        [raw_text],
        metadatas=[{"source": filename, "doc_id": doc_id, "file_path": file_path}],
    )

    return chunks, doc_id
