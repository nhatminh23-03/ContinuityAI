"""ContinuityAI backend entry point.

    uvicorn app.main:app --reload      # http://localhost:8000, docs at /docs

On first boot the database is created and seeded automatically when empty, so starting the API is
one command with no separate setup step. Set `AUTO_SEED=false` to manage the database yourself.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.db.session import ENGINE, SessionLocal, create_all

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("continuityai")


def _needs_seed() -> bool:
    if not inspect(ENGINE).has_table("platforms"):
        return True
    from app.models import Platform

    with SessionLocal() as session:
        return session.scalar(select(Platform.platform_id).limit(1)) is None


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_all()
    if settings.auto_seed and _needs_seed():
        logger.info("empty database detected, seeding the NovaPay demo dataset")
        from scripts.seed_demo import seed

        report = seed(verbose=False)
        logger.info(
            "seeded %s systems, %s capabilities, %s evidence records",
            report.systems,
            report.capabilities,
            report.evidence,
        )
    yield


app = FastAPI(
    title="ContinuityAI API",
    version="1.0.0",
    description="Engineering Knowledge Resilience. Contract: docs/API_CONTRACT.md",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Configurable via CORS_ORIGINS, because a hardcoded port 3000 turns an occupied port into a
    # browser-only failure that never appears in this process's log. See app/core/config.py.
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
