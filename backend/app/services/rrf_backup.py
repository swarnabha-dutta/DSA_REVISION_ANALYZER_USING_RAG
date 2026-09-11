"""
Reciprocal Rank Fusion (RRF)
============================

Purpose:
    Combine ranked results from multiple retrieval systems without
    comparing their raw scores directly.

Why RRF?
    Semantic retrieval and BM25 produce scores from different
    mathematical spaces.

    Example:

        Semantic score -> 0.91
        BM25 score     -> 12.91

    These values cannot be meaningfully compared.

    RRF solves this by using rank instead of raw score.

Formula:

        RRF(d) = sum(
            weight_i / (k + rank_i(d))
        )

    where:

        d       = document
        rank_i  = rank of document in retriever i
        weight  = optional retriever weight
        k       = rank constant

This module is intentionally independent from Qdrant and BM25.
It only knows about ranked items and stable document IDs.
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

    Attributes
    ----------
    document_id:
        Stable identifier for the retrieved document/chunk.

    score:
        Final RRF score.

    rank_positions:
        Rank assigned by each retrieval system.

        Example:

            {
                "semantic": 1,
                "bm25": 3,
            }

    contributions:
        Individual RRF contributions.

        Example:

            {
                "semantic": 1 / 61,
                "bm25": 1 / 63,
            }
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
        Mapping of retriever name -> ranked document IDs.

        Example:

            {
                "semantic": ["A", "B", "C"],
                "bm25": ["C", "A", "D"],
            }

    k:
        RRF rank constant.

        The standard value is 60.

        Larger values reduce the difference between high and
        low ranks.

    weights:
        Optional per-retriever weights.

        Example:

            {
                "semantic": 1.0,
                "bm25": 1.0,
            }

        If omitted, every retriever receives weight 1.0.

    top_k:
        Optional number of fused results to return.

    Returns
    -------
    list[RRFResult]
        Results sorted by descending RRF score.

    Notes
    -----
    Rank positions are 1-based.

    Duplicate document IDs inside one ranking are ignored after
    their first occurrence.
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

        weights = {
            name: 1.0
            for name in rankings
        }

    else:

        # Make a copy so the caller's dictionary is not mutated.
        weights = dict(weights)

        for name in rankings:

            weights.setdefault(
                name,
                1.0,
            )

    # --------------------------------------------------------
    # Validate weights
    # --------------------------------------------------------

    for name, weight in weights.items():

        if weight < 0:

            raise ValueError(
                f"Weight for '{name}' "
                "cannot be negative."
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
    # Process every ranking
    # --------------------------------------------------------

    for retriever_name, ranking in rankings.items():

        seen: set[Hashable] = set()

        for rank, document_id in enumerate(
            ranking,
            start=1,
        ):

            # ------------------------------------------------
            # Ignore duplicate IDs from the same retriever.
            # ------------------------------------------------

            if document_id in seen:
                continue

            seen.add(
                document_id
            )

            # ------------------------------------------------
            # RRF contribution
            # ------------------------------------------------

            weight = weights[
                retriever_name
            ]

            contribution = (
                weight
                / (
                    k + rank
                )
            )

            # ------------------------------------------------
            # Initialize document
            # ------------------------------------------------

            if document_id not in scores:

                scores[
                    document_id
                ] = 0.0

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
            result.document_id,
        )
    )

    # --------------------------------------------------------
    # Top-K
    # --------------------------------------------------------

    if top_k is not None:

        results = results[
            :top_k
        ]

    return results


# ============================================================
# TWO-WAY RETRIEVAL HELPER
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
    Convenience wrapper for the project's two retrieval systems.

    Semantic and BM25 receive equal weight by default.

    This keeps the first version of hybrid retrieval neutral.

    We can tune these weights later using evaluation data.
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
# DISPLAY HELPER
# ============================================================

def print_rrf_results(
    results: list[RRFResult],
) -> None:
    """
    Pretty-print fused RRF results.
    """

    print()
    print(
        "=" * 60
    )

    print(
        "RRF RESULTS"
    )

    print(
        "=" * 60
    )

    if not results:

        print(
            "No fused results."
        )

        return

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"[{rank}] "
            f"document={result.document_id} "
            f"RRF={result.score:.8f}"
        )

        print(
            f"    ranks={result.rank_positions}"
        )

        print(
            f"    contributions="
            f"{result.contributions}"
        )