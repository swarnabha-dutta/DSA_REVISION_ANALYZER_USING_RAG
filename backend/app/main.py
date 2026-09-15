"""
FastAPI application entry point for the DSA Revision Analyzer.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.retrieval import router as retrieval_router
from app.api.rag import router as rag_router


APP_TITLE = "DSA Revision Analyzer API"

APP_VERSION = "0.1.0"

APP_DESCRIPTION = (
    "API backend for the DSA Revision Analyzer "
    "intelligent retrieval and grounded RAG system."
)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    """

    application = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )

    # ========================================================
    # EXISTING ROUTES
    # ========================================================

    application.include_router(router)

    application.include_router(
        retrieval_router
    )

    # ========================================================
    # RAG ROUTES
    # ========================================================

    application.include_router(
        rag_router
    )

    # ========================================================
    # CORS
    # ========================================================

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = create_app()