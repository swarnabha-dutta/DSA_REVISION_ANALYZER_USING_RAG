"""
Semantic retrieval service for the DSA Revision Analyzer.

Responsibilities
----------------
1. Load the sentence-transformers embedding model.
2. Generate an embedding for a user query.
3. Connect to Qdrant.
4. Apply optional DSA metadata filters.
5. Perform semantic vector search.
6. Convert Qdrant results into stable RetrievalResult objects.

This module intentionally does NOT know about:
- BM25
- RRF
- Hybrid retrieval
- Query orchestration

Those responsibilities belong to higher-level services.
"""

from __future__ import annotations

# ============================================================
# STANDARD LIBRARY
# ============================================================

import os
from dataclasses import dataclass
from typing import Any


# ============================================================
# THIRD-PARTY
# ============================================================

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
)
from sentence_transformers import SentenceTransformer


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


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
).strip()


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


FILTERED_SEARCH_MULTIPLIER = int(
    os.getenv(
        "FILTERED_SEARCH_MULTIPLIER",
        "3",
    )
)


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class RetrievalResult:
    """
    Stable application-level representation of one
    semantically retrieved transcript chunk.

    The rest of the application should depend on this
    model instead of Qdrant's ScoredPoint directly.
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

    @property
    def start_seconds(self) -> float:
        """Backward-compatible alias for the chunk start timestamp."""
        return self.start

    @property
    def end_seconds(self) -> float:
        """Backward-compatible alias for the chunk end timestamp."""
        return self.end


# ============================================================
# EMBEDDING MODEL
# ============================================================

_embedding_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model lazily.

    The same model must be used during:
        ingestion
        +
        query-time retrieval
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
# QDRANT CLIENT
# ============================================================

def get_qdrant_client() -> QdrantClient:
    """
    Create a Qdrant client using environment configuration.

    Supports:
        - local Qdrant
        - Qdrant Cloud
    """

    if QDRANT_API_KEY:
        return QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

    return QdrantClient(
        url=QDRANT_URL,
    )


# ============================================================
# QUERY EMBEDDING
# ============================================================

def create_query_embedding(
    query: str,
) -> list[float]:
    """
    Convert a natural-language query into an embedding.
    """

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "Query cannot be empty."
        )

    model = get_embedding_model()

    embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    return embedding.tolist()


# ============================================================
# METADATA FILTER
# ============================================================

def build_metadata_filter(
    pattern: str | None = None,
    sub_pattern: str | None = None,
) -> Filter | None:
    """
    Build a Qdrant filter.

    Cases
    -----
    pattern + sub_pattern
        Filter using both fields.

    pattern only
        Filter using pattern.

    neither
        Return None.
    """

    conditions: list[FieldCondition] = []

    if pattern:
        conditions.append(
            FieldCondition(
                key="pattern",
                match=MatchValue(
                    value=pattern,
                ),
            )
        )

    if sub_pattern:
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
# SAFE PAYLOAD HELPERS
# ============================================================

def _get_payload_value(
    payload: dict[str, Any],
    *keys: str,
) -> Any:
    """
    Return the first existing payload value.
    """

    for key in keys:
        if key in payload:
            return payload[key]

    return None


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Convert a value to float safely.
    """

    if value is None:
        return default

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def _safe_string(
    value: Any,
) -> str | None:
    """
    Convert a payload value to a clean string.
    """

    if value is None:
        return None

    value = str(value).strip()

    return value or None


# ============================================================
# QDRANT RESULT CONVERSION
# ============================================================

def convert_qdrant_result(
    result: Any,
) -> RetrievalResult:
    """
    Convert a Qdrant ScoredPoint into RetrievalResult.
    """

    payload = result.payload or {}

    point_id = str(
        result.id
    )

    start = _safe_float(
        _get_payload_value(
            payload,
            "start",
            "start_seconds",
            "timestamp_start",
        )
    )

    end = _safe_float(
        _get_payload_value(
            payload,
            "end",
            "end_seconds",
            "timestamp_end",
        )
    )

    duration = _safe_float(
        _get_payload_value(
            payload,
            "duration",
        ),
        default=max(
            0.0,
            end - start,
        ),
    )

    return RetrievalResult(
        point_id=point_id,

        score=_safe_float(
            result.score
        ),

        pattern=_safe_string(
            _get_payload_value(
                payload,
                "pattern",
            )
        ),

        sub_pattern=_safe_string(
            _get_payload_value(
                payload,
                "sub_pattern",
            )
        ),

        playlist=_safe_string(
            _get_payload_value(
                payload,
                "playlist",
            )
        ),

        video_id=_safe_string(
            _get_payload_value(
                payload,
                "video_id",
            )
        ),

        video_title=_safe_string(
            _get_payload_value(
                payload,
                "video_title",
                "title",
            )
        ),

        chunk_id=_safe_string(
            _get_payload_value(
                payload,
                "chunk_id",
            )
        ),

        start=start,

        end=end,

        duration=duration,

        text=_safe_string(
            _get_payload_value(
                payload,
                "text",
                "chunk_text",
                "content",
            )
        ) or "",
    )


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
        Natural-language search query.

    top_k:
        Number of results requested.

    pattern:
        Optional DSA pattern filter.

    sub_pattern:
        Optional DSA sub-pattern filter.

    Returns
    -------
    list[RetrievalResult]
        Results ordered by semantic similarity.
    """

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "Query cannot be empty."
        )

    # --------------------------------------------------------
    # Validate top_k
    # --------------------------------------------------------

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    # --------------------------------------------------------
    # Create query embedding
    # --------------------------------------------------------

    query_vector = create_query_embedding(
        query
    )

    # --------------------------------------------------------
    # Qdrant client
    # --------------------------------------------------------

    client = get_qdrant_client()

    # --------------------------------------------------------
    # Metadata filter
    # --------------------------------------------------------

    query_filter = build_metadata_filter(
        pattern=pattern,
        sub_pattern=sub_pattern,
    )

    # --------------------------------------------------------
    # Candidate size
    # --------------------------------------------------------

    if query_filter is not None:
        search_limit = (
            top_k
            * FILTERED_SEARCH_MULTIPLIER
        )
    else:
        search_limit = top_k

    # --------------------------------------------------------
    # Semantic search
    # --------------------------------------------------------

    search_result = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=search_limit,
        with_payload=True,
    )

    points = search_result.points

    # --------------------------------------------------------
    # Convert results
    # --------------------------------------------------------

    results = [
        convert_qdrant_result(
            point
        )
        for point in points
    ]

    # --------------------------------------------------------
    # Safety trim
    # --------------------------------------------------------

    return results[:top_k]


# ============================================================
# DISPLAY HELPER
# ============================================================

def print_results(
    results: list[RetrievalResult],
) -> None:
    """
    Pretty-print semantic retrieval results.
    """

    print()
    print("=" * 60)
    print("SEMANTIC RETRIEVAL RESULTS")
    print("=" * 60)

    if not results:
        print("No results.")
        return

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"[{rank}] "
            f"score={result.score:.4f}"
        )

        print(
            f"    point_id   : "
            f"{result.point_id}"
        )

        print(
            f"    chunk_id   : "
            f"{result.chunk_id}"
        )

        print(
            f"    video_id   : "
            f"{result.video_id}"
        )

        print(
            f"    pattern    : "
            f"{result.pattern}"
        )

        print(
            f"    sub_pattern: "
            f"{result.sub_pattern}"
        )

        print(
            f"    timestamp  : "
            f"{result.start:.2f}s → "
            f"{result.end:.2f}s"
        )

        print(
            f"    text       : "
            f"{result.text[:180]}"
        )


# ============================================================
# SELF CHECK
# ============================================================

def self_check() -> None:
    """
    Verify that the retrieval service can initialize
    successfully.
    """

    print("=" * 60)
    print("RETRIEVAL SERVICE SELF-CHECK")
    print("=" * 60)

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

    # --------------------------------------------------------
    # Qdrant
    # --------------------------------------------------------

    client = get_qdrant_client()

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
    # Test embedding
    # --------------------------------------------------------

    test_embedding = model.encode(
        "memoization",
        normalize_embeddings=True,
    )

    print(
        "✓ Test embedding generated."
    )

    print(
        f"  Embedding dimension: "
        f"{len(test_embedding)}"
    )

    # --------------------------------------------------------
    # Client is intentionally retained so connection
    # construction is validated.
    # --------------------------------------------------------

    _ = client

    print()
    print(
        "✓ Retrieval service self-check passed."
    )


# ============================================================
# MODULE ENTRY POINT
# ============================================================

if __name__ == "__main__":
    self_check()