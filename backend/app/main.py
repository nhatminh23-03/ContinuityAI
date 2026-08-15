"""ContinuityAI backend entry point.

Run: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.errors import register_error_handlers

app = FastAPI(
    title="ContinuityAI API",
    version="1.0.0",
    description="Engineering Knowledge Resilience. Contract: docs/API_CONTRACT.md",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
