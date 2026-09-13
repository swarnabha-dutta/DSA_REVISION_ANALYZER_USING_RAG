"""
Phase 12 Context Assembly Test.

This test validates the Context Assembly layer independently
from the retrieval infrastructure.

It uses lightweight mock retrieval results, so it does not
load Qdrant, BM25, embedding models, or the Cross-Encoder.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


# ============================================================
# PYTHON PATH
# ============================================================

# Add backend/ to sys.path so that:
#
#     from app.services.context_assembler import ...
#
# works when this script is executed as:
#
#     python .\scripts\test_context_assembly.py
#

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# IMPORT
# ============================================================

from app.services.context_assembler import (  # noqa: E402
    assemble_context,
)


# ============================================================
# MOCK RETRIEVAL OBJECTS
# ============================================================


@dataclass
class MockSemanticResult:
    """Minimal semantic retrieval result used by the test."""

    point_id: str
    text: str
    video_id: str
    pattern: str
    sub_pattern: str
    timestamp_start: float
    timestamp_end: float


@dataclass
class MockHybridResult:
    """Minimal hybrid retrieval result used by the test."""

    point_id: str
    rrf_score: float
    reranker_score: float

    semantic_result: MockSemanticResult | None = None
    bm25_document: object | None = None


# ============================================================
# TEST DATA
# ============================================================


def build_test_results() -> list[MockHybridResult]:
    """
    Build deterministic mock results representing the output
    of the Phase 11 hybrid retrieval + reranking pipeline.
    """

    return [
        MockHybridResult(
            point_id="point-001",
            rrf_score=0.0315,
            reranker_score=9.80,
            semantic_result=MockSemanticResult(
                point_id="point-001",
                text=(
                    "Memoization stores previously computed "
                    "subproblem results."
                ),
                video_id="video-001",
                pattern="dynamic_programming",
                sub_pattern="memoization",
                timestamp_start=100.0,
                timestamp_end=130.0,
            ),
        ),
        MockHybridResult(
            point_id="point-002",
            rrf_score=0.0301,
            reranker_score=9.20,
            semantic_result=MockSemanticResult(
                point_id="point-002",
                text=(
                    "Overlapping subproblems can be solved "
                    "efficiently by reusing computed values."
                ),
                video_id="video-001",
                pattern="dynamic_programming",
                sub_pattern="memoization",
                timestamp_start=130.0,
                timestamp_end=165.0,
            ),
        ),
        MockHybridResult(
            point_id="point-003",
            rrf_score=0.0287,
            reranker_score=8.90,
            semantic_result=MockSemanticResult(
                point_id="point-003",
                text=(
                    "Top-down dynamic programming combines "
                    "recursion with memoization."
                ),
                video_id="video-001",
                pattern="dynamic_programming",
                sub_pattern="memoization",
                timestamp_start=165.0,
                timestamp_end=200.0,
            ),
        ),
        MockHybridResult(
            point_id="point-004",
            rrf_score=0.0271,
            reranker_score=8.50,
            semantic_result=MockSemanticResult(
                point_id="point-004",
                text=(
                    "Repeated subproblems should not be "
                    "recomputed unnecessarily."
                ),
                video_id="video-001",
                pattern="dynamic_programming",
                sub_pattern="memoization",
                timestamp_start=200.0,
                timestamp_end=235.0,
            ),
        ),
        MockHybridResult(
            point_id="point-005",
            rrf_score=0.0264,
            reranker_score=8.10,
            semantic_result=MockSemanticResult(
                point_id="point-005",
                text=(
                    "Caching results reduces repeated work "
                    "during recursive computation."
                ),
                video_id="video-001",
                pattern="dynamic_programming",
                sub_pattern="memoization",
                timestamp_start=235.0,
                timestamp_end=270.0,
            ),
        ),
    ]


# ============================================================
# ASSERTION HELPER
# ============================================================


def assert_true(
    condition: bool,
    message: str,
) -> None:
    """Raise a readable assertion error when a test fails."""

    if not condition:
        raise AssertionError(message)


# ============================================================
# TEST 1 — TOP-K
# ============================================================


def test_top_k_limit() -> None:
    """Verify that the requested Top-K is respected."""

    results = build_test_results()

    context = assemble_context(
        query="memoization",
        pattern="dynamic_programming",
        sub_pattern="memoization",
        results=results,
        top_k=3,
    )

    assert_true(
        len(context.items) == 3,
        "Top-K limit was not respected.",
    )


# ============================================================
# TEST 2 — RANK ORDER
# ============================================================


def test_rank_order() -> None:
    """Verify that reranked result order is preserved."""

    results = build_test_results()

    context = assemble_context(
        query="memoization",
        pattern="dynamic_programming",
        sub_pattern="memoization",
        results=results,
        top_k=5,
    )

    ids = [
        item.point_id
        for item in context.items
    ]

    expected = [
        "point-001",
        "point-002",
        "point-003",
        "point-004",
        "point-005",
    ]

    assert_true(
        ids == expected,
        "Reranked order was not preserved.",
    )

    ranks = [
        item.rank
        for item in context.items
    ]

    assert_true(
        ranks == [1, 2, 3, 4, 5],
        "Context ranks are incorrect.",
    )


# ============================================================
# TEST 3 — TEXT PRESERVATION
# ============================================================


def test_text_preservation() -> None:
    """Verify that retrieved chunk text is preserved."""

    results = build_test_results()

    context = assemble_context(
        query="memoization",
        results=results,
        top_k=5,
    )

    assert_true(
        (
            "Memoization stores previously computed"
            in context.items[0].text
        ),
        "Chunk text was not preserved.",
    )


# ============================================================
# TEST 4 — METADATA PRESERVATION
# ============================================================


def test_metadata_preservation() -> None:
    """Verify that retrieval metadata survives context assembly."""

    results = build_test_results()

    context = assemble_context(
        query="memoization",
        pattern="dynamic_programming",
        sub_pattern="memoization",
        results=results,
        top_k=1,
    )

    item = context.items[0]

    assert_true(
        item.point_id == "point-001",
        "point_id was not preserved.",
    )

    assert_true(
        item.video_id == "video-001",
        "video_id was not preserved.",
    )

    assert_true(
        item.pattern == "dynamic_programming",
        "pattern was not preserved.",
    )

    assert_true(
        item.sub_pattern == "memoization",
        "sub_pattern was not preserved.",
    )

    assert_true(
        item.timestamp_start == 100.0,
        "timestamp_start was not preserved.",
    )

    assert_true(
        item.timestamp_end == 130.0,
        "timestamp_end was not preserved.",
    )


# ============================================================
# TEST 5 — SCORE PRESERVATION
# ============================================================


def test_score_preservation() -> None:
    """Verify that RRF and Cross-Encoder scores are preserved."""

    results = build_test_results()

    context = assemble_context(
        query="memoization",
        results=results,
        top_k=1,
    )

    item = context.items[0]

    assert_true(
        item.rrf_score == 0.0315,
        "RRF score was not preserved.",
    )

    assert_true(
        item.reranker_score == 9.80,
        "Reranker score was not preserved.",
    )


# ============================================================
# TEST 6 — DUPLICATE HANDLING
# ============================================================


def test_duplicate_handling() -> None:
    """Verify that duplicate point IDs are removed."""

    results = build_test_results()

    duplicated_results = [
        results[0],
        results[0],
        results[1],
        results[1],
        results[2],
    ]

    context = assemble_context(
        query="memoization",
        results=duplicated_results,
        top_k=5,
    )

    ids = [
        item.point_id
        for item in context.items
    ]

    assert_true(
        len(ids) == len(set(ids)),
        "Duplicate point IDs were not removed.",
    )


# ============================================================
# TEST 7 — EMPTY RESULTS
# ============================================================


def test_empty_results() -> None:
    """Verify safe handling of empty retrieval results."""

    context = assemble_context(
        query="memoization",
        pattern="dynamic_programming",
        sub_pattern="memoization",
        results=[],
        top_k=5,
    )

    assert_true(
        context.items == [],
        "Empty retrieval should produce empty context.",
    )

    assert_true(
        context.text == "",
        "Empty context text should be empty.",
    )


# ============================================================
# TEST 8 — CONTEXT TEXT
# ============================================================


def test_context_text() -> None:
    """Verify deterministic LLM-ready text generation."""

    results = build_test_results()

    context = assemble_context(
        query="memoization",
        results=results,
        top_k=2,
    )

    text = context.text

    assert_true(
        "[Context 1]" in text,
        "Context 1 marker missing.",
    )

    assert_true(
        "[Context 2]" in text,
        "Context 2 marker missing.",
    )

    assert_true(
        "Point ID: point-001" in text,
        "Point ID missing from context text.",
    )

    assert_true(
        "Video ID: video-001" in text,
        "Video ID missing from context text.",
    )


# ============================================================
# TEST 9 — SERIALIZATION
# ============================================================


def test_dictionary_serialization() -> None:
    """Verify conversion to a JSON-compatible dictionary."""

    results = build_test_results()

    context = assemble_context(
        query="memoization",
        pattern="dynamic_programming",
        sub_pattern="memoization",
        results=results,
        top_k=2,
    )

    payload = context.to_dict()

    assert_true(
        payload["query"] == "memoization",
        "Query missing from serialized context.",
    )

    assert_true(
        payload["pattern"] == "dynamic_programming",
        "Pattern missing from serialized context.",
    )

    assert_true(
        payload["sub_pattern"] == "memoization",
        "Sub-pattern missing from serialized context.",
    )

    assert_true(
        len(payload["items"]) == 2,
        "Serialized Top-K is incorrect.",
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    """Run all Phase 12 Context Assembly tests."""

    print("=" * 60)
    print("PHASE 12 CONTEXT ASSEMBLY TEST")
    print("=" * 60)

    tests = [
        (
            "Top-K limit",
            test_top_k_limit,
        ),
        (
            "Reranked order preservation",
            test_rank_order,
        ),
        (
            "Chunk text preservation",
            test_text_preservation,
        ),
        (
            "Metadata preservation",
            test_metadata_preservation,
        ),
        (
            "Score preservation",
            test_score_preservation,
        ),
        (
            "Duplicate handling",
            test_duplicate_handling,
        ),
        (
            "Empty result handling",
            test_empty_results,
        ),
        (
            "Context text generation",
            test_context_text,
        ),
        (
            "Dictionary serialization",
            test_dictionary_serialization,
        ),
    ]

    passed = 0

    for name, test in tests:

        try:
            test()

            print(
                f"✓ {name} passed"
            )

            passed += 1

        except Exception as exc:

            print(
                f"✗ {name} FAILED"
            )

            print(
                f"  {exc}"
            )

    print()
    print("=" * 60)
    print("PHASE 12 CONTEXT ASSEMBLY SUMMARY")
    print("=" * 60)

    print(
        f"Passed : {passed}/{len(tests)}"
    )

    if passed != len(tests):

        print()
        print(
            "✗ CONTEXT ASSEMBLY TEST FAILED"
        )

        raise SystemExit(1)

    print()
    print(
        "✓ CONTEXT ASSEMBLY TEST PASSED"
    )


if __name__ == "__main__":
    main()