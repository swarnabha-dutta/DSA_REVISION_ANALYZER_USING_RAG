"""
Semantic search over DSA transcript chunks stored in Qdrant.

Pipeline:

    User Query
        ↓
    Query Embedding
        ↓
    Qdrant Vector Search
        ↓
    Top-K Relevant Chunks
        ↓
    Timestamp + Transcript Output

Usage:

    python scripts/search_chunks.py "your query"

Example:

    python scripts/search_chunks.py "dynamic programming recursion"
"""

from __future__ import annotations

# ============================================================
# STANDARD LIBRARY IMPORTS
# ============================================================

import os
import sys
from pathlib import Path
from typing import Any


# ============================================================
# THIRD-PARTY IMPORTS
# ============================================================

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# Load variables from backend/.env.
#
# This must happen before os.getenv() is used.

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env"
)


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

COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION",
    "dsa_revision_chunks",
)

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

# Number of chunks to retrieve from Qdrant.
DEFAULT_TOP_K = int(
    os.getenv(
        "SEARCH_TOP_K",
        "5",
    )
)


# ============================================================
# DISPLAY HELPERS
# ============================================================


def print_section(
    title: str,
) -> None:
    """
    Print a formatted section heading.

    This keeps terminal output readable during development.
    """

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def format_timestamp(
    seconds: Any,
) -> str:
    """
    Convert a timestamp in seconds into HH:MM:SS format.

    Example:

        3725.5
        ↓
        01:02:05

    If the value cannot be converted to a number, the original
    value is returned as a string.
    """

    try:

        total_seconds = int(
            float(seconds)
        )

    except (
        TypeError,
        ValueError,
    ):

        return str(seconds)

    hours = total_seconds // 3600

    minutes = (
        total_seconds % 3600
    ) // 60

    remaining_seconds = (
        total_seconds % 60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{remaining_seconds:02d}"
    )


# ============================================================
# QDRANT CLIENT
# ============================================================


def create_qdrant_client() -> QdrantClient:
    """
    Create a connection to Qdrant.

    If QDRANT_API_KEY is present, authenticated access is used.
    Otherwise, the client connects without an API key.
    """

    print(
        f"Qdrant URL: {QDRANT_URL}"
    )

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
    Load the same embedding model that was used during ingestion.

    IMPORTANT:

    The query embedding model must be identical to the model
    used to create the vectors stored in Qdrant.
    """

    print(
        f"Embedding model: "
        f"{EMBEDDING_MODEL_NAME}"
    )

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
    Convert the user's query into an embedding vector.

    normalize_embeddings=True is important because the stored
    vectors were also normalized during ingestion.
    """

    embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    return embedding.tolist()


# ============================================================
# QDRANT SEARCH
# ============================================================


def search_qdrant(
    client: QdrantClient,
    query_vector: list[float],
    top_k: int,
) -> list[Any]:
    """
    Search Qdrant for the most semantically similar chunks.

    Cosine similarity is used because the collection was created
    with cosine distance.
    """

    # --------------------------------------------------------
    # Use Qdrant's query_points API for vector search.
    # --------------------------------------------------------

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    return response.points


# ============================================================
# RESULT DISPLAY
# ============================================================


def display_results(
    results: list[Any],
) -> None:
    """
    Display retrieved chunks in a human-readable format.

    For each result we show:

        - Similarity score
        - Video ID
        - Chunk ID
        - Timestamp
        - Segment range
        - English transcript
        - Original transcript
    """

    if not results:

        print()
        print(
            "No matching chunks were found."
        )

        return

    print_section(
        f"Top {len(results)} Results"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        payload = (
            result.payload
            or {}
        )

        print()
        print(
            f"Result #{index}"
        )

        print(
            "-" * 60
        )

        # ----------------------------------------------------
        # Similarity score
        # ----------------------------------------------------

        print(
            f"Score       : "
            f"{result.score:.4f}"
        )

        # ----------------------------------------------------
        # Video information
        # ----------------------------------------------------

        print(
            f"Video ID    : "
            f"{payload.get('video_id', 'N/A')}"
        )

        print(
            f"Chunk ID    : "
            f"{payload.get('chunk_id', 'N/A')}"
        )

        # ----------------------------------------------------
        # Segment information
        # ----------------------------------------------------

        segment_start = payload.get(
            "segment_start",
            "N/A",
        )

        segment_end = payload.get(
            "segment_end",
            "N/A",
        )

        print(
            f"Segments    : "
            f"{segment_start} → {segment_end}"
        )

        # ----------------------------------------------------
        # Timestamp information
        # ----------------------------------------------------

        start = payload.get(
            "start",
            "N/A",
        )

        end = payload.get(
            "end",
            "N/A",
        )

        print(
            f"Timestamp   : "
            f"{format_timestamp(start)}"
            f" → "
            f"{format_timestamp(end)}"
        )

        # ----------------------------------------------------
        # Optional future metadata
        # ----------------------------------------------------

        if payload.get(
            "pattern"
        ):

            print(
                f"Pattern     : "
                f"{payload['pattern']}"
            )

        if payload.get(
            "sub_pattern"
        ):

            print(
                f"Sub-pattern : "
                f"{payload['sub_pattern']}"
            )

        if payload.get(
            "topic"
        ):

            print(
                f"Topic       : "
                f"{payload['topic']}"
            )

        # ----------------------------------------------------
        # English transcript
        # ----------------------------------------------------

        text_en = str(
            payload.get(
                "text_en",
                "",
            )
        ).strip()

        print()

        print(
            "English Text:"
        )

        print(
            text_en
            if text_en
            else "N/A"
        )

        # ----------------------------------------------------
        # Original transcript
        # ----------------------------------------------------

        original_text = str(
            payload.get(
                "text",
                "",
            )
        ).strip()

        print()

        print(
            "Original Text:"
        )

        print(
            original_text
            if original_text
            else "N/A"
        )

        print(
            "-" * 60
        )


# ============================================================
# MAIN SEARCH PIPELINE
# ============================================================


def search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
) -> None:
    """
    Execute the complete semantic search pipeline.

    Steps:

        1. Load embedding model.
        2. Create query embedding.
        3. Connect to Qdrant.
        4. Search the vector collection.
        5. Display the retrieved chunks.
    """

    # --------------------------------------------------------
    # Validate query.
    # --------------------------------------------------------

    query = query.strip()

    if not query:

        raise ValueError(
            "Search query cannot be empty."
        )

    if top_k <= 0:

        raise ValueError(
            "top_k must be greater than 0."
        )

    # --------------------------------------------------------
    # Display configuration.
    # --------------------------------------------------------

    print_section(
        "Semantic Search Configuration"
    )

    print(
        f"Query        : {query}"
    )

    print(
        f"Top-K        : {top_k}"
    )

    print(
        f"Collection   : "
        f"{COLLECTION_NAME}"
    )

    # --------------------------------------------------------
    # Load embedding model.
    # --------------------------------------------------------

    print_section(
        "Loading Embedding Model"
    )

    model = load_embedding_model()

    # --------------------------------------------------------
    # Create query embedding.
    # --------------------------------------------------------

    print_section(
        "Creating Query Embedding"
    )

    query_vector = create_query_embedding(
        model=model,
        query=query,
    )

    print(
        f"Vector dimensions: "
        f"{len(query_vector)}"
    )

    # --------------------------------------------------------
    # Connect to Qdrant.
    # --------------------------------------------------------

    print_section(
        "Connecting to Qdrant"
    )

    client = create_qdrant_client()

    # --------------------------------------------------------
    # Verify that the collection exists.
    # --------------------------------------------------------

    print_section(
        "Checking Qdrant Collection"
    )

    collections = (
        client.get_collections()
    )

    collection_names = {
        collection.name
        for collection in collections.collections
    }

    if COLLECTION_NAME not in collection_names:

        raise RuntimeError(
            f"Qdrant collection "
            f"'{COLLECTION_NAME}' "
            "does not exist."
        )

    print(
        f"Collection found: "
        f"{COLLECTION_NAME}"
    )

    # --------------------------------------------------------
    # Search Qdrant.
    # --------------------------------------------------------

    print_section(
        "Searching Qdrant"
    )

    results = search_qdrant(
        client=client,
        query_vector=query_vector,
        top_k=top_k,
    )

    print(
        f"Retrieved results: "
        f"{len(results)}"
    )

    # --------------------------------------------------------
    # Display results.
    # --------------------------------------------------------

    display_results(
        results
    )


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================


def main() -> None:
    """
    Command-line entry point.

    Usage:

        python scripts/search_chunks.py "your query"

    Optional third argument:

        python scripts/search_chunks.py "your query" 10

    The second argument controls the number of results.
    """

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            '  python scripts/search_chunks.py '
            '"your query"'
        )

        print()

        print(
            "Example:"
        )

        print(
            '  python scripts/search_chunks.py '
            '"dynamic programming recursion"'
        )

        print()

        print(
            "Optional Top-K:"
        )

        print(
            '  python scripts/search_chunks.py '
            '"dynamic programming recursion" 10'
        )

        raise SystemExit(1)

    query = sys.argv[1]

    # --------------------------------------------------------
    # Allow an optional Top-K value from the command line.
    # --------------------------------------------------------

    if len(sys.argv) >= 3:

        try:

            top_k = int(
                sys.argv[2]
            )

        except ValueError:

            print(
                "Error: Top-K must be an integer."
            )

            raise SystemExit(1)

    else:

        top_k = DEFAULT_TOP_K

    try:

        search(
            query=query,
            top_k=top_k,
        )

    except KeyboardInterrupt:

        print(
            "\nSearch cancelled by user."
        )

        raise SystemExit(130)

    except Exception as error:

        print()
        print(
            "=" * 60
        )

        print(
            "SEARCH FAILED"
        )

        print(
            "=" * 60
        )

        print(
            f"Error: {error}"
        )

        raise SystemExit(1)


# ============================================================
# PYTHON ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()