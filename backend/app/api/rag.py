"""
Public API endpoint for grounded RAG generation.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.requests import RAGRequest

from app.schemas.responses import (
    RAGResponse,
    RAGSourceResponse,
)

from app.services.context_assembler import (
    assemble_context,
)

from app.services.hybrid_retrieval import (
    retrieve_hybrid,
)

from app.services.llm_generator import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    generate_answer,
)

from app.services.query_understanding import (
    understand_query,
)


router = APIRouter(
    prefix="/api/v1/rag",
    tags=["RAG"],
)


@router.post(
    "/query",
    response_model=RAGResponse,
)
def rag_query(
    request: RAGRequest,
) -> RAGResponse:
    """
    Execute:

        Query Understanding
            ↓
        Hybrid Retrieval
            ↓
        Context Assembly
            ↓
        Language Detection
            ↓
        Grounded Prompt
            ↓
        Groq LLM
            ↓
        API Response
    """

    try:

        # ====================================================
        # 1. QUERY UNDERSTANDING
        # ====================================================

        query_analysis = understand_query(
            request.query,
        )

        # ====================================================
        # 2. HYBRID RETRIEVAL
        # ====================================================

        retrieval_result = retrieve_hybrid(
            query=request.query,
            pattern=request.pattern,
            sub_pattern=request.sub_pattern,
            query_analysis=query_analysis,
            top_k=request.top_k,
        )

        # ====================================================
        # 3. CONTEXT ASSEMBLY
        # ====================================================

        context = assemble_context(
            query=retrieval_result.query,
            results=retrieval_result.fused_results,
            pattern=retrieval_result.pattern,
            sub_pattern=retrieval_result.sub_pattern,
            top_k=request.top_k,
        )

        # ====================================================
        # 4. LLM GENERATION
        # ====================================================

        generation = generate_answer(
            context=context,
            model=(
                request.model
                or DEFAULT_MODEL
            ),
            temperature=(
                request.temperature
                if request.temperature is not None
                else DEFAULT_TEMPERATURE
            ),
            max_tokens=(
                request.max_tokens
                if request.max_tokens is not None
                else DEFAULT_MAX_TOKENS
            ),
        )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except FileNotFoundError as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail="RAG pipeline failed.",
        ) from exc

    # ========================================================
    # API RESPONSE
    # ========================================================

    return RAGResponse(
        query=generation.query,

        answer=generation.answer,

        model=generation.model,

        query_language=generation.query_language,

        response_language=generation.response_language,

        pattern=context.pattern,

        sub_pattern=context.sub_pattern,

        sources=[
            RAGSourceResponse(
                rank=item.rank,

                point_id=item.point_id,

                video_id=item.video_id,

                video_title=item.video_title,

                pattern=item.pattern,

                sub_pattern=item.sub_pattern,

                timestamp_start=item.timestamp_start,

                timestamp_end=item.timestamp_end,

                text=item.text,

                summary=(
                    generation.video_summaries.get(
                        item.video_id
                    )
                    if item.video_id
                    else None
                ),
            )
            for item in context.items
        ],
    )