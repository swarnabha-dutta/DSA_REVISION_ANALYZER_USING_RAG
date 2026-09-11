"""
RRF Unit / Integration Test
===========================

Tests Reciprocal Rank Fusion independently from Qdrant and BM25.

This verifies:

    1. Basic two-list fusion
    2. Rank-based scoring
    3. Documents appearing in both systems
    4. Documents appearing in only one system
    5. Duplicate handling
    6. Weight handling
    7. Top-K limiting
"""


from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# IMPORT
# ============================================================

from app.services.rrf import (  # noqa: E402
    fuse_semantic_and_bm25,
    reciprocal_rank_fusion,
    print_rrf_results,
)


# ============================================================
# TEST 1 — BASIC FUSION
# ============================================================

def test_basic_fusion() -> None:

    semantic = [
        "A",
        "B",
        "C",
        "D",
    ]

    bm25 = [
        "C",
        "A",
        "E",
        "B",
    ]

    results = fuse_semantic_and_bm25(
        semantic_ids=semantic,
        bm25_ids=bm25,
    )

    assert len(results) == 5

    # C and A appear highly ranked in both systems.
    # They should therefore appear near the top.
    top_ids = [
        result.document_id
        for result in results[:2]
    ]

    assert set(top_ids) == {
        "A",
        "C",
    }

    print(
        "✓ Basic fusion test passed."
    )


# ============================================================
# TEST 2 — EXACT SCORE
# ============================================================

def test_exact_score() -> None:

    results = reciprocal_rank_fusion(
        rankings={
            "semantic": ["A"],
            "bm25": ["A"],
        },
        k=60,
    )

    assert len(results) == 1

    expected = (
        1 / 61
        + 1 / 61
    )

    actual = results[0].score

    assert abs(
        actual - expected
    ) < 1e-12

    print(
        "✓ Exact RRF score test passed."
    )


# ============================================================
# TEST 3 — DUPLICATES
# ============================================================

def test_duplicate_handling() -> None:

    results = reciprocal_rank_fusion(
        rankings={
            "semantic": [
                "A",
                "A",
                "B",
            ],
            "bm25": [
                "B",
            ],
        }
    )

    result_map = {
        result.document_id: result
        for result in results
    }

    # A should receive only its first semantic rank.
    expected_a = 1 / 61

    assert abs(
        result_map["A"].score
        - expected_a
    ) < 1e-12

    # B receives semantic rank 3 + BM25 rank 1.
    expected_b = (
        1 / 63
        + 1 / 61
    )

    assert abs(
        result_map["B"].score
        - expected_b
    ) < 1e-12

    print(
        "✓ Duplicate handling test passed."
    )


# ============================================================
# TEST 4 — WEIGHTS
# ============================================================

def test_weights() -> None:

    results = reciprocal_rank_fusion(
        rankings={
            "semantic": ["A"],
            "bm25": ["B"],
        },
        weights={
            "semantic": 2.0,
            "bm25": 1.0,
        },
    )

    result_map = {
        result.document_id: result
        for result in results
    }

    assert (
        result_map["A"].score
        >
        result_map["B"].score
    )

    print(
        "✓ Weight test passed."
    )


# ============================================================
# TEST 5 — TOP-K
# ============================================================

def test_top_k() -> None:

    results = reciprocal_rank_fusion(
        rankings={
            "semantic": [
                "A",
                "B",
                "C",
                "D",
            ],
            "bm25": [
                "D",
                "C",
                "B",
                "A",
            ],
        },
        top_k=2,
    )

    assert len(results) == 2

    print(
        "✓ Top-K test passed."
    )


# ============================================================
# DEMO
# ============================================================

def run_demo() -> None:

    semantic = [
        "chunk_A",
        "chunk_B",
        "chunk_C",
        "chunk_D",
        "chunk_E",
    ]

    bm25 = [
        "chunk_C",
        "chunk_A",
        "chunk_F",
        "chunk_B",
        "chunk_G",
    ]

    results = fuse_semantic_and_bm25(
        semantic_ids=semantic,
        bm25_ids=bm25,
        top_k=7,
    )

    print()
    print(
        "RRF DEMO"
    )

    print_rrf_results(
        results
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print(
        "=" * 60
    )

    print(
        "RRF TEST SUITE"
    )

    print(
        "=" * 60
    )

    test_basic_fusion()
    test_exact_score()
    test_duplicate_handling()
    test_weights()
    test_top_k()

    run_demo()

    print()
    print(
        "=" * 60
    )

    print(
        "✓ ALL RRF TESTS PASSED"
    )

    print(
        "=" * 60
    )


if __name__ == "__main__":

    main()