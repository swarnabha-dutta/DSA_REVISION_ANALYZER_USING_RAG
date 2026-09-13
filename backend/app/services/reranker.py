"""
Cross-Encoder Reranker
======================

Reranks hybrid retrieval candidates using a Cross-Encoder.

Pipeline:

    Query
      +
    Candidate Chunk
      |
      v
    Cross-Encoder
      |
      v
    Relevance Score
      |
      v
    Reranked Candidates

The reranker operates only on candidates that have already
passed metadata-aware retrieval and RRF fusion.

It does NOT perform:
    - Qdrant retrieval
    - BM25 retrieval
    - metadata filtering
    - candidate discovery

Its responsibility is fine-grained relevance ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sentence_transformers import CrossEncoder


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_RERANKER_MODEL = (
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

DEFAULT_RERANKER_BATCH_SIZE = 16


# ============================================================
# RESULT MODEL
# ============================================================


@dataclass(frozen=True)
class RerankerResult:
    """
    One Cross-Encoder reranking result.

    candidate_index:
        Original candidate position.

    score:
        Cross-Encoder relevance score.

    """

    candidate_index: int
    score: float


# ============================================================
# RERANKER
# ============================================================


class CrossEncoderReranker:
    """
    Thin service wrapper around sentence-transformers
    CrossEncoder.
    """

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_RERANKER_MODEL,
        batch_size: int = DEFAULT_RERANKER_BATCH_SIZE,
    ) -> None:

        if not isinstance(model_name, str):
            raise TypeError(
                "model_name must be a string."
            )

        model_name = model_name.strip()

        if not model_name:
            raise ValueError(
                "model_name cannot be empty."
            )

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        self.model_name = model_name
        self.batch_size = batch_size

        self.model = CrossEncoder(
            model_name
        )

    # --------------------------------------------------------
    # SCORE CANDIDATES
    # --------------------------------------------------------

    def score(
        self,
        *,
        query: str,
        candidates: Sequence[str],
    ) -> list[float]:
        """
        Score query-candidate pairs.

        Returns one Cross-Encoder score per candidate.
        """

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string."
            )

        query = query.strip()

        if not query:
            raise ValueError(
                "query cannot be empty."
            )

        if not candidates:
            return []

        pairs: list[list[str]] = []

        for candidate in candidates:

            if not isinstance(candidate, str):
                raise TypeError(
                    "Every candidate must be a string."
                )

            candidate = candidate.strip()

            if not candidate:
                raise ValueError(
                    "Candidate text cannot be empty."
                )

            pairs.append(
                [query, candidate]
            )

        raw_scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        return [
            float(score)
            for score in raw_scores
        ]

    # --------------------------------------------------------
    # RERANK
    # --------------------------------------------------------

    def rerank(
        self,
        *,
        query: str,
        candidates: Sequence[str],
        top_k: int | None = None,
    ) -> list[RerankerResult]:
        """
        Score and rank candidates by Cross-Encoder relevance.

        The returned candidate_index points back to the
        original candidate list.
        """

        if top_k is not None and top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        scores = self.score(
            query=query,
            candidates=candidates,
        )

        results = [
            RerankerResult(
                candidate_index=index,
                score=score,
            )
            for index, score in enumerate(scores)
        ]

        # Highest Cross-Encoder relevance first.
        #
        # Candidate index is used as a deterministic tie-breaker.
        results.sort(
            key=lambda result: (
                -result.score,
                result.candidate_index,
            )
        )

        if top_k is not None:
            results = results[:top_k]

        return results


# ============================================================
# DEFAULT SINGLETON
# ============================================================


_RERANKER: CrossEncoderReranker | None = None


def get_reranker() -> CrossEncoderReranker:
    """
    Lazily initialize and return the default reranker.

    Lazy loading prevents the Cross-Encoder model from being
    loaded during unrelated imports.
    """

    global _RERANKER

    if _RERANKER is None:
        _RERANKER = CrossEncoderReranker()

    return _RERANKER


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================


def rerank(
    *,
    query: str,
    candidates: Sequence[str],
    top_k: int | None = None,
) -> list[RerankerResult]:
    """
    Convenience wrapper around the default reranker.
    """

    return get_reranker().rerank(
        query=query,
        candidates=candidates,
        top_k=top_k,
    )


# ============================================================
# SELF-CHECK
# ============================================================


def self_check() -> None:
    """
    Lightweight configuration/model self-check.

    This intentionally loads the actual Cross-Encoder model,
    so the first run may download the model from Hugging Face.
    """

    print("=" * 60)
    print("CROSS-ENCODER RERANKER SELF-CHECK")
    print("=" * 60)

    print(
        f"Model       : "
        f"{DEFAULT_RERANKER_MODEL}"
    )

    print(
        f"Batch size  : "
        f"{DEFAULT_RERANKER_BATCH_SIZE}"
    )

    reranker = CrossEncoderReranker()

    query = "what is memoization?"

    candidates = [
        (
            "Memoization stores previously computed results "
            "so repeated recursive calls can reuse them."
        ),
        (
            "Binary search finds an element in a sorted "
            "array by repeatedly dividing the search space."
        ),
    ]

    results = reranker.rerank(
        query=query,
        candidates=candidates,
        top_k=2,
    )

    assert len(results) == 2

    assert (
        results[0].score
        >= results[1].score
    )

    assert (
        results[0].candidate_index == 0
    )

    print()
    print(
        "✓ Cross-Encoder model loaded."
    )

    print(
        "✓ Query-candidate scoring passed."
    )

    print(
        "✓ Reranking order passed."
    )

    print()
    print(
        "✓ Cross-Encoder reranker self-check passed."
    )


# ============================================================
# MODULE ENTRY POINT
# ============================================================


if __name__ == "__main__":
    self_check()