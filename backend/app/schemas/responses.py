"""
Response schemas for the DSA Revision Analyzer API.

This module contains API response models only.

IMPORTANT:
    This module must NOT import API routers.
    Keeping schemas independent prevents circular imports.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalResultResponse(BaseModel):
    """
    One normalized retrieval result.
    """

    rank: int = Field(
        ...,
        ge=1,
        description="Final reranked position.",
    )

    point_id: str = Field(
        ...,
        min_length=1,
        description="Stable identifier of the retrieved chunk.",
    )

    text: str = Field(
        ...,
        min_length=1,
        description="Retrieved chunk text.",
    )

    video_id: str | None = Field(
        default=None,
        description="Source YouTube video ID.",
    )

    pattern: str | None = Field(
        default=None,
        description="Canonical DSA pattern.",
    )

    sub_pattern: str | None = Field(
        default=None,
        description="Canonical DSA sub-pattern.",
    )

    timestamp_start: float | None = Field(
        default=None,
        ge=0,
        description="Start timestamp in seconds.",
    )

    timestamp_end: float | None = Field(
        default=None,
        ge=0,
        description="End timestamp in seconds.",
    )

    rrf_score: float | None = Field(
        default=None,
        description="Reciprocal Rank Fusion score.",
    )

    reranker_score: float | None = Field(
        default=None,
        description="Cross-Encoder reranker score.",
    )


class RetrievalResponse(BaseModel):
    """
    Complete response from the hybrid retrieval endpoint.
    """

    query: str = Field(
        ...,
        min_length=1,
    )

    pattern: str | None = None

    sub_pattern: str | None = None

    results: list[RetrievalResultResponse] = Field(
        default_factory=list,
    )


class RAGSourceResponse(BaseModel):
    """
    Source metadata returned together with a grounded AI answer.
    """

    rank: int = Field(
        ...,
        ge=1,
    )

    point_id: str = Field(
        ...,
        min_length=1,
    )

    video_id: str | None = None

    pattern: str | None = None

    sub_pattern: str | None = None

    timestamp_start: float | None = Field(
        default=None,
        ge=0,
    )

    timestamp_end: float | None = Field(
        default=None,
        ge=0,
    )

    text: str = Field(
        ...,
        min_length=1,
    )


class RAGResponse(BaseModel):
    """
    Public response model for the grounded RAG endpoint.
    """

    query: str = Field(
        ...,
        min_length=1,
    )

    answer: str = Field(
        ...,
        min_length=1,
    )

    model: str = Field(
        ...,
        min_length=1,
    )

    query_language: str = Field(
        ...,
        min_length=1,
    )

    response_language: str = Field(
        ...,
        min_length=1,
    )

    pattern: str | None = None

    sub_pattern: str | None = None

    sources: list[RAGSourceResponse] = Field(
        default_factory=list,
    )