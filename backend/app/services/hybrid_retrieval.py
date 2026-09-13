"""
Hybrid Retrieval Service
========================

Combines:

    1. Semantic retrieval through Qdrant
    2. Lexical retrieval through BM25
    3. Reciprocal Rank Fusion (RRF)
    4. Cross-Encoder reranking

Pipeline:

    User Query
         |
         +----------------------+
         |                      |
         v                      v
    Semantic                 BM25
    Retrieval                Retrieval
         |                      |
         +----------+-----------+
                    |
                    v
               RRF Fusion
                    |
                    v
          Expanded Candidate Pool
                    |
                    v
          Cross-Encoder Reranking
                    |
                    v
               Final Top-K
                    |
                    v
              Hybrid Results
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

from app.services.reranker import (
    rerank,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_HYBRID_TOP_K = 5

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
    One hybrid retrieval candidate.

    rrf_score:
        Score assigned by Reciprocal Rank Fusion.

    reranker_score:
        Fine-grained relevance score assigned by the
        Cross-Encoder.

    rerank_rank:
        Final position after Cross-Encoder reranking.

    semantic_result:
        Full semantic result when available.

    bm25_document:
        Full BM25 document when available.
    """

    point_id: str

    rrf_score: float

    reranker_score: float | None

    rerank_rank: int | None

    rank_positions: dict[str, int]

    contributions: dict[str, float]

    semantic_result: RetrievalResult | None

    bm25_document: BM25Document | None


@dataclass(frozen=True)
class HybridRetrievalResult:
    """
    Complete result of the hybrid retrieval pipeline.

    semantic_results:
        Candidate results returned by semantic retrieval.

    bm25_results:
        Candidate results returned by BM25.

    rrf_results:
        Full candidate pool after RRF fusion.

    fused_results:
        Final Top-K results after Cross-Encoder reranking.
    """

    query: str

    semantic_results: list[RetrievalResult]

    bm25_results: list[BM25RetrievalResult]

    rrf_results: list[HybridResult]

    fused_results: list[HybridResult]

    pattern: str | None

    sub_pattern: str | None


# ============================================================
# BM25 INDEX
# ============================================================


def load_bm25_index() -> BM25Index:
    """
    Load the persistent BM25 index.
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
    Extract a value from either:

        - dictionary
        - object with attributes
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

    Explicit arguments always take priority.

    Missing values are obtained from
    query_analysis when available.
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
    Run semantic retrieval.

    retrieval.py owns:

        - embedding generation
        - Qdrant client
        - metadata filtering
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

    Metadata filtering is applied before ranking.
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
# RESULT LOOKUPS
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

    Both retrievers must use the same point_id for the
    same underlying chunk.
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


# ============================================================
# BUILD RRF RESULTS
# ============================================================


def _build_fused_results(
    *,
    rrf_results: list[RRFResult],
    semantic_results: list[RetrievalResult],
    bm25_results: list[BM25RetrievalResult],
) -> list[HybridResult]:
    """
    Convert generic RRF results into application-level
    HybridResult objects.

    RRF only knows stable IDs.

    This function restores the actual semantic/BM25
    metadata associated with each ID.

    Cross-Encoder fields remain unset at this stage.
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

                reranker_score=None,

                rerank_rank=None,

                rank_positions=dict(
                    result.rank_positions
                ),

                contributions=dict(
                    result.contributions
                ),

                semantic_result=(
                    semantic_lookup.get(
                        point_id
                    )
                ),

                bm25_document=(
                    bm25_lookup.get(
                        point_id
                    )
                ),
            )
        )

    return fused_results


# ============================================================
# CANDIDATE TEXT EXTRACTION
# ============================================================


def _get_candidate_text(
    result: HybridResult,
) -> str:
    """
    Extract the text that will be passed to the Cross-Encoder.

    Semantic retrieval is preferred because it represents the
    primary application-level retrieval result.

    BM25 document is used as a fallback.
    """

    if result.semantic_result is not None:

        text = getattr(
            result.semantic_result,
            "text",
            None,
        )

        if isinstance(
            text,
            str,
        ) and text.strip():

            return text.strip()

    if result.bm25_document is not None:

        text = getattr(
            result.bm25_document,
            "text",
            None,
        )

        if isinstance(
            text,
            str,
        ) and text.strip():

            return text.strip()

    raise ValueError(
        "No candidate text available for "
        f"point_id={result.point_id}"
    )


# ============================================================
# CROSS-ENCODER RERANKING
# ============================================================


def _rerank_fused_results(
    *,
    query: str,
    fused_results: list[HybridResult],
    top_k: int,
) -> list[HybridResult]:
    """
    Rerank the complete RRF candidate pool using the
    Cross-Encoder.

    RRF and Cross-Encoder have different responsibilities:

        RRF:
            Candidate fusion.

        Cross-Encoder:
            Fine-grained relevance ranking.

    Their scores are intentionally NOT added together.
    """

    if not fused_results:
        return []

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    candidate_texts = [
        _get_candidate_text(result)
        for result in fused_results
    ]

    reranked = rerank(
        query=query,
        candidates=candidate_texts,
        top_k=top_k,
    )

    final_results: list[HybridResult] = []

    for final_rank, reranker_result in enumerate(
        reranked,
        start=1,
    ):

        original_result = fused_results[
            reranker_result.candidate_index
        ]

        final_results.append(
            HybridResult(
                point_id=original_result.point_id,

                rrf_score=original_result.rrf_score,

                reranker_score=float(
                    reranker_result.score
                ),

                rerank_rank=final_rank,

                rank_positions=dict(
                    original_result.rank_positions
                ),

                contributions=dict(
                    original_result.contributions
                ),

                semantic_result=(
                    original_result.semantic_result
                ),

                bm25_document=(
                    original_result.bm25_document
                ),
            )
        )

    return final_results


# ============================================================
# MAIN HYBRID RETRIEVAL
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
      Semantic               BM25
      Candidate-K            Candidate-K
          |                    |
          +---------+----------+
                    |
                    v
                   RRF
                    |
                    v
          Expanded Candidate Pool
                    |
                    v
          Cross-Encoder Reranking
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
        Number of final Cross-Encoder results.

    candidate_multiplier:
        Candidate pool multiplier.

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
    # Validate parameters
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
    # Prepare stable IDs
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
    # RRF FUSION
    # --------------------------------------------------------

    # IMPORTANT:
    #
    # RRF must preserve the complete candidate pool.
    #
    # If RRF is truncated to top_k here, the Cross-Encoder
    # would only see those already-selected results.
    #
    # Therefore:
    #
    #   Semantic/BM25 candidate pool
    #              ↓
    #             RRF
    #              ↓
    #       complete RRF pool
    #              ↓
    #        Cross-Encoder
    #              ↓
    #          final Top-K

    unique_candidate_ids = list(
        dict.fromkeys(
            semantic_ids + bm25_ids
        )
    )

    if unique_candidate_ids:

        rrf_results = fuse_semantic_and_bm25(
            semantic_ids=semantic_ids,
            bm25_ids=bm25_ids,
            k=rrf_k,
            semantic_weight=semantic_weight,
            bm25_weight=bm25_weight,
            top_k=len(
                unique_candidate_ids
            ),
        )

    else:

        rrf_results = []

    # --------------------------------------------------------
    # Restore complete metadata
    # --------------------------------------------------------

    rrf_hybrid_results = _build_fused_results(
        rrf_results=rrf_results,
        semantic_results=semantic_results,
        bm25_results=bm25_results,
    )

    # --------------------------------------------------------
    # Cross-Encoder reranking
    # --------------------------------------------------------

    final_results = _rerank_fused_results(
        query=query,
        fused_results=rrf_hybrid_results,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return HybridRetrievalResult(
        query=query,

        semantic_results=semantic_results,

        bm25_results=bm25_results,

        rrf_results=rrf_hybrid_results,

        fused_results=final_results,

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
    Print semantic candidates.
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
    Print BM25 candidates.
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
# DISPLAY: RRF CANDIDATES
# ============================================================


def print_rrf_results(
    results: list[HybridResult],
) -> None:
    """
    Print the complete RRF candidate pool.
    """

    print()
    print("=" * 60)
    print("RRF CANDIDATE POOL")
    print("=" * 60)

    if not results:
        print("No RRF candidates.")
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


# ============================================================
# DISPLAY: FINAL RERANKED RESULTS
# ============================================================


def print_fused_results(
    results: list[HybridResult],
) -> None:
    """
    Print final Cross-Encoder reranked results.
    """

    print()
    print("=" * 60)
    print("CROSS-ENCODER RERANKED RESULTS")
    print("=" * 60)

    if not results:
        print("No reranked results.")
        return

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"[{rank}] "
            f"reranker="
            f"{result.reranker_score:.6f}"
        )

        print(
            f"    point_id      : "
            f"{result.point_id}"
        )

        print(
            f"    RRF           : "
            f"{result.rrf_score:.8f}"
        )

        print(
            f"    rerank_rank   : "
            f"{result.rerank_rank}"
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
                f"    pattern       : "
                f"{semantic.pattern}"
            )

            print(
                f"    sub_pattern   : "
                f"{semantic.sub_pattern}"
            )

            print(
                f"    timestamp     : "
                f"{semantic.start:.2f}s → "
                f"{semantic.end:.2f}s"
            )

        bm25 = result.bm25_document

        if bm25 is not None:

            print(
                "    bm25          : "
                "available"
            )

            print(
                f"    bm25 chunk    : "
                f"{bm25.chunk_id}"
            )


# ============================================================
# DISPLAY: COMPLETE PIPELINE
# ============================================================


def print_hybrid_results(
    result: HybridRetrievalResult,
) -> None:
    """
    Print the complete hybrid retrieval pipeline.
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

    print_rrf_results(
        result.rrf_results
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
    # Cross-Encoder
    # --------------------------------------------------------

    if callable(rerank):

        print(
            "✓ Cross-Encoder reranking interface available."
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