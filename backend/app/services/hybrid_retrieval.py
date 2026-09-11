"""
Hybrid Retrieval Service
========================

Purpose
-------
Run semantic retrieval and lexical BM25 retrieval for the same
user query and return both candidate sets independently.

Pipeline
--------

                    User Query
                        |
              +---------+---------+
              |                   |
              v                   v
        Qdrant Semantic       BM25 Lexical
              |                   |
              v                   v
      Semantic Results       BM25 Results
              |                   |
              +---------+---------+
                        |
                        v
             HybridRetrievalResult

Important
---------
This module does NOT perform RRF.

RRF is intentionally kept as a separate stage so that:

1. semantic retrieval can be tested independently
2. BM25 retrieval can be tested independently
3. candidate generation can be inspected
4. fusion can be tested separately
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.bm25_index import (
    BM25Document,
    BM25Index,
    BM25_INDEX_FILE,
    get_allowed_document_indices,
)

from app.services.retrieval import (
    RetrievalResult,
    retrieve,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_HYBRID_TOP_K = 5

# Retrieve more candidates than the final Top-K.
#
# Example:
#     top_k = 5
#     multiplier = 3
#     candidate_k = 15
#
# This gives the future RRF stage a larger candidate pool.
DEFAULT_CANDIDATE_MULTIPLIER = 3


# ============================================================
# RESULT MODELS
# ============================================================

@dataclass(frozen=True)
class BM25RetrievalResult:
    """
    Application-level representation of one BM25 result.

    score:
        BM25 lexical relevance score.

    document:
        BM25Document containing the indexed chunk metadata.
    """

    score: float
    document: BM25Document


@dataclass(frozen=True)
class HybridRetrievalResult:
    """
    Independent outputs of semantic and BM25 retrieval.

    No RRF fusion is performed here.
    """

    query: str

    semantic_results: list[
        RetrievalResult
    ]

    bm25_results: list[
        BM25RetrievalResult
    ]

    pattern: str | None

    sub_pattern: str | None


# ============================================================
# BM25 INDEX LOADING
# ============================================================

def load_bm25_index() -> BM25Index:
    """
    Load the persistent BM25 index from disk.

    The index is expected to be created by:

        scripts/build_bm25_index.py
    """

    if not BM25_INDEX_FILE.exists():
        raise FileNotFoundError(
            "BM25 index does not exist: "
            f"{BM25_INDEX_FILE}. "
            "Run scripts/build_bm25_index.py first."
        )

    return BM25Index.load(
        BM25_INDEX_FILE
    )


# ============================================================
# QUERY ANALYSIS HELPERS
# ============================================================

def get_analysis_value(
    query_analysis: Any,
    field_name: str,
) -> str | None:
    """
    Safely extract a field from a QueryAnalysis-like object.

    Supports both:

        dictionary:
            {"pattern": "dynamic_programming"}

    and object:

        analysis.pattern
    """

    if query_analysis is None:
        return None

    if isinstance(
        query_analysis,
        dict,
    ):
        value = query_analysis.get(
            field_name
        )
    else:
        value = getattr(
            query_analysis,
            field_name,
            None,
        )

    if value is None:
        return None

    value = str(
        value
    ).strip()

    return value or None


def resolve_metadata(
    *,
    pattern: str | None,
    sub_pattern: str | None,
    query_analysis: Any = None,
) -> tuple[
    str | None,
    str | None,
]:
    """
    Resolve pattern and sub-pattern.

    Explicit function arguments always have priority.

    If an explicit value is missing, the function attempts to
    obtain it from query_analysis.

    This keeps query-analysis support inside the hybrid layer
    without forcing retrieval.py to depend on QueryAnalysis.
    """

    if pattern is None:
        pattern = get_analysis_value(
            query_analysis,
            "pattern",
        )

    if sub_pattern is None:
        sub_pattern = get_analysis_value(
            query_analysis,
            "sub_pattern",
        )

    return (
        pattern,
        sub_pattern,
    )


# ============================================================
# SEMANTIC RETRIEVAL
# ============================================================

def retrieve_semantic(
    *,
    query: str,
    pattern: str | None,
    sub_pattern: str | None,
    candidate_k: int,
) -> list[RetrievalResult]:
    """
    Run semantic retrieval through retrieval.py.

    IMPORTANT:
        retrieval.py owns Qdrant logic.

        hybrid_retrieval.py must NOT duplicate:
            - embedding generation
            - Qdrant client creation
            - Qdrant filtering
            - Qdrant result conversion

    This function therefore calls the existing public
    retrieve() API.
    """

    return retrieve(
        query=query,
        top_k=candidate_k,
        pattern=pattern,
        sub_pattern=sub_pattern,
    )


# ============================================================
# BM25 RETRIEVAL
# ============================================================

def retrieve_bm25(
    *,
    query: str,
    pattern: str | None,
    sub_pattern: str | None,
    candidate_k: int,
) -> list[BM25RetrievalResult]:
    """
    Run BM25 lexical retrieval.

    Metadata restrictions are applied before ranking.
    """

    index = load_bm25_index()

    allowed_indices = (
        get_allowed_document_indices(
            index,
            pattern=pattern,
            sub_pattern=sub_pattern,
        )
    )

    raw_results = index.search(
        query=query,
        top_k=candidate_k,
        allowed_document_indices=allowed_indices,
    )

    return [
        BM25RetrievalResult(
            score=float(score),
            document=document,
        )
        for document, score in raw_results
    ]


# ============================================================
# HYBRID RETRIEVAL
# ============================================================

def retrieve_hybrid(
    *,
    query: str,
    pattern: str | None = None,
    sub_pattern: str | None = None,
    query_analysis: Any = None,
    top_k: int = DEFAULT_HYBRID_TOP_K,
    candidate_multiplier: int = DEFAULT_CANDIDATE_MULTIPLIER,
) -> HybridRetrievalResult:
    """
    Run semantic and BM25 retrieval independently.

    Parameters
    ----------
    query:
        User's natural-language query.

    pattern:
        Optional DSA pattern restriction.

    sub_pattern:
        Optional DSA sub-pattern restriction.

    query_analysis:
        Optional QueryAnalysis-like object/dictionary.

        This is handled ONLY by this hybrid layer.
        It is NOT forwarded into retrieval.py.

    top_k:
        Desired final result count.

    candidate_multiplier:
        Number of candidates retrieved from each retriever
        relative to top_k.

    Example
    -------
    top_k = 5
    candidate_multiplier = 3

    candidate_k = 15

    Semantic:
        top 15

    BM25:
        top 15

    Later:

        15 + 15
            |
            v
           RRF
            |
            v
        final Top 5
    """

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "Query cannot be empty."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    if candidate_multiplier <= 0:
        raise ValueError(
            "candidate_multiplier must be greater than 0."
        )

    # --------------------------------------------------------
    # Resolve metadata
    # --------------------------------------------------------

    pattern, sub_pattern = (
        resolve_metadata(
            pattern=pattern,
            sub_pattern=sub_pattern,
            query_analysis=query_analysis,
        )
    )

    # --------------------------------------------------------
    # Candidate pool
    # --------------------------------------------------------

    candidate_k = max(
        top_k,
        top_k * candidate_multiplier,
    )

    # --------------------------------------------------------
    # Semantic retrieval
    # --------------------------------------------------------

    semantic_results = retrieve_semantic(
        query=query,
        pattern=pattern,
        sub_pattern=sub_pattern,
        candidate_k=candidate_k,
    )

    # --------------------------------------------------------
    # BM25 retrieval
    # --------------------------------------------------------

    bm25_results = retrieve_bm25(
        query=query,
        pattern=pattern,
        sub_pattern=sub_pattern,
        candidate_k=candidate_k,
    )

    # --------------------------------------------------------
    # Return independent candidate sets
    # --------------------------------------------------------

    return HybridRetrievalResult(
        query=query,
        semantic_results=semantic_results,
        bm25_results=bm25_results,
        pattern=pattern,
        sub_pattern=sub_pattern,
    )


# ============================================================
# RESULT DISPLAY HELPERS
# ============================================================

def print_semantic_results(
    results: list[RetrievalResult],
) -> None:
    """
    Pretty-print semantic retrieval results.
    """

    print()
    print("=" * 60)
    print("SEMANTIC RESULTS")
    print("=" * 60)

    print(
        f"Retrieved semantic candidates: "
        f"{len(results)}"
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):
        print()

        print(
            f"[{rank}] "
            f"score={result.score:.4f}"
        )

        print(
            f"    point_id   : "
            f"{result.point_id}"
        )

        print(
            f"    chunk_id   : "
            f"{result.chunk_id}"
        )

        print(
            f"    video_id   : "
            f"{result.video_id}"
        )

        print(
            f"    pattern    : "
            f"{result.pattern}"
        )

        print(
            f"    sub_pattern: "
            f"{result.sub_pattern}"
        )

        print(
            f"    timestamp  : "
            f"{result.start:.2f}s"
            f" → "
            f"{result.end:.2f}s"
        )


def print_bm25_results(
    results: list[BM25RetrievalResult],
) -> None:
    """
    Pretty-print BM25 retrieval results.
    """

    print()
    print("=" * 60)
    print("BM25 RESULTS")
    print("=" * 60)

    print(
        f"Retrieved BM25 candidates: "
        f"{len(results)}"
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):
        document = result.document

        print()

        print(
            f"[{rank}] "
            f"score={result.score:.4f}"
        )

        print(
            f"    point_id   : "
            f"{document.point_id}"
        )

        print(
            f"    chunk_id   : "
            f"{document.chunk_id}"
        )

        print(
            f"    video_id   : "
            f"{document.video_id}"
        )

        print(
            f"    pattern    : "
            f"{document.pattern}"
        )

        print(
            f"    sub_pattern: "
            f"{document.sub_pattern}"
        )


# ============================================================
# MODULE SELF-CHECK
# ============================================================

def self_check() -> None:
    """
    Validate that the hybrid module imports correctly and that
    the BM25 index is available.

    This does NOT execute Qdrant retrieval because that would
    make module import/self-check dependent on external service
    availability.
    """

    print("=" * 60)
    print("HYBRID RETRIEVAL SERVICE SELF-CHECK")
    print("=" * 60)

    print(
        f"Default Top-K          : "
        f"{DEFAULT_HYBRID_TOP_K}"
    )

    print(
        f"Candidate Multiplier   : "
        f"{DEFAULT_CANDIDATE_MULTIPLIER}"
    )

    print(
        f"BM25 Index             : "
        f"{BM25_INDEX_FILE}"
    )

    # --------------------------------------------------------
    # Verify BM25 index
    # --------------------------------------------------------

    if BM25_INDEX_FILE.exists():
        print(
            "✓ BM25 index file exists."
        )
    else:
        print(
            "⚠ BM25 index file does not exist."
        )

    # --------------------------------------------------------
    # Verify callable interfaces
    # --------------------------------------------------------

    assert callable(
        retrieve_semantic
    )

    assert callable(
        retrieve_bm25
    )

    assert callable(
        retrieve_hybrid
    )

    print(
        "✓ Semantic retrieval interface available."
    )

    print(
        "✓ BM25 retrieval interface available."
    )

    print(
        "✓ Hybrid retrieval interface available."
    )

    print()
    print(
        "✓ Hybrid retrieval service self-check passed."
    )


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    self_check()