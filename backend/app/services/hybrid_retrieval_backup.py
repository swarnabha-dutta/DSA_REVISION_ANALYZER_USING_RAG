"""
Hybrid Retrieval Service
========================

Purpose:
    Combine semantic retrieval and lexical BM25 retrieval
    using Reciprocal Rank Fusion (RRF).

Pipeline:

    User Query
         |
         +-------------------------+
         |                         |
         v                         v
    Semantic Retrieval          BM25 Retrieval
       (Qdrant)                   (Lexical)
         |                         |
         | Top Candidate-K         | Top Candidate-K
         |                         |
         +------------+------------+
                      |
                      v
                 RRF Fusion
                      |
                      v
                 Final Top-K
                      |
                      v
              Hybrid Results

Responsibilities:
    1. Resolve metadata filters.
    2. Retrieve semantic candidates.
    3. Retrieve BM25 candidates.
    4. Fuse both ranked lists using RRF.
    5. Map fused IDs back to complete chunk metadata.

Important:
    retrieval.py owns semantic/Qdrant retrieval.

    bm25_index.py owns BM25 indexing and lexical search.

    rrf.py owns Reciprocal Rank Fusion.

    This module orchestrates all three.
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

from app.services.rrf import (
    DEFAULT_RRF_K,
    RRFResult,
    fuse_semantic_and_bm25,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_HYBRID_TOP_K = 5

# Retrieve more candidates from each retriever before fusion.
#
# Example:
#
#     top_k = 5
#     multiplier = 3
#
#     semantic = 15
#     BM25     = 15
#     RRF      = final 5
#
DEFAULT_CANDIDATE_MULTIPLIER = 3


# ============================================================
# RESULT MODELS
# ============================================================


@dataclass(frozen=True)
class BM25RetrievalResult:
    """
    Application-level representation of one BM25 result.
    """

    score: float
    document: BM25Document


@dataclass(frozen=True)
class HybridResult:
    """
    One final RRF-fused retrieval result.

    Attributes
    ----------
    point_id:
        Stable Qdrant/BM25 document identifier.

    rrf_score:
        Final Reciprocal Rank Fusion score.

    rank_positions:
        Rank assigned by each retriever.

    contributions:
        Individual RRF contributions.

    semantic_result:
        Full semantic retrieval result if available.

    bm25_document:
        Full BM25 document if available.
    """

    point_id: str

    rrf_score: float

    rank_positions: dict[str, int]

    contributions: dict[str, float]

    semantic_result: RetrievalResult | None

    bm25_document: BM25Document | None


@dataclass(frozen=True)
class HybridRetrievalResult:
    """
    Complete output of the hybrid retrieval pipeline.

    semantic_results:
        Candidate results returned by semantic retrieval.

    bm25_results:
        Candidate results returned by BM25.

    fused_results:
        Final RRF-ranked results.
    """

    query: str

    semantic_results: list[RetrievalResult]

    bm25_results: list[BM25RetrievalResult]

    fused_results: list[HybridResult]

    pattern: str | None

    sub_pattern: str | None


# ============================================================
# BM25 INDEX LOADING
# ============================================================


def load_bm25_index() -> BM25Index:
    """
    Load the persistent BM25 index from disk.

    The index is created by:

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
    Extract a metadata value from either:

        - a dictionary
        - an object with attributes

    Example dictionary:

        {
            "pattern": "dynamic_programming",
            "sub_pattern": "memoization",
        }
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

    Missing values may be obtained from query_analysis.
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

    retrieval.py remains the owner of:

        - embedding generation
        - Qdrant client
        - Qdrant filtering
        - result conversion
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
# RRF RESULT MAPPING
# ============================================================


def _build_result_lookup(
    semantic_results: list[RetrievalResult],
    bm25_results: list[BM25RetrievalResult],
) -> tuple[
    dict[str, RetrievalResult],
    dict[str, BM25Document],
]:
    """
    Build lookup tables keyed by stable point_id.

    Both semantic and BM25 must use the same point_id
    so RRF can identify the same underlying chunk.
    """

    semantic_lookup: dict[
        str,
        RetrievalResult,
    ] = {}

    bm25_lookup: dict[
        str,
        BM25Document,
    ] = {}

    for result in semantic_results:
        semantic_lookup[
            str(result.point_id)
        ] = result

    for result in bm25_results:
        document = result.document

        bm25_lookup[
            str(document.point_id)
        ] = document

    return (
        semantic_lookup,
        bm25_lookup,
    )


def _build_fused_results(
    *,
    rrf_results: list[RRFResult],
    semantic_results: list[RetrievalResult],
    bm25_results: list[BM25RetrievalResult],
) -> list[HybridResult]:
    """
    Convert generic RRF results into application-level
    HybridResult objects.

    RRF only knows about stable IDs.

    This function restores the complete metadata associated
    with those IDs.
    """

    (
        semantic_lookup,
        bm25_lookup,
    ) = _build_result_lookup(
        semantic_results,
        bm25_results,
    )

    fused_results: list[HybridResult] = []

    for result in rrf_results:

        point_id = str(
            result.document_id
        )

        fused_results.append(
            HybridResult(
                point_id=point_id,
                rrf_score=float(
                    result.score
                ),
                rank_positions=dict(
                    result.rank_positions
                ),
                contributions=dict(
                    result.contributions
                ),
                semantic_result=semantic_lookup.get(
                    point_id
                ),
                bm25_document=bm25_lookup.get(
                    point_id
                ),
            )
        )

    return fused_results


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
    rrf_k: float = DEFAULT_RRF_K,
    semantic_weight: float = 1.0,
    bm25_weight: float = 1.0,
) -> HybridRetrievalResult:
    """
    Execute the complete hybrid retrieval pipeline.

    Pipeline:

        Query
          |
          +--------------------+
          |                    |
          v                    v
      Semantic                BM25
       Top-K                  Top-K
          |                    |
          +---------+----------+
                    |
                    v
                   RRF
                    |
                    v
                Final Top-K

    Parameters
    ----------
    query:
        User's natural-language query.

    pattern:
        Optional DSA pattern filter.

    sub_pattern:
        Optional DSA sub-pattern filter.

    query_analysis:
        Optional QueryAnalysis-like object or dictionary.

    top_k:
        Number of final fused results.

    candidate_multiplier:
        Number of candidates retrieved from each retriever
        relative to top_k.

    rrf_k:
        RRF rank constant.

    semantic_weight:
        Weight applied to semantic retrieval.

    bm25_weight:
        Weight applied to BM25 retrieval.
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

    # --------------------------------------------------------
    # Validate numeric parameters
    # --------------------------------------------------------

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    if candidate_multiplier <= 0:
        raise ValueError(
            "candidate_multiplier must be greater than 0."
        )

    if rrf_k <= 0:
        raise ValueError(
            "rrf_k must be greater than 0."
        )

    if semantic_weight < 0:
        raise ValueError(
            "semantic_weight cannot be negative."
        )

    if bm25_weight < 0:
        raise ValueError(
            "bm25_weight cannot be negative."
        )

    # --------------------------------------------------------
    # Resolve metadata
    # --------------------------------------------------------

    (
        pattern,
        sub_pattern,
    ) = resolve_metadata(
        pattern=pattern,
        sub_pattern=sub_pattern,
        query_analysis=query_analysis,
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
    # Prepare stable IDs for RRF
    # --------------------------------------------------------

    semantic_ids = [
        str(result.point_id)
        for result in semantic_results
    ]

    bm25_ids = [
        str(result.document.point_id)
        for result in bm25_results
    ]

    # --------------------------------------------------------
    # RRF fusion
    # --------------------------------------------------------

    rrf_results = fuse_semantic_and_bm25(
        semantic_ids=semantic_ids,
        bm25_ids=bm25_ids,
        k=rrf_k,
        semantic_weight=semantic_weight,
        bm25_weight=bm25_weight,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # Restore complete metadata
    # --------------------------------------------------------

    fused_results = _build_fused_results(
        rrf_results=rrf_results,
        semantic_results=semantic_results,
        bm25_results=bm25_results,
    )

    # --------------------------------------------------------
    # Return complete hybrid result
    # --------------------------------------------------------

    return HybridRetrievalResult(
        query=query,
        semantic_results=semantic_results,
        bm25_results=bm25_results,
        fused_results=fused_results,
        pattern=pattern,
        sub_pattern=sub_pattern,
    )


# ============================================================
# DISPLAY: SEMANTIC
# ============================================================


def print_semantic_results(
    results: list[RetrievalResult],
) -> None:
    """
    Pretty-print semantic candidates.
    """

    print()
    print("=" * 60)
    print("SEMANTIC RESULTS")
    print("=" * 60)

    if not results:
        print("No semantic results.")
        return

    for rank, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"[{rank}] "
            f"score={result.score:.4f} "
            f"chunk={result.chunk_id}"
        )

        print(
            f"    point_id   : "
            f"{result.point_id}"
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
            f"{result.start:.2f}s → "
            f"{result.end:.2f}s"
        )


# ============================================================
# DISPLAY: BM25
# ============================================================


def print_bm25_results(
    results: list[BM25RetrievalResult],
) -> None:
    """
    Pretty-print BM25 candidates.
    """

    print()
    print("=" * 60)
    print("BM25 RESULTS")
    print("=" * 60)

    if not results:
        print("No BM25 results.")
        return

    for rank, result in enumerate(
        results,
        start=1,
    ):
        document = result.document

        print(
            f"[{rank}] "
            f"score={result.score:.4f} "
            f"chunk={document.chunk_id}"
        )

        print(
            f"    point_id   : "
            f"{document.point_id}"
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
# DISPLAY: RRF
# ============================================================


def print_fused_results(
    results: list[HybridResult],
) -> None:
    """
    Pretty-print final RRF results.
    """

    print()
    print("=" * 60)
    print("RRF FUSED RESULTS")
    print("=" * 60)

    if not results:
        print("No fused results.")
        return

    for rank, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"[{rank}] "
            f"RRF={result.rrf_score:.8f}"
        )

        print(
            f"    point_id      : "
            f"{result.point_id}"
        )

        print(
            f"    ranks         : "
            f"{result.rank_positions}"
        )

        print(
            f"    contributions : "
            f"{result.contributions}"
        )

        semantic = result.semantic_result

        if semantic is not None:
            print(
                f"    semantic      : "
                f"{semantic.score:.4f}"
            )

            print(
                f"    chunk         : "
                f"{semantic.chunk_id}"
            )

            print(
                f"    video         : "
                f"{semantic.video_id}"
            )

            print(
                f"    timestamp     : "
                f"{semantic.start:.2f}s → "
                f"{semantic.end:.2f}s"
            )

        bm25 = result.bm25_document

        if bm25 is not None:
            print(
                f"    bm25          : "
                f"available"
            )

            print(
                f"    bm25 chunk    : "
                f"{bm25.chunk_id}"
            )


# ============================================================
# DISPLAY: COMPLETE HYBRID
# ============================================================


def print_hybrid_results(
    result: HybridRetrievalResult,
) -> None:
    """
    Pretty-print the complete hybrid retrieval pipeline.
    """

    print()
    print("=" * 60)
    print("HYBRID RETRIEVAL")
    print("=" * 60)

    print(
        f"Query       : "
        f"{result.query}"
    )

    print(
        f"Pattern     : "
        f"{result.pattern or 'None'}"
    )

    print(
        f"Sub-pattern : "
        f"{result.sub_pattern or 'None'}"
    )

    print_semantic_results(
        result.semantic_results
    )

    print_bm25_results(
        result.bm25_results
    )

    print_fused_results(
        result.fused_results
    )


# ============================================================
# SELF CHECK
# ============================================================


def self_check() -> None:
    """
    Lightweight module self-check.

    This verifies that:

        1. BM25 index exists.
        2. Semantic retrieval is importable.
        3. BM25 retrieval is importable.
        4. RRF is importable.
        5. Hybrid retrieval is importable.
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
        f"RRF K                  : "
        f"{DEFAULT_RRF_K}"
    )

    print(
        f"BM25 Index             : "
        f"{BM25_INDEX_FILE}"
    )

    # --------------------------------------------------------
    # BM25
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
    # Semantic
    # --------------------------------------------------------

    if callable(retrieve):
        print(
            "✓ Semantic retrieval interface available."
        )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    if callable(retrieve_bm25):
        print(
            "✓ BM25 retrieval interface available."
        )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    if callable(fuse_semantic_and_bm25):
        print(
            "✓ RRF fusion interface available."
        )

    # --------------------------------------------------------
    # Hybrid
    # --------------------------------------------------------

    if callable(retrieve_hybrid):
        print(
            "✓ Hybrid retrieval interface available."
        )

    print()
    print(
        "✓ Hybrid retrieval service self-check passed."
    )


# ============================================================
# MODULE ENTRY POINT
# ============================================================


if __name__ == "__main__":
    self_check()