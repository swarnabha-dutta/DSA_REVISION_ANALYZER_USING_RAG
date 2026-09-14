"""
API routes for the DSA Revision Analyzer.

Phase 15.2 responsibilities:
    - Expose versioned API routes.
    - Provide the health endpoint.
    - Define the public API boundary.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.requests import (
    QueryRequest,
    RAGRequest,
    SearchRequest,
)


router = APIRouter(
    prefix="/api/v1",
)


@router.get(
    "/health",
    tags=["Health"],
)
def health_check() -> dict[str, str]:
    """
    Return the current API health status.
    """

    return {
        "status": "ok",
        "service": "dsa-revision-analyzer-api",
    }