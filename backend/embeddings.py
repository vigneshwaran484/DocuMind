import os
import requests
from typing import List
from langchain.embeddings.base import Embeddings

HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL}"

class HuggingFaceAPIEmbeddings(Embeddings):
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}

    def _embed(self, texts: List[str]) -> List[List[float]]:
        response = requests.post(
            HF_API_URL,
            headers=self.headers,
            json={"inputs": texts, "options": {"wait_for_model": True}}
        )
        response.raise_for_status()
        return response.json()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]

def get_embeddings() -> HuggingFaceAPIEmbeddings:
    return HuggingFaceAPIEmbeddings()