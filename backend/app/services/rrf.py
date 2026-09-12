"""
Reciprocal Rank Fusion (RRF)
============================

Combines ranked results from multiple retrieval systems.

Semantic retrieval and BM25 produce scores from different
mathematical spaces, so their raw scores should not be compared
directly.

RRF uses rank positions instead.

Formula:

    RRF(d) = sum(
        weight_i / (k + rank_i(d))
    )

This module is intentionally independent from:
    - Qdrant
    - BM25
    - embeddings
    - query analysis
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Iterable


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_RRF_K = 60.0


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class RRFResult:
    """
    One fused retrieval result.
    """

    document_id: Hashable

    score: float

    rank_positions: dict[str, int]

    contributions: dict[str, float]


# ============================================================
# CORE RRF
# ============================================================

def reciprocal_rank_fusion(
    rankings: dict[
        str,
        Iterable[Hashable],
    ],
    *,
    k: float = DEFAULT_RRF_K,
    weights: dict[str, float] | None = None,
    top_k: int | None = None,
) -> list[RRFResult]:
    """
    Fuse multiple ranked lists using Reciprocal Rank Fusion.

    Parameters
    ----------
    rankings:
        Mapping:

            retriever_name -> ranked document IDs

        Example:

            {
                "semantic": ["A", "B", "C"],
                "bm25": ["C", "A", "D"],
            }

    k:
        RRF rank constant.

        Standard value = 60.

    weights:
        Optional retriever weights.

        Example:

            {
                "semantic": 1.0,
                "bm25": 1.0,
            }

    top_k:
        Optional number of results to return.

    Returns
    -------
    list[RRFResult]
        Results ordered by descending RRF score.
    """

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if k <= 0:
        raise ValueError(
            "RRF k must be greater than 0."
        )

    if top_k is not None and top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    if not rankings:
        return []

    # --------------------------------------------------------
    # Resolve weights
    # --------------------------------------------------------

    if weights is None:
        resolved_weights = {
            name: 1.0
            for name in rankings
        }
    else:
        resolved_weights = dict(weights)

        for name in rankings:
            resolved_weights.setdefault(
                name,
                1.0,
            )

    # --------------------------------------------------------
    # Validate weights
    # --------------------------------------------------------

    for name, weight in resolved_weights.items():

        if weight < 0:
            raise ValueError(
                f"Weight for '{name}' cannot be negative."
            )

    # --------------------------------------------------------
    # Accumulators
    # --------------------------------------------------------

    scores: dict[
        Hashable,
        float,
    ] = {}

    rank_positions: dict[
        Hashable,
        dict[str, int],
    ] = {}

    contributions: dict[
        Hashable,
        dict[str, float],
    ] = {}

    # --------------------------------------------------------
    # Process rankings
    # --------------------------------------------------------

    for retriever_name, ranking in rankings.items():

        seen: set[Hashable] = set()

        for rank, document_id in enumerate(
            ranking,
            start=1,
        ):

            # ------------------------------------------------
            # Ignore duplicates inside one retriever
            # ------------------------------------------------

            if document_id in seen:
                continue

            seen.add(document_id)

            # ------------------------------------------------
            # Calculate contribution
            # ------------------------------------------------

            weight = resolved_weights[
                retriever_name
            ]

            contribution = (
                weight
                / (k + rank)
            )

            # ------------------------------------------------
            # Initialize document
            # ------------------------------------------------

            if document_id not in scores:

                scores[document_id] = 0.0

                rank_positions[
                    document_id
                ] = {}

                contributions[
                    document_id
                ] = {}

            # ------------------------------------------------
            # Accumulate
            # ------------------------------------------------

            scores[
                document_id
            ] += contribution

            rank_positions[
                document_id
            ][
                retriever_name
            ] = rank

            contributions[
                document_id
            ][
                retriever_name
            ] = contribution

    # --------------------------------------------------------
    # Convert to result objects
    # --------------------------------------------------------

    results = [
        RRFResult(
            document_id=document_id,
            score=score,
            rank_positions=rank_positions[
                document_id
            ],
            contributions=contributions[
                document_id
            ],
        )
        for document_id, score in scores.items()
    ]

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    results.sort(
        key=lambda result: (
            -result.score,
            str(result.document_id),
        )
    )

    # --------------------------------------------------------
    # Top-K
    # --------------------------------------------------------

    if top_k is not None:
        results = results[:top_k]

    return results


# ============================================================
# TWO-WAY FUSION
# ============================================================

def fuse_semantic_and_bm25(
    semantic_ids: Iterable[Hashable],
    bm25_ids: Iterable[Hashable],
    *,
    k: float = DEFAULT_RRF_K,
    semantic_weight: float = 1.0,
    bm25_weight: float = 1.0,
    top_k: int | None = None,
) -> list[RRFResult]:
    """
    Fuse semantic and BM25 rankings.

    Default:

        semantic weight = 1.0
        BM25 weight     = 1.0

    Equal weighting is intentionally used for the first version.
    """

    return reciprocal_rank_fusion(
        rankings={
            "semantic": semantic_ids,
            "bm25": bm25_ids,
        },
        k=k,
        weights={
            "semantic": semantic_weight,
            "bm25": bm25_weight,
        },
        top_k=top_k,
    )


# ============================================================
# DISPLAY
# ============================================================

def print_rrf_results(
    results: list[RRFResult],
) -> None:
    """
    Pretty-print fused results.
    """

    print()
    print("=" * 60)
    print("RRF RESULTS")
    print("=" * 60)

    if not results:
        print(
            "No fused results."
        )
        return

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print()

        print(
            f"[{rank}] "
            f"document={result.document_id} "
            f"RRF={result.score:.8f}"
        )

        print(
            f"    ranks="
            f"{result.rank_positions}"
        )

        print(
            f"    contributions="
            f"{result.contributions}"
        )


# ============================================================
# SELF-CHECK
# ============================================================

def self_check() -> None:
    """
    Run a small deterministic RRF test.
    """

    print("=" * 60)
    print("RRF SERVICE SELF-CHECK")
    print("=" * 60)

    semantic = [
        "A",
        "B",
        "C",
    ]

    bm25 = [
        "C",
        "A",
        "D",
    ]

    results = fuse_semantic_and_bm25(
        semantic_ids=semantic,
        bm25_ids=bm25,
        top_k=4,
    )

    assert len(results) == 4

    result_by_id = {
        result.document_id: result
        for result in results
    }

    assert "A" in result_by_id
    assert "B" in result_by_id
    assert "C" in result_by_id
    assert "D" in result_by_id

    # A:
    #
    # semantic rank 1
    # BM25 rank 2
    #
    # RRF = 1/61 + 1/62

    expected_a = (
        1.0 / 61.0
        + 1.0 / 62.0
    )

    assert abs(
        result_by_id["A"].score
        - expected_a
    ) < 1e-12

    # C:
    #
    # semantic rank 3
    # BM25 rank 1

    expected_c = (
        1.0 / 63.0
        + 1.0 / 61.0
    )

    assert abs(
        result_by_id["C"].score
        - expected_c
    ) < 1e-12

    print(
        "✓ Basic RRF fusion passed."
    )

    print(
        "✓ Rank-based scoring passed."
    )

    print(
        "✓ Multi-retriever contribution passed."
    )

    print(
        "✓ RRF service self-check passed."
    )


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    self_check()