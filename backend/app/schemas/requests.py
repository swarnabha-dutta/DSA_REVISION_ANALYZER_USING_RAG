"""
Request schemas for the DSA Revision Analyzer API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """
    Request payload for hybrid retrieval.
    """

    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language DSA search query.",
    )

    pattern: str | None = Field(
        default=None,
        description="Optional canonical DSA pattern.",
    )

    sub_pattern: str | None = Field(
        default=None,
        description="Optional canonical DSA sub-pattern.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of final retrieval results.",
    )


class QueryRequest(BaseModel):
    """
    Request payload for query understanding.
    """

    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language DSA query.",
    )


class RAGRequest(BaseModel):
    """
    Request payload for grounded RAG generation.
    """

    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language DSA question.",
    )

    pattern: str | None = Field(
        default=None,
        description="Optional canonical DSA pattern.",
    )

    sub_pattern: str | None = Field(
        default=None,
        description="Optional canonical DSA sub-pattern.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of retrieval results used for context.",
    )

    model: str | None = Field(
        default=None,
        description="Optional Groq model override.",
    )

    temperature: float | None = Field(
        default=None,
        ge=0.0,
        description="Optional LLM sampling temperature.",
    )

    max_tokens: int | None = Field(
        default=None,
        ge=1,
        description="Optional maximum generated tokens.",
    )