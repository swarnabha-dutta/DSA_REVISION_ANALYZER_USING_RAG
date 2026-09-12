"""
Integration test for the complete hybrid retrieval pipeline.

Validates:

1. Semantic retrieval works.
2. BM25 retrieval works.
3. Metadata filters are respected.
4. Candidate pool size is correct.
5. Semantic and BM25 use stable point IDs.
6. RRF fusion is executed.
7. Final fused result count is <= Top-K.
8. RRF ranking information is preserved.
9. Semantic/BM25 metadata is restored after fusion.

Run from backend root:

    python scripts/test_hybrid_retrieval.py
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# IMPORTS
# ============================================================

from app.services.hybrid_retrieval import (
    DEFAULT_CANDIDATE_MULTIPLIER,
    DEFAULT_HYBRID_TOP_K,
    HybridResult,
    retrieve_hybrid,
)


# ============================================================
# TEST CONFIGURATION
# ============================================================

QUERY = "memoization"

PATTERN = "dynamic_programming"

SUB_PATTERN = "memoization"

TOP_K = 5


# ============================================================
# ASSERTION HELPERS
# ============================================================

def assert_semantic_result(
    result,
) -> None:
    """
    Validate one semantic RetrievalResult.
    """

    assert result.point_id, (
        "Semantic result missing point_id."
    )

    assert result.chunk_id is not None, (
        "Semantic result missing chunk_id."
    )

    assert result.video_id, (
        "Semantic result missing video_id."
    )

    assert result.pattern == PATTERN, (
        f"Unexpected semantic pattern: "
        f"{result.pattern}"
    )

    assert result.sub_pattern == SUB_PATTERN, (
        f"Unexpected semantic sub-pattern: "
        f"{result.sub_pattern}"
    )

    assert isinstance(
        result.score,
        float,
    ), (
        "Semantic score must be a float."
    )


def assert_bm25_result(
    result,
) -> None:
    """
    Validate one BM25 result.
    """

    assert isinstance(
        result.score,
        float,
    ), (
        "BM25 score must be a float."
    )

    document = result.document

    assert document.point_id, (
        "BM25 result missing point_id."
    )

    assert document.chunk_id is not None, (
        "BM25 result missing chunk_id."
    )

    assert document.video_id, (
        "BM25 result missing video_id."
    )

    assert document.pattern == PATTERN, (
        f"Unexpected BM25 pattern: "
        f"{document.pattern}"
    )

    assert document.sub_pattern == SUB_PATTERN, (
        f"Unexpected BM25 sub-pattern: "
        f"{document.sub_pattern}"
    )


def assert_fused_result(
    result: HybridResult,
) -> None:
    """
    Validate one final HybridResult.
    """

    assert result.point_id, (
        "Fused result missing point_id."
    )

    assert isinstance(
        result.rrf_score,
        float,
    ), (
        "RRF score must be a float."
    )

    assert result.rrf_score > 0, (
        "RRF score must be greater than zero."
    )

    assert isinstance(
        result.rank_positions,
        dict,
    ), (
        "rank_positions must be a dictionary."
    )

    assert isinstance(
        result.contributions,
        dict,
    ), (
        "contributions must be a dictionary."
    )

    assert (
        result.semantic_result is not None
        or result.bm25_document is not None
    ), (
        "Fused result has no underlying "
        "semantic or BM25 document."
    )


# ============================================================
# MAIN TEST
# ============================================================

def main() -> None:

    print("=" * 60)
    print("HYBRID RETRIEVAL INTEGRATION TEST")
    print("=" * 60)

    print(
        f"Query       : {QUERY}"
    )

    print(
        f"Top-K       : {TOP_K}"
    )

    print(
        f"Pattern     : {PATTERN}"
    )

    print(
        f"Sub-pattern : {SUB_PATTERN}"
    )

    expected_candidate_k = max(
        TOP_K,
        TOP_K * DEFAULT_CANDIDATE_MULTIPLIER,
    )

    print(
        f"Candidate K : "
        f"{expected_candidate_k}"
    )

    print()

    print("=" * 60)
    print("Running Complete Hybrid Retrieval")
    print("=" * 60)

    # --------------------------------------------------------
    # Execute complete pipeline
    # --------------------------------------------------------

    result = retrieve_hybrid(
        query=QUERY,
        pattern=PATTERN,
        sub_pattern=SUB_PATTERN,
        top_k=TOP_K,
    )

    # --------------------------------------------------------
    # Basic result validation
    # --------------------------------------------------------

    assert result.query == QUERY

    assert result.pattern == PATTERN

    assert result.sub_pattern == SUB_PATTERN

    print()
    print(
        "✓ Query and metadata validated."
    )

    # --------------------------------------------------------
    # Candidate count validation
    # --------------------------------------------------------

    assert (
        len(result.semantic_results)
        <= expected_candidate_k
    ), (
        "Semantic candidate count exceeded "
        "candidate_k."
    )

    assert (
        len(result.bm25_results)
        <= expected_candidate_k
    ), (
        "BM25 candidate count exceeded "
        "candidate_k."
    )

    print(
        f"✓ Candidate pool validated "
        f"(max={expected_candidate_k})."
    )

    # --------------------------------------------------------
    # Semantic validation
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SEMANTIC RESULTS")
    print("=" * 60)

    print(
        f"Retrieved semantic candidates: "
        f"{len(result.semantic_results)}"
    )

    assert len(result.semantic_results) > 0, (
        "Semantic retrieval returned no results."
    )

    for rank, semantic_result in enumerate(
        result.semantic_results,
        start=1,
    ):

        assert_semantic_result(
            semantic_result
        )

        print(
            f"[{rank}] "
            f"score={semantic_result.score:.4f} "
            f"chunk={semantic_result.chunk_id}"
        )

        print(
            f"    point_id   : "
            f"{semantic_result.point_id}"
        )

        print(
            f"    video_id   : "
            f"{semantic_result.video_id}"
        )

        print(
            f"    pattern    : "
            f"{semantic_result.pattern}"
        )

        print(
            f"    sub_pattern: "
            f"{semantic_result.sub_pattern}"
        )

        print(
            f"    timestamp  : "
            f"{semantic_result.start:.2f}s"
            f" → "
            f"{semantic_result.end:.2f}s"
        )

    print()
    print(
        "✓ Semantic retrieval validated."
    )

    # --------------------------------------------------------
    # BM25 validation
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("BM25 RESULTS")
    print("=" * 60)

    print(
        f"Retrieved BM25 candidates: "
        f"{len(result.bm25_results)}"
    )

    assert len(result.bm25_results) > 0, (
        "BM25 retrieval returned no results."
    )

    for rank, bm25_result in enumerate(
        result.bm25_results,
        start=1,
    ):

        assert_bm25_result(
            bm25_result
        )

        document = bm25_result.document

        print(
            f"[{rank}] "
            f"score={bm25_result.score:.4f} "
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

    print()
    print(
        "✓ BM25 retrieval validated."
    )

    # --------------------------------------------------------
    # Cross-retriever ID validation
    # --------------------------------------------------------

    semantic_point_ids = {
        str(item.point_id)
        for item in result.semantic_results
    }

    bm25_point_ids = {
        str(item.document.point_id)
        for item in result.bm25_results
    }

    overlap = (
        semantic_point_ids
        &
        bm25_point_ids
    )

    print()
    print("=" * 60)
    print("CROSS-RETRIEVER ANALYSIS")
    print("=" * 60)

    print(
        f"Semantic candidates : "
        f"{len(semantic_point_ids)}"
    )

    print(
        f"BM25 candidates     : "
        f"{len(bm25_point_ids)}"
    )

    print(
        f"Overlapping points  : "
        f"{len(overlap)}"
    )

    if overlap:

        print()
        print("Shared point IDs:")

        for point_id in sorted(
            overlap
        ):
            print(
                f"  - {point_id}"
            )

    # --------------------------------------------------------
    # RRF validation
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("RRF FUSED RESULTS")
    print("=" * 60)

    print(
        f"Final fused results: "
        f"{len(result.fused_results)}"
    )

    assert (
        len(result.fused_results)
        <= TOP_K
    ), (
        "RRF returned more than top_k results."
    )

    assert len(result.fused_results) > 0, (
        "RRF fusion returned no results."
    )

    previous_score = None

    for rank, fused_result in enumerate(
        result.fused_results,
        start=1,
    ):

        assert_fused_result(
            fused_result
        )

        print(
            f"[{rank}] "
            f"RRF={fused_result.rrf_score:.8f}"
        )

        print(
            f"    point_id      : "
            f"{fused_result.point_id}"
        )

        print(
            f"    ranks         : "
            f"{fused_result.rank_positions}"
        )

        print(
            f"    contributions : "
            f"{fused_result.contributions}"
        )

        if (
            fused_result.semantic_result
            is not None
        ):

            semantic = (
                fused_result.semantic_result
            )

            print(
                f"    semantic      : "
                f"{semantic.score:.4f}"
            )

            print(
                f"    chunk         : "
                f"{semantic.chunk_id}"
            )

        if (
            fused_result.bm25_document
            is not None
        ):

            bm25 = (
                fused_result.bm25_document
            )

            print(
                f"    bm25          : available"
            )

            print(
                f"    bm25 chunk    : "
                f"{bm25.chunk_id}"
            )

        # RRF results must be descending.
        if previous_score is not None:

            assert (
                fused_result.rrf_score
                <= previous_score
            ), (
                "RRF results are not sorted "
                "in descending score order."
            )

        previous_score = (
            fused_result.rrf_score
        )

    print()
    print(
        "✓ RRF fusion validated."
    )

    # --------------------------------------------------------
    # Stable ID preservation
    # --------------------------------------------------------

    all_source_ids = (
        semantic_point_ids
        |
        bm25_point_ids
    )

    fused_ids = {
        str(item.point_id)
        for item in result.fused_results
    }

    assert fused_ids <= all_source_ids, (
        "RRF produced an unknown point_id."
    )

    print(
        "✓ Stable point_id preservation validated."
    )

    # --------------------------------------------------------
    # Final architecture validation
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("COMPLETE HYBRID RETRIEVAL VALIDATION")
    print("=" * 60)

    print(
        "✓ Query passed correctly"
    )

    print(
        "✓ Metadata filters passed correctly"
    )

    print(
        "✓ Semantic candidate retrieval passed"
    )

    print(
        "✓ BM25 candidate retrieval passed"
    )

    print(
        "✓ Candidate IDs are compatible"
    )

    print(
        "✓ RRF fusion executed"
    )

    print(
        "✓ Final Top-K constraint passed"
    )

    print(
        "✓ RRF ranking order passed"
    )

    print(
        "✓ Metadata restoration passed"
    )

    print()
    print("=" * 60)
    print(
        "✓ COMPLETE HYBRID RETRIEVAL TEST PASSED"
    )
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()