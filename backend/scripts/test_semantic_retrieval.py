"""
Semantic Retrieval Integration Test
===================================

Purpose:
    Verify that the semantic retrieval service can:

    1. Accept a natural-language query.
    2. Generate an embedding.
    3. Search Qdrant.
    4. Apply metadata filters.
    5. Return RetrievalResult objects.
    6. Preserve Qdrant point_id.
    7. Return the expected transcript metadata.

This test intentionally does NOT involve:
    - BM25
    - Hybrid retrieval
    - RRF

Those will be tested separately.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# RETRIEVAL SERVICE
# ============================================================

from app.services.retrieval import retrieve


# ============================================================
# TEST CONFIGURATION
# ============================================================

QUERY = "memoization"

TOP_K = 5

PATTERN = "dynamic_programming"

SUB_PATTERN = "memoization"


# ============================================================
# MAIN TEST
# ============================================================

def main() -> None:

    print("=" * 60)
    print("SEMANTIC RETRIEVAL INTEGRATION TEST")
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

    print()

    # --------------------------------------------------------
    # Execute semantic retrieval
    # --------------------------------------------------------

    print("=" * 60)
    print("Running Semantic Retrieval")
    print("=" * 60)

    results = retrieve(
        QUERY,
        top_k=TOP_K,
        pattern=PATTERN,
        sub_pattern=SUB_PATTERN,
    )

    print(
        f"Retrieved results: {len(results)}"
    )

    print()

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if not results:

        raise AssertionError(
            "Semantic retrieval returned zero results."
        )

    if len(results) > TOP_K:

        raise AssertionError(
            "Semantic retrieval returned more than Top-K results."
        )

    # --------------------------------------------------------
    # Validate result structure
    # --------------------------------------------------------

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"[{index}] "
            f"score={result.score:.4f}"
        )

        print(
            f"    point_id   : {result.point_id}"
        )

        print(
            f"    chunk_id   : {result.chunk_id}"
        )

        print(
            f"    video_id   : {result.video_id}"
        )

        print(
            f"    pattern    : {result.pattern}"
        )

        print(
            f"    sub_pattern: {result.sub_pattern}"
        )

        print(
            f"    timestamp  : "
            f"{result.start:.2f}s"
            f" → "
            f"{result.end:.2f}s"
        )

        print(
            f"    text       : "
            f"{result.text[:200]}"
        )

        print()

        # ----------------------------------------------------
        # Required identity validation
        # ----------------------------------------------------

        if not result.point_id:

            raise AssertionError(
                f"Result {index} has an empty point_id."
            )

        # ----------------------------------------------------
        # Score validation
        # ----------------------------------------------------

        if not isinstance(
            result.score,
            float,
        ):

            raise AssertionError(
                f"Result {index} score is not a float."
            )

        # ----------------------------------------------------
        # Text validation
        # ----------------------------------------------------

        if not result.text:

            raise AssertionError(
                f"Result {index} has empty transcript text."
            )

        # ----------------------------------------------------
        # Filter validation
        # ----------------------------------------------------

        if result.pattern != PATTERN:

            raise AssertionError(
                f"Result {index} returned an unexpected "
                f"pattern: {result.pattern}"
            )

        if result.sub_pattern != SUB_PATTERN:

            raise AssertionError(
                f"Result {index} returned an unexpected "
                f"sub-pattern: {result.sub_pattern}"
            )

    # --------------------------------------------------------
    # Point ID uniqueness
    # --------------------------------------------------------

    point_ids = [
        result.point_id
        for result in results
    ]

    if len(point_ids) != len(set(point_ids)):

        raise AssertionError(
            "Duplicate point_id detected in semantic results."
        )

    # --------------------------------------------------------
    # Ranking validation
    # --------------------------------------------------------

    scores = [
        result.score
        for result in results
    ]

    if scores != sorted(
        scores,
        reverse=True,
    ):

        raise AssertionError(
            "Semantic results are not ordered by descending score."
        )

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print("=" * 60)
    print("✓ SEMANTIC RETRIEVAL TEST PASSED")
    print("=" * 60)

    print(
        f"Validated results : {len(results)}"
    )

    print(
        "✓ Qdrant retrieval"
    )

    print(
        "✓ Query embedding"
    )

    print(
        "✓ Metadata filtering"
    )

    print(
        "✓ RetrievalResult conversion"
    )

    print(
        "✓ point_id preservation"
    )

    print(
        "✓ Result ranking"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()