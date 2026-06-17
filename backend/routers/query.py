"""
routers/query.py – Question answering endpoint
POST /api/query
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.qa_chain import answer_question
from backend.auth import get_current_user

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


@router.post("/query")
async def query_documents(request: QueryRequest, user=Depends(get_current_user)):
    try:
        result = answer_question(request.question, user.id)
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
