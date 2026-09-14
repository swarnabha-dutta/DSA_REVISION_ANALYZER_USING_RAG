"""
Retrieval API routes for the DSA Revision Analyzer.

Phase 15.3 responsibilities:
    - Accept validated retrieval requests.
    - Run query understanding.
    - Execute the existing hybrid retrieval pipeline.
    - Normalize results through the existing context assembly layer.
    - Convert normalized results into API-safe responses.

The API layer does not implement retrieval logic itself.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.requests import SearchRequest
from app.schemas.responses import (
    RetrievalResponse,
    RetrievalResultResponse,
)
from app.services.context_assembler import assemble_context
from app.services.hybrid_retrieval import retrieve_hybrid
from app.services.query_understanding import understand_query


router = APIRouter(
    prefix="/api/v1/retrieval",
    tags=["Retrieval"],
)


@router.post(
    "/search",
    response_model=RetrievalResponse,
)
def search(request: SearchRequest) -> RetrievalResponse:
    """
    Execute the complete hybrid retrieval pipeline.

    Pipeline
    --------
    Request validation
        ↓
    Query understanding
        ↓
    Hybrid retrieval
        ↓
    Context normalization
        ↓
    API response
    """

    try:
        # --------------------------------------------------------
        # Query Understanding
        # --------------------------------------------------------

        query_analysis = understand_query(
            request.query,
        )

        # --------------------------------------------------------
        # Hybrid Retrieval
        # --------------------------------------------------------

        retrieval_result = retrieve_hybrid(
            query=request.query,
            pattern=request.pattern,
            sub_pattern=request.sub_pattern,
            query_analysis=query_analysis,
            top_k=request.top_k,
        )

        # --------------------------------------------------------
        # Context Assembly
        # --------------------------------------------------------

        context = assemble_context(
            query=retrieval_result.query,
            results=retrieval_result.fused_results,
            pattern=retrieval_result.pattern,
            sub_pattern=retrieval_result.sub_pattern,
            top_k=request.top_k,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Retrieval pipeline failed.",
        ) from exc

    # ------------------------------------------------------------
    # Normalize Context Items → API Response Models
    # ------------------------------------------------------------

    results: list[RetrievalResultResponse] = []

    for item in context.items:
        results.append(
            RetrievalResultResponse(
                rank=item.rank,
                point_id=item.point_id,
                text=item.text,
                video_id=item.video_id,
                pattern=item.pattern,
                sub_pattern=item.sub_pattern,
                timestamp_start=item.timestamp_start,
                timestamp_end=item.timestamp_end,
                rrf_score=item.rrf_score,
                reranker_score=item.reranker_score,
            )
        )

    return RetrievalResponse(
        query=retrieval_result.query,
        pattern=retrieval_result.pattern,
        sub_pattern=retrieval_result.sub_pattern,
        results=results,
    )