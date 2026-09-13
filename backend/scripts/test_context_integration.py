"""
Phase 12 Context Integration Test.

Validates the integration between:

    Hybrid Retrieval
        -> RRF Fusion
        -> Cross-Encoder Reranking
        -> Context Assembly
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PYTHON PATH
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# IMPORTS
# ============================================================

from app.services.context_assembler import assemble_context
from app.services.hybrid_retrieval import retrieve_hybrid


# ============================================================
# CONFIGURATION
# ============================================================

QUERY = "memoization"

PATTERN = "dynamic_programming"

SUB_PATTERN = "memoization"

TOP_K = 5

CANDIDATE_MULTIPLIER = 3

RRF_K = 60.0


# ============================================================
# ASSERTION HELPER
# ============================================================


def assert_true(
    condition: bool,
    message: str,
) -> None:
    """Raise a readable assertion error when validation fails."""

    if not condition:
        raise AssertionError(message)


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    print("=" * 60)
    print("PHASE 12 CONTEXT INTEGRATION TEST")
    print("=" * 60)

    print(f"Query        : {QUERY}")
    print(f"Pattern      : {PATTERN}")
    print(f"Sub-pattern  : {SUB_PATTERN}")
    print(f"Top-K        : {TOP_K}")
    print(
        f"Candidate K  : "
        f"{TOP_K * CANDIDATE_MULTIPLIER}"
    )

    # ========================================================
    # STEP 1 — HYBRID RETRIEVAL
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 1 — HYBRID RETRIEVAL")
    print("=" * 60)

    retrieval_result = retrieve_hybrid(
        query=QUERY,
        pattern=PATTERN,
        sub_pattern=SUB_PATTERN,
        top_k=TOP_K,
        candidate_multiplier=CANDIDATE_MULTIPLIER,
        rrf_k=RRF_K,
    )

    # --------------------------------------------------------
    # Validate result object
    # --------------------------------------------------------

    assert_true(
        retrieval_result.query == QUERY,
        "Hybrid result query does not match input query.",
    )

    assert_true(
        retrieval_result.pattern == PATTERN,
        "Hybrid result pattern does not match input pattern.",
    )

    assert_true(
        retrieval_result.sub_pattern == SUB_PATTERN,
        "Hybrid result sub-pattern does not match input.",
    )

    print("✓ Hybrid retrieval metadata validated.")

    # --------------------------------------------------------
    # Validate retrieval stages
    # --------------------------------------------------------

    assert_true(
        retrieval_result.semantic_results,
        "Semantic retrieval returned no candidates.",
    )

    assert_true(
        retrieval_result.bm25_results,
        "BM25 retrieval returned no candidates.",
    )

    assert_true(
        retrieval_result.rrf_results,
        "RRF fusion returned no candidates.",
    )

    assert_true(
        retrieval_result.fused_results,
        "Cross-Encoder reranking returned no final results.",
    )

    print("✓ Semantic retrieval results available.")

    print("✓ BM25 retrieval results available.")

    print("✓ RRF fused results available.")

    print("✓ Cross-Encoder reranked results available.")

    # --------------------------------------------------------
    # Validate final Top-K
    # --------------------------------------------------------

    fused_results = retrieval_result.fused_results

    assert_true(
        len(fused_results) <= TOP_K,
        (
            "Cross-Encoder final results exceeded "
            "configured Top-K."
        ),
    )

    print(
        f"✓ Final reranked Top-K validated "
        f"(returned={len(fused_results)}, max={TOP_K})."
    )

    # --------------------------------------------------------
    # Validate Cross-Encoder scores
    # --------------------------------------------------------

    for index, result in enumerate(
        fused_results,
        start=1,
    ):

        assert_true(
            result.point_id,
            f"Final result {index} has no point_id.",
        )

        assert_true(
            result.reranker_score is not None,
            (
                f"Final result {index} has no "
                "Cross-Encoder score."
            ),
        )

        assert_true(
            result.rrf_score is not None,
            (
                f"Final result {index} has no "
                "RRF score."
            ),
        )

    print(
        "✓ RRF and Cross-Encoder scores preserved."
    )

    # ========================================================
    # STEP 2 — CONTEXT ASSEMBLY
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 2 — CONTEXT ASSEMBLY")
    print("=" * 60)

    context = assemble_context(
        query=QUERY,
        pattern=PATTERN,
        sub_pattern=SUB_PATTERN,
        results=fused_results,
        top_k=TOP_K,
    )

    # --------------------------------------------------------
    # Validate context metadata
    # --------------------------------------------------------

    assert_true(
        context.query == QUERY,
        "Context query does not match original query.",
    )

    assert_true(
        context.pattern == PATTERN,
        "Context pattern does not match original pattern.",
    )

    assert_true(
        context.sub_pattern == SUB_PATTERN,
        (
            "Context sub-pattern does not match "
            "original sub-pattern."
        ),
    )

    print(
        "✓ Context metadata preserved."
    )

    # --------------------------------------------------------
    # Validate context item count
    # --------------------------------------------------------

    assert_true(
        0 < len(context.items) <= TOP_K,
        (
            "Context item count is outside "
            "expected Top-K range."
        ),
    )

    print(
        f"✓ Context item count validated "
        f"({len(context.items)} items)."
    )

    # --------------------------------------------------------
    # Validate point IDs
    # --------------------------------------------------------

    point_ids = [
        item.point_id
        for item in context.items
    ]

    assert_true(
        len(point_ids) == len(set(point_ids)),
        "Duplicate point IDs detected.",
    )

    print(
        "✓ Duplicate handling validated."
    )

    # --------------------------------------------------------
    # Validate ranks
    # --------------------------------------------------------

    expected_ranks = list(
        range(
            1,
            len(context.items) + 1,
        )
    )

    actual_ranks = [
        item.rank
        for item in context.items
    ]

    assert_true(
        actual_ranks == expected_ranks,
        "Context ranks are not sequential.",
    )

    print(
        "✓ Context ranks validated."
    )

    # --------------------------------------------------------
    # Validate text
    # --------------------------------------------------------

    for index, item in enumerate(
        context.items,
        start=1,
    ):

        assert_true(
            isinstance(item.text, str),
            f"Context item {index} text is not a string.",
        )

        assert_true(
            item.text.strip(),
            f"Context item {index} has empty text.",
        )

    print(
        "✓ Chunk text preserved."
    )

    # ========================================================
    # STEP 3 — RANKING METADATA PRESERVATION
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 3 — RANKING METADATA PRESERVATION")
    print("=" * 60)

    for index, item in enumerate(
        context.items,
        start=1,
    ):

        assert_true(
            item.rrf_score is not None,
            f"Context item {index} lost RRF score.",
        )

        assert_true(
            item.reranker_score is not None,
            (
                f"Context item {index} lost "
                "Cross-Encoder score."
            ),
        )

    print(
        "✓ RRF scores preserved."
    )

    print(
        "✓ Cross-Encoder scores preserved."
    )

    # ========================================================
    # STEP 4 — LLM-READY CONTEXT
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 4 — LLM-READY CONTEXT")
    print("=" * 60)

    context_text = context.text

    assert_true(
        isinstance(context_text, str),
        "Generated context is not a string.",
    )

    assert_true(
        context_text.strip(),
        "Generated context is empty.",
    )

    assert_true(
        "[Context 1]" in context_text,
        "Generated context is missing Context 1 marker.",
    )

    print(
        "✓ LLM-ready context generated."
    )

    # ========================================================
    # STEP 5 — SERIALIZATION
    # ========================================================

    print()
    print("=" * 60)
    print("STEP 5 — SERIALIZATION")
    print("=" * 60)

    payload = context.to_dict()

    assert_true(
        isinstance(payload, dict),
        "Context serialization did not return a dictionary.",
    )

    assert_true(
        payload["query"] == QUERY,
        "Serialized query is incorrect.",
    )

    assert_true(
        payload["pattern"] == PATTERN,
        "Serialized pattern is incorrect.",
    )

    assert_true(
        payload["sub_pattern"] == SUB_PATTERN,
        "Serialized sub-pattern is incorrect.",
    )

    assert_true(
        len(payload["items"]) == len(context.items),
        "Serialized item count does not match context.",
    )

    print(
        "✓ Dictionary serialization validated."
    )

    # ========================================================
    # FINAL CONTEXT PREVIEW
    # ========================================================

    print()
    print("=" * 60)
    print("FINAL ASSEMBLED CONTEXT")
    print("=" * 60)

    for item in context.items:

        print()

        print(
            f"[{item.rank}] "
            f"point_id={item.point_id}"
        )

        print(
            f"    video_id       : {item.video_id}"
        )

        print(
            f"    pattern        : {item.pattern}"
        )

        print(
            f"    sub_pattern    : {item.sub_pattern}"
        )

        print(
            f"    RRF score      : {item.rrf_score}"
        )

        print(
            f"    CE score       : {item.reranker_score}"
        )

        print(
            f"    timestamp      : "
            f"{item.timestamp_start} -> "
            f"{item.timestamp_end}"
        )

        preview = (
            item.text
            .replace("\n", " ")
            .strip()
        )

        if len(preview) > 120:
            preview = preview[:120] + "..."

        print(
            f"    text           : {preview}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print("PHASE 12 CONTEXT INTEGRATION SUMMARY")
    print("=" * 60)

    print("✓ Hybrid retrieval completed.")

    print("✓ RRF fusion completed.")

    print("✓ Cross-Encoder reranking completed.")

    print("✓ Final Top-K validated.")

    print("✓ Context Assembly completed.")

    print("✓ Context metadata preserved.")

    print("✓ Stable point IDs preserved.")

    print("✓ Chunk text preserved.")

    print("✓ RRF scores preserved.")

    print("✓ Cross-Encoder scores preserved.")

    print("✓ LLM-ready context generated.")

    print("✓ Dictionary serialization validated.")

    print()
    print(
        "✓ PHASE 12 CONTEXT INTEGRATION PASSED"
    )


# ============================================================
# ENTRY POINT
# ============================================================


if __name__ == "__main__":
    main()