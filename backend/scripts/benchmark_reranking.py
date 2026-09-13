"""
Phase 11 Benchmark: RRF vs Cross-Encoder Reranking

Compares:
    1. RRF-only final Top-K
    2. RRF + Cross-Encoder final Top-K

This benchmark intentionally does NOT claim MRR/nDCG because the project
does not yet have human-validated relevance labels.

Run from backend root:
    python scripts/benchmark_reranking.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from statistics import mean

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.services.hybrid_retrieval import (  # noqa: E402
    DEFAULT_CANDIDATE_MULTIPLIER,
    DEFAULT_HYBRID_TOP_K,
    _build_fused_results,
    retrieve_bm25,
    retrieve_hybrid,
    retrieve_semantic,
)
from app.services.rrf import (  # noqa: E402
    DEFAULT_RRF_K,
    fuse_semantic_and_bm25,
)
from app.services.reranker import rerank  # noqa: E402


# ============================================================
# BENCHMARK CONFIGURATION
# ============================================================

TOP_K = DEFAULT_HYBRID_TOP_K
CANDIDATE_MULTIPLIER = DEFAULT_CANDIDATE_MULTIPLIER
RRF_K = DEFAULT_RRF_K

TEST_CASES = [
    {
        "name": "Memoization",
        "query": "memoization",
        "pattern": "dynamic_programming",
        "sub_pattern": "memoization",
    },
    {
        "name": "Overlapping subproblems",
        "query": "overlapping subproblems",
        "pattern": "dynamic_programming",
        "sub_pattern": "memoization",
    },
    {
        "name": "Top-down DP",
        "query": "top down dynamic programming",
        "pattern": "dynamic_programming",
        "sub_pattern": "memoization",
    },
    {
        "name": "Recursive caching",
        "query": "recursive caching computed results",
        "pattern": "dynamic_programming",
        "sub_pattern": "memoization",
    },
    {
        "name": "Repeated subproblems",
        "query": "repeated subproblems reuse results",
        "pattern": "dynamic_programming",
        "sub_pattern": "memoization",
    },
]


# ============================================================
# HELPERS
# ============================================================


def candidate_k() -> int:
    return max(
        TOP_K,
        TOP_K * CANDIDATE_MULTIPLIER,
    )


def get_candidate_text(result) -> str:
    """Extract text using the same preference as hybrid retrieval."""
    if result.semantic_result is not None:
        text = getattr(
            result.semantic_result,
            "text",
            None,
        )

        if isinstance(text, str) and text.strip():
            return text.strip()

    if result.bm25_document is not None:
        text = getattr(
            result.bm25_document,
            "text",
            None,
        )

        if isinstance(text, str) and text.strip():
            return text.strip()

    raise ValueError(
        "No candidate text available for "
        f"point_id={result.point_id}"
    )


def run_rrf_only(
    *,
    query: str,
    pattern: str | None,
    sub_pattern: str | None,
):
    """
    Execute semantic + BM25 + RRF without Cross-Encoder reranking.
    """
    started = time.perf_counter()

    semantic_results = retrieve_semantic(
        query=query,
        pattern=pattern,
        sub_pattern=sub_pattern,
        candidate_k=candidate_k(),
    )

    bm25_results = retrieve_bm25(
        query=query,
        pattern=pattern,
        sub_pattern=sub_pattern,
        candidate_k=candidate_k(),
    )

    semantic_ids = [
        str(result.point_id)
        for result in semantic_results
    ]

    bm25_ids = [
        str(result.document.point_id)
        for result in bm25_results
    ]

    unique_candidate_ids = list(
        dict.fromkeys(
            semantic_ids + bm25_ids
        )
    )

    if unique_candidate_ids:
        rrf_results = fuse_semantic_and_bm25(
            semantic_ids=semantic_ids,
            bm25_ids=bm25_ids,
            k=RRF_K,
            semantic_weight=1.0,
            bm25_weight=1.0,
            top_k=len(unique_candidate_ids),
        )
    else:
        rrf_results = []

    full_rrf_results = _build_fused_results(
        rrf_results=rrf_results,
        semantic_results=semantic_results,
        bm25_results=bm25_results,
    )

    elapsed_ms = (
        time.perf_counter() - started
    ) * 1000.0

    return full_rrf_results[:TOP_K], elapsed_ms


def run_full_pipeline(
    *,
    query: str,
    pattern: str | None,
    sub_pattern: str | None,
):
    """Execute the production RRF + Cross-Encoder pipeline."""
    started = time.perf_counter()

    result = retrieve_hybrid(
        query=query,
        pattern=pattern,
        sub_pattern=sub_pattern,
        top_k=TOP_K,
        candidate_multiplier=CANDIDATE_MULTIPLIER,
        rrf_k=RRF_K,
    )

    elapsed_ms = (
        time.perf_counter() - started
    ) * 1000.0

    return result, elapsed_ms


def run_cross_encoder_only(
    *,
    query: str,
    rrf_results: list,
) -> float:
    """
    Measure the Cross-Encoder stage against the complete RRF pool.

    This is a separate measurement and therefore intentionally performs
    one additional reranking call.
    """
    candidates = [
        get_candidate_text(result)
        for result in rrf_results
    ]

    started = time.perf_counter()

    rerank(
        query=query,
        candidates=candidates,
        top_k=TOP_K,
    )

    return (
        time.perf_counter() - started
    ) * 1000.0


def chunk_id_for(result) -> object:
    if result.semantic_result is not None:
        return result.semantic_result.chunk_id

    if result.bm25_document is not None:
        return result.bm25_document.chunk_id

    return None


def print_results(
    title: str,
    results: list,
    *,
    show_ce_score: bool = False,
) -> None:
    print()
    print(title)
    print("-" * 60)

    if not results:
        print("No results.")
        return

    for rank, result in enumerate(
        results,
        start=1,
    ):
        line = (
            f"[{rank}] "
            f"point_id={result.point_id} "
            f"chunk={chunk_id_for(result)} "
            f"RRF={result.rrf_score:.8f}"
        )

        if show_ce_score:
            line += (
                f" CE={result.reranker_score:.6f}"
            )

        print(line)


def rank_map(results: list) -> dict[str, int]:
    return {
        str(result.point_id): rank
        for rank, result in enumerate(
            results,
            start=1,
        )
    }


def ranking_movement(
    rrf_results: list,
    reranked_results: list,
) -> dict[str, int]:
    """
    Positive value = moved upward.
    Negative value = moved downward.
    """
    old_ranks = rank_map(rrf_results)
    new_ranks = rank_map(reranked_results)

    movement = {}

    for point_id, new_rank in new_ranks.items():
        old_rank = old_ranks.get(point_id)

        if old_rank is not None:
            movement[point_id] = old_rank - new_rank

    return movement


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    print("=" * 60)
    print("PHASE 11 CROSS-ENCODER RERANKING BENCHMARK")
    print("=" * 60)

    print(
        f"Top-K                  : {TOP_K}"
    )
    print(
        f"Candidate multiplier   : "
        f"{CANDIDATE_MULTIPLIER}"
    )
    print(
        f"Candidate K            : "
        f"{candidate_k()}"
    )
    print(
        f"RRF K                  : {RRF_K}"
    )
    print(
        f"Queries                : "
        f"{len(TEST_CASES)}"
    )

    rrf_latencies = []
    pipeline_latencies = []
    ce_latencies = []

    queries_with_changes = 0
    total_changed_items = 0

    for case in TEST_CASES:
        print()
        print("=" * 60)
        print(
            f"QUERY: {case['name']}"
        )
        print("=" * 60)

        print(
            f"Text        : {case['query']}"
        )
        print(
            f"Pattern     : {case['pattern']}"
        )
        print(
            f"Sub-pattern : {case['sub_pattern']}"
        )

        # ----------------------------------------------------
        # RRF-only baseline
        # ----------------------------------------------------

        rrf_results, rrf_ms = run_rrf_only(
            query=case["query"],
            pattern=case["pattern"],
            sub_pattern=case["sub_pattern"],
        )

        # ----------------------------------------------------
        # Complete production pipeline
        # ----------------------------------------------------

        full_result, pipeline_ms = run_full_pipeline(
            query=case["query"],
            pattern=case["pattern"],
            sub_pattern=case["sub_pattern"],
        )

        reranked_results = full_result.fused_results

        # ----------------------------------------------------
        # Validate benchmark invariants
        # ----------------------------------------------------

        assert len(rrf_results) <= TOP_K
        assert len(reranked_results) <= TOP_K

        full_rrf_ids = {
            str(item.point_id)
            for item in full_result.rrf_results
        }

        final_ids = {
            str(item.point_id)
            for item in reranked_results
        }

        assert final_ids <= full_rrf_ids, (
            "Cross-Encoder returned a result outside "
            "the RRF candidate pool."
        )

        # ----------------------------------------------------
        # Cross-Encoder stage timing
        # ----------------------------------------------------

        ce_ms = run_cross_encoder_only(
            query=case["query"],
            rrf_results=full_result.rrf_results,
        )

        rrf_latencies.append(rrf_ms)
        pipeline_latencies.append(pipeline_ms)
        ce_latencies.append(ce_ms)

        print_results(
            "RRF-ONLY TOP-K",
            rrf_results,
        )

        print_results(
            "RRF + CROSS-ENCODER TOP-K",
            reranked_results,
            show_ce_score=True,
        )

        # ----------------------------------------------------
        # Ranking movement
        # ----------------------------------------------------

        movement = ranking_movement(
            rrf_results,
            reranked_results,
        )

        changed = {
            point_id: delta
            for point_id, delta in movement.items()
            if delta != 0
        }

        if changed:
            queries_with_changes += 1
            total_changed_items += len(changed)

        print()
        print("RANKING MOVEMENT")
        print("-" * 60)

        if not changed:
            print(
                "No Top-K rank movement for this query."
            )
        else:
            for point_id, delta in changed.items():
                if delta > 0:
                    direction = "UP"
                else:
                    direction = "DOWN"

                print(
                    f"{direction:4} "
                    f"{point_id}: "
                    f"{abs(delta)} position(s)"
                )

        print()
        print(
            f"RRF-only latency      : "
            f"{rrf_ms:.2f} ms"
        )
        print(
            f"Full pipeline latency : "
            f"{pipeline_ms:.2f} ms"
        )
        print(
            f"CE stage latency      : "
            f"{ce_ms:.2f} ms"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print("PHASE 11 BENCHMARK SUMMARY")
    print("=" * 60)

    avg_rrf = mean(rrf_latencies)
    avg_pipeline = mean(pipeline_latencies)
    avg_ce = mean(ce_latencies)

    print(
        f"Average RRF-only latency  : "
        f"{avg_rrf:.2f} ms"
    )
    print(
        f"Average full latency      : "
        f"{avg_pipeline:.2f} ms"
    )
    print(
        f"Average CE stage latency  : "
        f"{avg_ce:.2f} ms"
    )
    print(
        f"Approx. full-pipeline overhead: "
        f"{avg_pipeline - avg_rrf:.2f} ms"
    )

    print(
        f"Queries with Top-K changes: "
        f"{queries_with_changes}/"
        f"{len(TEST_CASES)}"
    )
    print(
        f"Changed Top-K items       : "
        f"{total_changed_items}"
    )

    print()
    print("=" * 60)
    print("INTERPRETATION")
    print("=" * 60)

    print(
        "✓ RRF-only provides the baseline ranking."
    )
    print(
        "✓ Cross-Encoder provides the production final ranking."
    )
    print(
        "✓ Ranking movement shows whether Cross-Encoder "
        "changes the Top-K order."
    )
    print(
        "✓ Latency shows the additional retrieval/reranking cost."
    )
    print(
        "NOTE: Relevance improvement is NOT claimed because "
        "ground-truth relevance labels are not available yet."
    )
    print(
        "Later, human-validated labels can support MRR, "
        "nDCG@K, Recall@K, and Precision@K."
    )

    print()
    print("=" * 60)
    print(
        "✓ PHASE 11 RERANKING BENCHMARK COMPLETED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
