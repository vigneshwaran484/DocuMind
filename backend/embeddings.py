import os
from typing import List
from langchain.embeddings.base import Embeddings
import google.generativeai as genai

class GeminiEmbeddings(Embeddings):
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        result = []
        for text in texts:
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            result.append(response["embedding"])
        return result
    
    def embed_query(self, text: str) -> List[float]:
        response = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return response["embedding"]

def get_embeddings() -> GeminiEmbeddings:
    return GeminiEmbeddings()