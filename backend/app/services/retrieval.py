"""
Semantic Retrieval Service
==========================

Purpose:
    Retrieve transcript chunks from Qdrant using semantic similarity.

Responsibilities:
    1. Generate query embeddings.
    2. Search the Qdrant collection.
    3. Apply metadata filters.
    4. Convert Qdrant points into stable RetrievalResult objects.
    5. Preserve the original Qdrant point_id for downstream
       hybrid retrieval and Reciprocal Rank Fusion (RRF).

This module does NOT:
    - perform BM25 retrieval
    - perform RRF fusion
    - perform reranking

Those responsibilities belong to separate services.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
)
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    "",
)

QDRANT_COLLECTION = os.getenv(
    "QDRANT_COLLECTION",
    "dsa_revision_chunks",
)

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

DEFAULT_TOP_K = int(
    os.getenv(
        "SEARCH_TOP_K",
        "5",
    )
)

# ------------------------------------------------------------
# Qdrant network configuration
# ------------------------------------------------------------
#
# Qdrant Cloud requests can occasionally take longer than the
# default HTTP timeout because of:
#
#   - temporary network latency
#   - cloud cluster wake-up
#   - transient service load
#   - slower response transmission
#
# We therefore use an extended timeout and retry failed
# requests with exponential backoff.
# ------------------------------------------------------------

QDRANT_TIMEOUT = int(
    os.getenv(
        "QDRANT_TIMEOUT",
        "120",
    )
)

QDRANT_RETRIES = int(
    os.getenv(
        "QDRANT_RETRIES",
        "3",
    )
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

_embedding_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Load and cache the SentenceTransformer embedding model.

    The model is loaded only once per Python process.

    Returns
    -------
    SentenceTransformer
        Cached embedding model.
    """

    global _embedding_model

    if _embedding_model is None:

        print(
            f"Loading embedding model: "
            f"{EMBEDDING_MODEL_NAME}"
        )

        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

    return _embedding_model


# ============================================================
# RETRIEVAL RESULT
# ============================================================

@dataclass(frozen=True)
class RetrievalResult:
    """
    Stable application-level representation of a retrieved
    transcript chunk.

    point_id:
        Original Qdrant point ID.

        This is the stable identity used by hybrid retrieval
        and Reciprocal Rank Fusion (RRF) to determine whether
        semantic and BM25 results refer to the same chunk.

    score:
        Semantic similarity score returned by Qdrant.
    """

    point_id: str

    score: float

    pattern: str | None

    sub_pattern: str | None

    playlist: str | None

    video_id: str | None

    video_title: str | None

    chunk_id: str | None

    start: float

    end: float

    duration: float

    text: str


# ============================================================
# QDRANT CLIENT
# ============================================================

def get_qdrant_client() -> QdrantClient:
    """
    Create a Qdrant client.

    The client uses:
        - QDRANT_URL
        - QDRANT_API_KEY when configured
        - extended HTTP timeout

    The extended timeout is important for Qdrant Cloud,
    where a request can occasionally take longer than the
    default client timeout.

    Returns
    -------
    QdrantClient
        Configured Qdrant client.
    """

    client_kwargs: dict[str, Any] = {
        "url": QDRANT_URL,
        "timeout": QDRANT_TIMEOUT,
    }

    if QDRANT_API_KEY:
        client_kwargs["api_key"] = QDRANT_API_KEY

    return QdrantClient(
        **client_kwargs,
    )


# ============================================================
# METADATA FILTER
# ============================================================

def build_metadata_filter(
    *,
    pattern: str | None = None,
    sub_pattern: str | None = None,
) -> Filter | None:
    """
    Build a Qdrant metadata filter.

    Parameters
    ----------
    pattern:
        Optional DSA pattern filter.

    sub_pattern:
        Optional DSA sub-pattern filter.

    Returns
    -------
    Filter | None
        Qdrant filter if one or more conditions exist.
    """

    conditions: list[FieldCondition] = []

    if pattern is not None:

        conditions.append(
            FieldCondition(
                key="pattern",
                match=MatchValue(
                    value=pattern,
                ),
            )
        )

    if sub_pattern is not None:

        conditions.append(
            FieldCondition(
                key="sub_pattern",
                match=MatchValue(
                    value=sub_pattern,
                ),
            )
        )

    if not conditions:
        return None

    return Filter(
        must=conditions,
    )


# ============================================================
# PAYLOAD HELPERS
# ============================================================

def _get_payload_value(
    payload: dict[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    """
    Safely retrieve a value from a Qdrant payload.
    """

    return payload.get(
        key,
        default,
    )


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.
    """

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


def _safe_string(
    value: Any,
) -> str | None:
    """
    Safely convert a value to a string.
    """

    if value is None:
        return None

    value = str(
        value
    ).strip()

    if not value:
        return None

    return value


# ============================================================
# QDRANT RESULT CONVERSION
# ============================================================

def convert_qdrant_result(
    result: Any,
) -> RetrievalResult:
    """
    Convert a Qdrant ScoredPoint into RetrievalResult.

    Important:
        result.id is preserved as point_id.

        The BM25 index also stores this same Qdrant point ID.
        Therefore semantic and lexical retrieval can later be
        fused correctly using RRF.
    """

    payload = (
        result.payload
        or {}
    )

    if not isinstance(
        payload,
        dict,
    ):

        payload = {}

    # --------------------------------------------------------
    # Stable Qdrant point identity
    # --------------------------------------------------------

    point_id = str(
        getattr(
            result,
            "id",
            "",
        )
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    pattern = _safe_string(
        _get_payload_value(
            payload,
            "pattern",
        )
    )

    sub_pattern = _safe_string(
        _get_payload_value(
            payload,
            "sub_pattern",
        )
    )

    playlist = _safe_string(
        _get_payload_value(
            payload,
            "playlist",
        )
    )

    video_id = _safe_string(
        _get_payload_value(
            payload,
            "video_id",
        )
    )

    video_title = _safe_string(
        _get_payload_value(
            payload,
            "video_title",
            _get_payload_value(
                payload,
                "title",
            ),
        )
    )

    chunk_id = _safe_string(
        _get_payload_value(
            payload,
            "chunk_id",
        )
    )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    start = _safe_float(
        _get_payload_value(
            payload,
            "start",
            0.0,
        )
    )

    end = _safe_float(
        _get_payload_value(
            payload,
            "end",
            0.0,
        )
    )

    duration = _safe_float(
        _get_payload_value(
            payload,
            "duration",
            end - start,
        )
    )

    # --------------------------------------------------------
    # Transcript text
    # --------------------------------------------------------

    text = str(
        _get_payload_value(
            payload,
            "text",
            "",
        )
    )

    # --------------------------------------------------------
    # Semantic score
    # --------------------------------------------------------

    score = _safe_float(
        getattr(
            result,
            "score",
            0.0,
        )
    )

    return RetrievalResult(
        point_id=point_id,
        score=score,
        pattern=pattern,
        sub_pattern=sub_pattern,
        playlist=playlist,
        video_id=video_id,
        video_title=video_title,
        chunk_id=chunk_id,
        start=start,
        end=end,
        duration=duration,
        text=text,
    )


# ============================================================
# QDRANT SEARCH WITH RETRY
# ============================================================

def _query_qdrant_with_retry(
    *,
    client: QdrantClient,
    query_vector: list[float],
    query_filter: Filter | None,
    top_k: int,
) -> Any:
    """
    Execute a Qdrant semantic search with retry handling.

    Retry behavior:
        Attempt 1 -> immediate request
        Attempt 2 -> wait 1 second
        Attempt 3 -> wait 2 seconds

    The retry logic is intentionally limited so that a genuine
    Qdrant failure does not result in an infinite loop.

    Parameters
    ----------
    client:
        Configured Qdrant client.

    query_vector:
        Normalized query embedding.

    query_filter:
        Optional metadata filter.

    top_k:
        Number of candidates to retrieve.

    Returns
    -------
    Any
        Qdrant QueryResponse.
    """

    last_error: Exception | None = None

    for attempt in range(
        1,
        QDRANT_RETRIES + 1,
    ):

        try:

            print(
                f"Qdrant search attempt "
                f"{attempt}/{QDRANT_RETRIES}..."
            )

            result = client.query_points(
                collection_name=QDRANT_COLLECTION,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )

            print(
                "Qdrant search successful."
            )

            return result

        except ResponseHandlingException as exc:

            last_error = exc

            if attempt >= QDRANT_RETRIES:

                raise RuntimeError(
                    "Qdrant semantic search failed "
                    f"after {QDRANT_RETRIES} attempts. "
                    f"Qdrant URL: {QDRANT_URL}. "
                    f"Collection: {QDRANT_COLLECTION}."
                ) from exc

            wait_seconds = 2 ** (
                attempt - 1
            )

            print(
                "Qdrant request failed or timed out. "
                f"Retrying in {wait_seconds}s..."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        "Qdrant semantic search failed."
    ) from last_error


# ============================================================
# SEMANTIC RETRIEVAL
# ============================================================

def retrieve(
    query: str,
    *,
    top_k: int = DEFAULT_TOP_K,
    pattern: str | None = None,
    sub_pattern: str | None = None,
) -> list[RetrievalResult]:
    """
    Perform semantic retrieval from Qdrant.

    Parameters
    ----------
    query:
        Natural-language query.

    top_k:
        Number of semantic candidates to retrieve.

    pattern:
        Optional DSA pattern filter.

    sub_pattern:
        Optional DSA sub-pattern filter.

    Returns
    -------
    list[RetrievalResult]
        Semantic retrieval results ordered by Qdrant score.
    """

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not query or not query.strip():

        return []

    if top_k <= 0:

        return []

    # --------------------------------------------------------
    # Load embedding model
    # --------------------------------------------------------

    model = get_embedding_model()

    # --------------------------------------------------------
    # Generate query embedding
    # --------------------------------------------------------

    query_embedding = model.encode(
        query.strip(),
        normalize_embeddings=True,
    )

    # --------------------------------------------------------
    # Qdrant client
    # --------------------------------------------------------

    client = get_qdrant_client()

    # --------------------------------------------------------
    # Metadata filters
    # --------------------------------------------------------

    query_filter = build_metadata_filter(
        pattern=pattern,
        sub_pattern=sub_pattern,
    )

    # --------------------------------------------------------
    # Semantic search
    # --------------------------------------------------------

    search_result = _query_qdrant_with_retry(
        client=client,
        query_vector=query_embedding.tolist(),
        query_filter=query_filter,
        top_k=top_k,
    )

    # --------------------------------------------------------
    # Convert Qdrant results
    # --------------------------------------------------------

    results: list[RetrievalResult] = []

    for point in search_result.points:

        results.append(
            convert_qdrant_result(
                point
            )
        )

    return results


# ============================================================
# DISPLAY RESULTS
# ============================================================

def print_results(
    results: list[RetrievalResult],
) -> None:
    """
    Pretty-print semantic retrieval results.
    """

    print()

    print(
        "=" * 60
    )

    print(
        "SEMANTIC RETRIEVAL RESULTS"
    )

    print(
        "=" * 60
    )

    if not results:

        print(
            "No results found."
        )

        return

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print()

        print(
            f"[{rank}] "
            f"Semantic Score: "
            f"{result.score:.4f}"
        )

        print(
            f"Point ID   : "
            f"{result.point_id}"
        )

        print(
            f"Chunk ID   : "
            f"{result.chunk_id}"
        )

        print(
            f"Video ID   : "
            f"{result.video_id}"
        )

        print(
            f"Title      : "
            f"{result.video_title}"
        )

        print(
            f"Pattern    : "
            f"{result.pattern}"
        )

        print(
            f"Sub-pattern: "
            f"{result.sub_pattern}"
        )

        print(
            f"Playlist   : "
            f"{result.playlist}"
        )

        print(
            f"Timestamp  : "
            f"{result.start:.2f}s"
            f" → "
            f"{result.end:.2f}s"
        )

        print(
            f"Text       : "
            f"{result.text[:300]}"
        )


# ============================================================
# SELF CHECK
# ============================================================

def self_check() -> None:
    """
    Lightweight module self-check.

    This verifies:
        1. Qdrant client construction.
        2. Embedding model import.
        3. Embedding model loading.
        4. Query embedding generation.
    """

    print(
        "=" * 60
    )

    print(
        "RETRIEVAL SERVICE SELF-CHECK"
    )

    print(
        "=" * 60
    )

    print(
        f"Qdrant URL       : "
        f"{QDRANT_URL}"
    )

    print(
        f"Collection       : "
        f"{QDRANT_COLLECTION}"
    )

    print(
        f"Embedding model  : "
        f"{EMBEDDING_MODEL_NAME}"
    )

    print(
        f"Default Top-K    : "
        f"{DEFAULT_TOP_K}"
    )

    print(
        f"Qdrant timeout   : "
        f"{QDRANT_TIMEOUT}s"
    )

    print(
        f"Qdrant retries   : "
        f"{QDRANT_RETRIES}"
    )

    print()

    # --------------------------------------------------------
    # Qdrant client
    # --------------------------------------------------------

    get_qdrant_client()

    print(
        "✓ Qdrant client created."
    )

    # --------------------------------------------------------
    # Embedding model
    # --------------------------------------------------------

    model = get_embedding_model()

    print(
        "✓ Embedding model loaded."
    )

    # --------------------------------------------------------
    # Test embedding generation
    # --------------------------------------------------------

    test_embedding = model.encode(
        "dynamic programming",
        normalize_embeddings=True,
    )

    print(
        "✓ Test embedding generated."
    )

    print(
        f"  Embedding dimension: "
        f"{len(test_embedding)}"
    )

    print()

    print(
        "✓ Retrieval service self-check passed."
    )


# ============================================================
# MODULE ENTRY POINT
# ============================================================

if __name__ == "__main__":

    self_check()