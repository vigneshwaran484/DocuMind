from functools import lru_cache
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

@lru_cache(maxsize=1)
def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
