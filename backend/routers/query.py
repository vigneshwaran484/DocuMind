"""
routers/query.py – Question answering endpoint
POST /api/query
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.qa_chain import answer_question

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000, description="The question to ask.")


@router.post("/query")
async def query_documents(request: QueryRequest):
    """Answer a question using the indexed documents."""
    try:
        result = answer_question(request.question)
        return {
            "success": True,
            "question": request.question,
            "answer": result["answer"],
            "sources": result["sources"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA pipeline error: {e}")
