"""
main.py – FastAPI application entry point
Mounts all routers and serves the React/HTML frontend as static files.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routers import upload, query, documents

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Enterprise RAG Q&A System",
    description="Upload enterprise documents and ask intelligent questions powered by Groq LLM.",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])

# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "Enterprise RAG Q&A System"}

@app.get("/api/debug", tags=["Health"])
async def debug():
    from backend.supabase_store import test_connection
    conn = test_connection()
    return {"supabase": conn}

# ── Serve Frontend Static Files ───────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/login", include_in_schema=False)
    async def serve_login():
        return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
