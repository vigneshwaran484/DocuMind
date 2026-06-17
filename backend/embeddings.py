import os
from typing import List
from langchain.embeddings.base import Embeddings
from google import genai

class GeminiEmbeddings(Embeddings):
    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options={"api_version": "v1beta"}
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        result = []
        for text in texts:
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            result.append(response.embeddings[0].values)
        return result
    
    def embed_query(self, text: str) -> List[float]:
        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values

def get_embeddings() -> GeminiEmbeddings:
    return GeminiEmbeddings()