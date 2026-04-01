"""
qa_chain.py – RAG chain: retriever + prompt + Groq LLM
Returns structured answer with source citations.
"""
from typing import Dict, Any
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from backend.llm import get_llm
from backend.vectorstore import get_vectorstore
from backend.config import TOP_K

PROMPT_TEMPLATE = """You are an expert enterprise document analyst. Use the following retrieved document excerpts to answer the user's question accurately and thoroughly.

Guidelines:
- Answer clearly and concisely based ONLY on the provided context.
- If the answer is not found in the context, say: "I couldn't find relevant information in the uploaded documents."
- Include specific details, numbers, or facts from the documents when relevant.
- Structure longer answers with bullet points or numbered lists for clarity.

Context:
{context}

Question: {question}

Detailed Answer:"""


def get_qa_chain() -> RetrievalQA:
    """Build and return a RetrievalQA chain."""
    vs = get_vectorstore()
    if vs is None:
        raise ValueError("No documents have been indexed yet. Please upload documents first.")

    retriever = vs.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )

    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )

    chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )
    return chain


def answer_question(question: str) -> Dict[str, Any]:
    """
    Run the RAG pipeline for a given question.
    Returns {answer, sources}.
    """
    chain = get_qa_chain()
    result = chain.invoke({"query": question})

    sources = []
    seen = set()
    for doc in result.get("source_documents", []):
        src = doc.metadata.get("source", "Unknown")
        if src not in seen:
            seen.add(src)
            sources.append({
                "filename": src,
                "excerpt": doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else ""),
            })

    return {
        "answer": result.get("result", "No answer generated."),
        "sources": sources,
    }
