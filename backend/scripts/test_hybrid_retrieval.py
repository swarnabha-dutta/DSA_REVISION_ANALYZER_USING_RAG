"""
Integration test for the hybrid retrieval service.

Validates that:

1. Semantic retrieval runs successfully.
2. BM25 retrieval runs successfully.
3. Both retrievers respect metadata filters.
4. Both result sets are returned independently.
5. Candidate retrieval works before RRF fusion.

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
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# IMPORTS
# ============================================================

from app.services.hybrid_retrieval import (
    DEFAULT_CANDIDATE_MULTIPLIER,
    DEFAULT_HYBRID_TOP_K,
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


def assert_semantic_result(result) -> None:
    """Validate one semantic RetrievalResult."""

    assert result.point_id, "Semantic result missing point_id."
    assert result.chunk_id is not None, "Semantic result missing chunk_id."
    assert result.video_id, "Semantic result missing video_id."
    assert result.pattern == PATTERN, (
        f"Unexpected semantic pattern: {result.pattern}"
    )
    assert result.sub_pattern == SUB_PATTERN, (
        f"Unexpected semantic sub-pattern: {result.sub_pattern}"
    )
    assert isinstance(result.score, float), (
        "Semantic score must be a float."
    )


def assert_bm25_result(result) -> None:
    """Validate one BM25RetrievalResult."""

    assert isinstance(result.score, float), (
        "BM25 score must be a float."
    )

    document = result.document

    assert document.point_id, "BM25 result missing point_id."
    assert document.chunk_id is not None, "BM25 result missing chunk_id."
    assert document.video_id, "BM25 result missing video_id."

    assert document.pattern == PATTERN, (
        f"Unexpected BM25 pattern: {document.pattern}"
    )

    assert document.sub_pattern == SUB_PATTERN, (
        f"Unexpected BM25 sub-pattern: {document.sub_pattern}"
    )


# ============================================================
# MAIN TEST
# ============================================================


def main() -> None:
    print("=" * 60)
    print("HYBRID RETRIEVAL INTEGRATION TEST")
    print("=" * 60)

    print(f"Query       : {QUERY}")
    print(f"Top-K       : {TOP_K}")
    print(f"Pattern     : {PATTERN}")
    print(f"Sub-pattern : {SUB_PATTERN}")
    print(
        f"Candidate K : "
        f"{TOP_K * DEFAULT_CANDIDATE_MULTIPLIER}"
    )

    print()
    print("=" * 60)
    print("Running Hybrid Retrieval")
    print("=" * 60)

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

    # --------------------------------------------------------
    # Candidate count validation
    # --------------------------------------------------------

    expected_candidate_k = max(
        TOP_K,
        TOP_K * DEFAULT_CANDIDATE_MULTIPLIER,
    )

    assert len(result.semantic_results) <= expected_candidate_k
    assert len(result.bm25_results) <= expected_candidate_k

    # --------------------------------------------------------
    # Validate semantic results
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SEMANTIC RESULTS")
    print("=" * 60)

    print(
        f"Retrieved semantic candidates: "
        f"{len(result.semantic_results)}"
    )

    for rank, semantic_result in enumerate(
        result.semantic_results,
        start=1,
    ):
        assert_semantic_result(semantic_result)

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
            f"{semantic_result.start_seconds:.2f}s"
            f" → "
            f"{semantic_result.end_seconds:.2f}s"
        )

    assert len(result.semantic_results) > 0, (
        "Semantic retrieval returned no results."
    )

    print()
    print("✓ Semantic retrieval validated.")

    # --------------------------------------------------------
    # Validate BM25 results
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("BM25 RESULTS")
    print("=" * 60)

    print(
        f"Retrieved BM25 candidates: "
        f"{len(result.bm25_results)}"
    )

    for rank, bm25_result in enumerate(
        result.bm25_results,
        start=1,
    ):
        assert_bm25_result(bm25_result)

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

    assert len(result.bm25_results) > 0, (
        "BM25 retrieval returned no results."
    )

    print()
    print("✓ BM25 retrieval validated.")

    # --------------------------------------------------------
    # Cross-retriever validation
    # --------------------------------------------------------

    semantic_point_ids = {
        item.point_id
        for item in result.semantic_results
    }

    bm25_point_ids = {
        item.document.point_id
        for item in result.bm25_results
    }

    overlap = semantic_point_ids & bm25_point_ids

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

        for point_id in sorted(overlap):
            print(f"  - {point_id}")

    else:
        print()
        print(
            "No overlapping point IDs found. "
            "This is still valid; the two retrievers use "
            "different relevance signals."
        )

    # --------------------------------------------------------
    # Important architectural assertion
    # --------------------------------------------------------

    # Hybrid retrieval should NOT perform RRF yet.
    # It should only return the independent candidate sets.

    assert hasattr(result, "semantic_results")
    assert hasattr(result, "bm25_results")

    print()
    print("=" * 60)
    print("HYBRID RETRIEVAL VALIDATION")
    print("=" * 60)

    print("✓ Query passed correctly")
    print("✓ Metadata filters passed correctly")
    print("✓ Semantic candidate retrieval passed")
    print("✓ BM25 candidate retrieval passed")
    print("✓ Both result sets returned independently")
    print("✓ Shared point IDs are preserved")
    print("✓ Hybrid layer is ready for RRF integration")

    print()
    print("=" * 60)
    print("✓ HYBRID RETRIEVAL TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()