"""
Response schemas for the DSA Revision Analyzer API.

These Pydantic models define the public JSON contract returned
by the API layer.

Internal service-layer dataclasses are intentionally not exposed
directly to API clients.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalResultResponse(BaseModel):
    """
    One normalized retrieval result returned by the API.
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
    Complete response returned by the hybrid retrieval endpoint.
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