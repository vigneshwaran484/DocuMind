"""
auth.py – FastAPI dependency that validates a Supabase JWT and returns the user.
"""
from fastapi import Header, HTTPException
from supabase import create_client

from backend.config import SUPABASE_URL, SUPABASE_KEY

_anon_client = None


def _get_anon_client():
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _anon_client


async def get_current_user(authorization: str = Header(...)):
    """Extract and validate the Bearer token, return the Supabase user object."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    try:
        client = _get_anon_client()
        response = client.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return response.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth error: {e}")
