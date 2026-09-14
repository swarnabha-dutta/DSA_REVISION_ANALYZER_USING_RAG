"""
FastAPI application entry point for the DSA Revision Analyzer.

Phase 15 responsibilities:
    - Create the FastAPI application.
    - Register API routes.
    - Provide application metadata.
    - Keep startup lightweight.

The application must not eagerly initialize expensive retrieval,
reranking, embedding, or LLM components during import.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.api.retrieval import router as retrieval_router


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_TITLE = "DSA Revision Analyzer API"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = (
    "API backend for the DSA Revision Analyzer "
    "intelligent retrieval and grounded RAG system."
)


# ============================================================
# APPLICATION FACTORY
# ============================================================


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        Configured FastAPI application instance.
    """

    application = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )

    application.include_router(router)
    application.include_router(retrieval_router)

    return application


# ============================================================
# APPLICATION INSTANCE
# ============================================================

app = create_app()