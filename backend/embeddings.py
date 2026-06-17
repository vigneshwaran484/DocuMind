import os
from typing import List
from langchain.embeddings.base import Embeddings
from google import genai
from google.genai import types

class GeminiEmbeddings(Embeddings):
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        result = []
        for text in texts:
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            result.append(response.embeddings[0].values)
        return result
    
    def embed_query(self, text: str) -> List[float]:
        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        return response.embeddings[0].values

def get_embeddings() -> GeminiEmbeddings:
    return GeminiEmbeddings()