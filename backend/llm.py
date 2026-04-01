"""
llm.py – Groq LLM initialisation via LangChain
"""
from functools import lru_cache
from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY, GROQ_MODEL


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """Instantiate and cache the Groq-backed ChatLLM."""
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=GROQ_MODEL,
        temperature=0.2,
        max_tokens=1024,
    )
