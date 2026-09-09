"""
Metadata-Aware DSA Retrieval Service

Purpose:
    Retrieve relevant DSA transcript chunks from Qdrant.

Pipeline:

    User Query
        ↓
    Query Understanding
        ↓
    Pattern / Sub-pattern
        ↓
    Query Embedding
        ↓
    Metadata Filter
        ↓
    Qdrant Vector Search
        ↓
    RetrievalResult objects

The service supports:

    1. Pure semantic retrieval
    2. Pattern-aware retrieval
    3. Sub-pattern-aware retrieval
    4. Safe semantic fallback
    5. Structured retrieval results

The retrieval layer is intentionally independent from the
query-understanding implementation.

It can therefore receive either:

    - pattern + sub_pattern directly
    - OR a QueryAnalysis-like object/dictionary
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
)
from sentence_transformers import SentenceTransformer


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parents[2]


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(
    BASE_DIR / ".env"
)


# ============================================================
# QDRANT CONFIGURATION
# ============================================================

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    "",
)

COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION",
    "dsa_revision_chunks",
)


# ============================================================
# EMBEDDING CONFIGURATION
# ============================================================

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


# ============================================================
# SEARCH CONFIGURATION
# ============================================================

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
# RETRIEVAL RESULT MODEL
# ============================================================

@dataclass(frozen=True)
class RetrievalResult:
    """
    Stable application-level representation of a retrieved
    transcript chunk.

    This prevents the rest of the application from depending
    directly on Qdrant's internal ScoredPoint structure.
    """

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

def create_qdrant_client() -> QdrantClient:
    """
    Create and return a Qdrant client.

    Uses API-key authentication when QDRANT_API_KEY is
    configured.
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
# EMBEDDING MODEL
# ============================================================

def load_embedding_model() -> SentenceTransformer:
    """
    Load the same embedding model used during ingestion.

    The query embedding model MUST match the model used to
    generate the vectors stored in Qdrant.
    """

    return SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )


# ============================================================
# QUERY EMBEDDING
# ============================================================

def create_query_embedding(
    model: SentenceTransformer,
    query: str,
) -> list[float]:
    """
    Convert a user query into a normalized embedding vector.
    """

    embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    return embedding.tolist()


# ============================================================
# QUERY ANALYSIS HELPERS
# ============================================================

def get_analysis_value(
    query_analysis: Any,
    key: str,
) -> Any:
    """
    Support both dictionary-based and object-based query
    analysis results.
    """

    if query_analysis is None:
        return None

    if isinstance(
        query_analysis,
        dict,
    ):
        return query_analysis.get(
            key
        )

    return getattr(
        query_analysis,
        key,
        None,
    )


# ============================================================
# METADATA FILTER
# ============================================================

def build_metadata_filter(
    pattern: str | None = None,
    sub_pattern: str | None = None,
) -> Filter | None:
    """
    Build a Qdrant metadata filter.

    Behaviour:

        pattern + sub_pattern
            → filter by both

        pattern only
            → filter by pattern

        neither
            → no filter
    """

    conditions: list[FieldCondition] = []

    # --------------------------------------------------------
    # Pattern filter
    # --------------------------------------------------------

    if pattern:
        conditions.append(
            FieldCondition(
                key="pattern",
                match=MatchValue(
                    value=pattern
                ),
            )
        )

    # --------------------------------------------------------
    # Sub-pattern filter
    # --------------------------------------------------------

    if sub_pattern:
        conditions.append(
            FieldCondition(
                key="sub_pattern",
                match=MatchValue(
                    value=sub_pattern
                ),
            )
        )

    if not conditions:
        return None

    return Filter(
        must=conditions
    )


# ============================================================
# VECTOR SEARCH
# ============================================================

def search_qdrant(
    *,
    client: QdrantClient,
    query_vector: list[float],
    top_k: int,
    query_filter: Filter | None = None,
) -> list[Any]:
    """
    Execute vector search against Qdrant.
    """

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    return response.points


# ============================================================
# PAYLOAD HELPERS
# ============================================================

def get_payload_value(
    payload: dict[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    """
    Safely retrieve a value from a Qdrant payload.

    Supports both direct payloads and a nested metadata
    payload if one is used in the future.
    """

    if key in payload:
        return payload[key]

    metadata = payload.get(
        "metadata"
    )

    if isinstance(
        metadata,
        dict,
    ):
        return metadata.get(
            key,
            default,
        )

    return default


def to_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.
    """

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def to_optional_string(
    value: Any,
) -> str | None:
    """
    Convert a payload value to an optional string.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


# ============================================================
# QDRANT RESULT → APPLICATION RESULT
# ============================================================

def convert_qdrant_result(
    result: Any,
) -> RetrievalResult:
    """
    Convert a Qdrant ScoredPoint into our stable
    RetrievalResult structure.
    """

    payload = getattr(
        result,
        "payload",
        None,
    )

    if not isinstance(
        payload,
        dict,
    ):
        payload = {}

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    pattern = to_optional_string(
        get_payload_value(
            payload,
            "pattern",
        )
    )

    sub_pattern = to_optional_string(
        get_payload_value(
            payload,
            "sub_pattern",
        )
    )

    playlist = to_optional_string(
        get_payload_value(
            payload,
            "playlist",
        )
    )

    video_id = to_optional_string(
        get_payload_value(
            payload,
            "video_id",
        )
    )

    video_title = to_optional_string(
        get_payload_value(
            payload,
            "video_title",
        )
    )

    # --------------------------------------------------------
    # Chunk metadata
    # --------------------------------------------------------

    chunk_id = get_payload_value(
        payload,
        "chunk_id",
    )

    if chunk_id is None:
        chunk_id = get_payload_value(
            payload,
            "id",
        )

    chunk_id = (
        str(chunk_id)
        if chunk_id is not None
        else None
    )

    start = to_float(
        get_payload_value(
            payload,
            "start",
            0.0,
        )
    )

    end = to_float(
        get_payload_value(
            payload,
            "end",
            0.0,
        )
    )

    duration = to_float(
        get_payload_value(
            payload,
            "duration",
            max(
                0.0,
                end - start,
            ),
        )
    )

    text = get_payload_value(
        payload,
        "text",
        "",
    )

    if text is None:
        text = ""

    text = str(text)

    score = to_float(
        getattr(
            result,
            "score",
            0.0,
        )
    )

    return RetrievalResult(
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
# RESULT DEDUPLICATION
# ============================================================

def deduplicate_results(
    results: list[Any],
) -> list[Any]:
    """
    Remove duplicate Qdrant points while preserving ranking
    order.
    """

    seen: set[str] = set()

    unique_results: list[Any] = []

    for result in results:

        result_id = str(
            getattr(
                result,
                "id",
                id(result),
            )
        )

        if result_id in seen:
            continue

        seen.add(
            result_id
        )

        unique_results.append(
            result
        )

    return unique_results


# ============================================================
# RESULT SORTING
# ============================================================

def sort_results(
    results: list[Any],
) -> list[Any]:
    """
    Sort results by descending similarity score.
    """

    return sorted(
        results,
        key=lambda result: float(
            getattr(
                result,
                "score",
                0.0,
            )
        ),
        reverse=True,
    )


# ============================================================
# MAIN RETRIEVAL
# ============================================================

def retrieve_chunks(
    *,
    query: str,
    pattern: str | None = None,
    sub_pattern: str | None = None,
    query_analysis: Any = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[RetrievalResult]:
    """
    Retrieve transcript chunks relevant to the user's query.

    Supported calling styles:

    ------------------------------------------------------------
    Style 1 — direct metadata
    ------------------------------------------------------------

        retrieve_chunks(
            query="Explain memoization",
            pattern="dynamic_programming",
            sub_pattern="memoization",
            top_k=5,
        )

    ------------------------------------------------------------
    Style 2 — QueryAnalysis object
    ------------------------------------------------------------

        retrieve_chunks(
            query="Explain memoization",
            query_analysis=analysis,
            top_k=5,
        )

    ------------------------------------------------------------

    Metadata-aware retrieval is attempted first.

    If strict filtering returns no results, semantic-only
    fallback retrieval is performed.

    Finally Qdrant results are converted into stable
    RetrievalResult objects.
    """

    # ========================================================
    # VALIDATE QUERY
    # ========================================================

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

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    # ========================================================
    # RESOLVE METADATA
    # ========================================================
    #
    # Direct arguments take precedence.
    #
    # If they are not supplied, attempt to obtain them from
    # query_analysis.
    # ========================================================

    if pattern is None:
        pattern = get_analysis_value(
            query_analysis,
            "pattern",
        )

    if sub_pattern is None:
        sub_pattern = get_analysis_value(
            query_analysis,
            "sub_pattern",
        )

    # ========================================================
    # CREATE QDRANT CLIENT
    # ========================================================

    client = create_qdrant_client()

    # ========================================================
    # VERIFY COLLECTION
    # ========================================================

    collections = client.get_collections()

    collection_names = {
        collection.name
        for collection in collections.collections
    }

    if COLLECTION_NAME not in collection_names:
        raise RuntimeError(
            f"Qdrant collection "
            f"'{COLLECTION_NAME}' "
            f"does not exist."
        )

    # ========================================================
    # LOAD EMBEDDING MODEL
    # ========================================================

    model = load_embedding_model()

    # ========================================================
    # CREATE QUERY EMBEDDING
    # ========================================================

    query_vector = create_query_embedding(
        model=model,
        query=query,
    )

    # ========================================================
    # BUILD METADATA FILTER
    # ========================================================

    metadata_filter = build_metadata_filter(
        pattern=pattern,
        sub_pattern=sub_pattern,
    )

    # ========================================================
    # METADATA-AWARE RETRIEVAL
    # ========================================================

    if metadata_filter is not None:

        filtered_limit = max(
            top_k,
            top_k * FILTERED_SEARCH_MULTIPLIER,
        )

        filtered_results = search_qdrant(
            client=client,
            query_vector=query_vector,
            top_k=filtered_limit,
            query_filter=metadata_filter,
        )

        filtered_results = deduplicate_results(
            filtered_results
        )

        filtered_results = sort_results(
            filtered_results
        )

        if filtered_results:

            return [
                convert_qdrant_result(
                    result
                )
                for result in filtered_results[
                    :top_k
                ]
            ]

    # ========================================================
    # SEMANTIC FALLBACK
    # ========================================================
    #
    # If metadata filtering produces zero results, perform
    # semantic-only retrieval.
    #
    # This prevents the system from failing simply because
    # metadata is incomplete or query understanding is
    # slightly inaccurate.
    # ========================================================

    fallback_results = search_qdrant(
        client=client,
        query_vector=query_vector,
        top_k=top_k,
        query_filter=None,
    )

    fallback_results = deduplicate_results(
        fallback_results
    )

    fallback_results = sort_results(
        fallback_results
    )

    return [
        convert_qdrant_result(
            result
        )
        for result in fallback_results[
            :top_k
        ]
    ]


# ============================================================
# DEBUG / SELF-CHECK
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(
        "RETRIEVAL SERVICE SELF-CHECK"
    )
    print("=" * 60)

    print()

    print(
        f"Qdrant URL       : {QDRANT_URL}"
    )

    print(
        f"Collection       : {COLLECTION_NAME}"
    )

    print(
        f"Embedding model  : {EMBEDDING_MODEL_NAME}"
    )

    print(
        f"Default Top-K    : {DEFAULT_TOP_K}"
    )

    print()

    print(
        "Retrieval service loaded successfully."
    )