"""
Generate embeddings for transcript chunks and store them in Qdrant.

Pipeline:

    Chunked Transcript
            ↓
    English Text Extraction
            ↓
    Local Embedding Model
            ↓
    Vector Generation
            ↓
    Qdrant Vector Database

This script is intentionally kept separate from the retrieval
logic so that ingestion and querying remain independent concerns.

Usage:

    python scripts/ingest_embeddings.py <video_id>

Example:

    python scripts/ingest_embeddings.py dyG4JBKh6tA
"""

from __future__ import annotations

# ============================================================
# STANDARD LIBRARY IMPORTS
# ============================================================

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Any



# ============================================================
# THIRD-PARTY IMPORTS
# ============================================================

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from sentence_transformers import SentenceTransformer

load_dotenv()

# ============================================================
# PROJECT PATH CONFIGURATION
# ============================================================

# Resolve the backend directory from this script location.
#
# File:
#
#     backend/scripts/ingest_embeddings.py
#
# Therefore:
#
#     parent       -> backend/scripts
#     parent.parent -> backend
#
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

CHUNKS_DIR = DATA_DIR / "chunks"


# ============================================================
# QDRANT CONFIGURATION
# ============================================================

# Qdrant can run locally or remotely.
#
# For local development, the default configuration below uses
# a local Qdrant server running on port 6333.
#
# These values can later be moved into a .env file or settings
# module when the project grows.

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
# EMBEDDING MODEL CONFIGURATION
# ============================================================

# We use a local Sentence Transformers model.
#
# This avoids sending transcript content to an external
# embedding API and keeps the ingestion pipeline inexpensive
# and reproducible.
#
# The model produces 384-dimensional embeddings.

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


# ============================================================
# BATCH CONFIGURATION
# ============================================================

# Embeddings are generated in batches instead of processing
# every chunk individually.
#
# This is more efficient for larger playlists.

EMBEDDING_BATCH_SIZE = int(
    os.getenv(
        "EMBEDDING_BATCH_SIZE",
        "32",
    )
)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================


def print_section(title: str) -> None:
    """
    Print a visually separated section heading.

    This makes command-line ingestion logs easier to read.
    """

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def load_chunks(
    video_id: str,
) -> dict[str, Any]:
    """
    Load the chunked transcript JSON for a video.

    Parameters
    ----------
    video_id:
        YouTube video ID.

    Returns
    -------
    dict
        Parsed chunk data.

    Raises
    ------
    FileNotFoundError
        If the chunk file does not exist.
    """

    chunk_file = (
        CHUNKS_DIR
        / f"{video_id}.json"
    )

    if not chunk_file.exists():
        raise FileNotFoundError(
            f"Chunk file not found: {chunk_file}"
        )

    with chunk_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Chunk file must contain a JSON object."
        )

    return data


def extract_chunk_text(
    chunk: dict[str, Any],
) -> str:
    """
    Extract the preferred text representation from a chunk.

    English text is preferred because the embedding pipeline
    uses the translated transcript.

    If English text is unavailable, the original transcript
    text is used as a fallback.
    """

    text_en = str(
        chunk.get(
            "text_en",
            "",
        )
    ).strip()

    if text_en:
        return text_en

    text = str(
        chunk.get(
            "text",
            "",
        )
    ).strip()

    return text


def validate_chunks(
    chunks: list[dict[str, Any]],
) -> None:
    """
    Validate the minimum information required for embedding.

    The function intentionally performs lightweight validation.
    More advanced metadata validation can be added later when
    playlist and DSA pattern classification are implemented.
    """

    if not chunks:
        raise ValueError(
            "No chunks were found in the input file."
        )

    for index, chunk in enumerate(chunks):

        if not isinstance(chunk, dict):
            raise ValueError(
                f"Chunk at index {index} is not a JSON object."
            )

        if "chunk_id" not in chunk:
            raise ValueError(
                f"Chunk at index {index} is missing 'chunk_id'."
            )

        text = extract_chunk_text(
            chunk
        )

        if not text:
            raise ValueError(
                f"Chunk {chunk.get('chunk_id')} "
                "does not contain usable text."
            )


# ============================================================
# EMBEDDING MODEL
# ============================================================


def load_embedding_model() -> SentenceTransformer:
    """
    Load the local Sentence Transformers embedding model.

    The model is downloaded automatically on first use and then
    reused from the local Hugging Face cache.
    """

    print(
        f"Loading embedding model: "
        f"{EMBEDDING_MODEL_NAME}"
    )

    model = SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

    return model


# ============================================================
# QDRANT CLIENT
# ============================================================


def create_qdrant_client() -> QdrantClient:
    """
    Create a Qdrant client.

    If QDRANT_API_KEY is configured, it is passed to Qdrant.
    Otherwise, the client connects without authentication.
    """

    print(
        f"Connecting to Qdrant: {QDRANT_URL}"
    )

    if QDRANT_API_KEY:

        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

    else:

        client = QdrantClient(
            url=QDRANT_URL,
        )

    return client


# ============================================================
# COLLECTION MANAGEMENT
# ============================================================


def ensure_collection(
    client: QdrantClient,
    vector_size: int,
) -> None:
    """
    Create the Qdrant collection if it does not already exist.

    The vector dimension is obtained dynamically from the
    embedding model instead of being hard-coded.

    This makes it safer to change embedding models later.
    """

    existing_collections = (
        client.get_collections()
    )

    collection_names = {
        collection.name
        for collection in existing_collections.collections
    }

    if COLLECTION_NAME in collection_names:

        print(
            f"Qdrant collection already exists: "
            f"{COLLECTION_NAME}"
        )

        return

    print(
        f"Creating Qdrant collection: "
        f"{COLLECTION_NAME}"
    )

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )

    print(
        "Qdrant collection created successfully."
    )


# ============================================================
# PAYLOAD CREATION
# ============================================================


def build_payload(
    video_id: str,
    chunk: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the metadata payload stored alongside the vector.

    Keeping metadata inside Qdrant allows future retrieval
    filters such as:

        video_id = ...
        pattern = "two_pointer"
        sub_pattern = "opposite_direction"
        playlist = ...

    Some fields may not exist yet. They are therefore included
    only when available.
    """

    payload: dict[str, Any] = {
        "video_id": video_id,

        "chunk_id": chunk.get(
            "chunk_id"
        ),

        "segment_start": chunk.get(
            "segment_start"
        ),

        "segment_end": chunk.get(
            "segment_end"
        ),

        "start": chunk.get(
            "start"
        ),

        "end": chunk.get(
            "end"
        ),

        "duration": chunk.get(
            "duration"
        ),

        "segment_count": chunk.get(
            "segment_count"
        ),

        "text": chunk.get(
            "text",
            "",
        ),

        "text_en": chunk.get(
            "text_en",
            "",
        ),
    }

    # --------------------------------------------------------
    # Preserve future metadata if it already exists.
    #
    # These fields will become important when the system starts
    # classifying DSA patterns and playlists.
    # --------------------------------------------------------

    optional_metadata_fields = [
        "video_title",
        "playlist",
        "playlist_id",
        "pattern",
        "sub_pattern",
        "topic",
    ]

    for field in optional_metadata_fields:

        if field in chunk:

            payload[field] = chunk[field]

    return payload


# ============================================================
# VECTOR INGESTION
# ============================================================


def generate_embeddings(
    model: SentenceTransformer,
    texts: list[str],
) -> list[list[float]]:
    """
    Generate embeddings for transcript chunks.

    Embeddings are generated in batches to improve performance.

    normalize_embeddings=True ensures that the vectors are
    normalized, which works well with cosine similarity.
    """

    embeddings = model.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    return embeddings.tolist()


def build_points(
    video_id: str,
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> list[PointStruct]:
    """
    Convert chunks and embeddings into Qdrant points.

    Each point contains:

        ID
        Vector
        Metadata payload

    A deterministic point ID is generated from the video ID
    and chunk ID so that re-running ingestion updates the same
    records instead of creating uncontrolled duplicates.
    """

    points: list[PointStruct] = []

    for chunk, embedding in zip(
        chunks,
        embeddings,
    ):

        chunk_id = chunk.get(
            "chunk_id"
        )

        if chunk_id is None:
            raise ValueError(
                "Chunk is missing chunk_id."
            )

        # ----------------------------------------------------
        # Use a deterministic string-based ID.
        #
        # This makes ingestion idempotent for a given video.
        # ----------------------------------------------------

        point_id = (
            f"{video_id}_{chunk_id}"
        )

        # Qdrant point IDs support integers or UUIDs.
        #
        # Therefore we use a deterministic UUID generated from
        # the video ID and chunk ID.
        import uuid

        deterministic_uuid = (
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                point_id,
            )
        )

        points.append(
            PointStruct(
                id=str(
                    deterministic_uuid
                ),
                vector=embedding,
                payload=build_payload(
                    video_id=video_id,
                    chunk=chunk,
                ),
            )
        )

    return points


def upload_points(
    client: QdrantClient,
    points: list[PointStruct],
) -> None:
    """
    Upload vector points to Qdrant.

    Qdrant's upsert operation makes the ingestion process
    idempotent: running the same ingestion command again updates
    existing points instead of creating duplicates.
    """

    if not points:
        return

    print(
        f"Uploading {len(points)} vectors to Qdrant..."
    )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True,
    )

    print(
        "Vector ingestion completed successfully."
    )


# ============================================================
# MAIN INGESTION PIPELINE
# ============================================================


def ingest_video(
    video_id: str,
) -> None:
    """
    Execute the complete embedding ingestion pipeline for one
    YouTube video.
    """

    print_section(
        "Embedding ingestion configuration"
    )

    chunk_file = (
        CHUNKS_DIR
        / f"{video_id}.json"
    )

    print(
        f"BASE_DIR        : {BASE_DIR}"
    )

    print(
        f"CHUNKS_DIR      : {CHUNKS_DIR}"
    )

    print(
        f"CHUNK FILE      : {chunk_file}"
    )

    print(
        f"EXISTS          : {chunk_file.exists()}"
    )

    print(
        f"Embedding model : {EMBEDDING_MODEL_NAME}"
    )

    print(
        f"Qdrant URL      : {QDRANT_URL}"
    )

    print(
        f"Collection      : {COLLECTION_NAME}"
    )

    # --------------------------------------------------------
    # Load chunked transcript.
    # --------------------------------------------------------

    print_section(
        "Loading transcript chunks"
    )

    data = load_chunks(
        video_id
    )

    chunks = data.get(
        "chunks",
        []
    )

    if not isinstance(
        chunks,
        list,
    ):
        raise ValueError(
            "'chunks' must be a list."
        )

    validate_chunks(
        chunks
    )

    print(
        f"Loaded chunks: {len(chunks)}"
    )

    # --------------------------------------------------------
    # Extract text that will be embedded.
    # --------------------------------------------------------

    print_section(
        "Preparing embedding text"
    )

    texts = [
        extract_chunk_text(chunk)
        for chunk in chunks
    ]

    print(
        f"Texts prepared: {len(texts)}"
    )

    # --------------------------------------------------------
    # Load embedding model.
    # --------------------------------------------------------

    print_section(
        "Loading embedding model"
    )

    model = load_embedding_model()

    # --------------------------------------------------------
    # Generate embeddings.
    # --------------------------------------------------------

    print_section(
        "Generating embeddings"
    )

    embeddings = generate_embeddings(
        model=model,
        texts=texts,
    )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Embedding count does not match chunk count."
        )

    vector_size = len(
        embeddings[0]
    )

    print(
        f"Generated vectors : {len(embeddings)}"
    )

    print(
        f"Vector dimensions  : {vector_size}"
    )

    # --------------------------------------------------------
    # Connect to Qdrant.
    # --------------------------------------------------------

    print_section(
        "Connecting to Qdrant"
    )

    client = create_qdrant_client()

    # --------------------------------------------------------
    # Make sure the collection exists.
    # --------------------------------------------------------

    print_section(
        "Checking Qdrant collection"
    )

    ensure_collection(
        client=client,
        vector_size=vector_size,
    )

    # --------------------------------------------------------
    # Build Qdrant points.
    # --------------------------------------------------------

    print_section(
        "Building Qdrant points"
    )

    points = build_points(
        video_id=video_id,
        chunks=chunks,
        embeddings=embeddings,
    )

    print(
        f"Points prepared: {len(points)}"
    )

    # --------------------------------------------------------
    # Upload vectors and metadata.
    # --------------------------------------------------------

    print_section(
        "Uploading vectors"
    )

    upload_points(
        client=client,
        points=points,
    )

    # --------------------------------------------------------
    # Final summary.
    # --------------------------------------------------------

    print_section(
        "Embedding ingestion completed successfully."
    )

    print(
        f"Video ID          : {video_id}"
    )

    print(
        f"Chunks ingested   : {len(chunks)}"
    )

    print(
        f"Vector dimensions : {vector_size}"
    )

    print(
        f"Qdrant collection : {COLLECTION_NAME}"
    )

    print(
        f"Qdrant URL        : {QDRANT_URL}"
    )


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================


def main() -> None:
    """
    Command-line entry point.

    Expected usage:

        python scripts/ingest_embeddings.py <video_id>
    """

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "  python scripts/ingest_embeddings.py <video_id>"
        )

        print()

        print(
            "Example:"
        )

        print(
            "  python scripts/ingest_embeddings.py dyG4JBKh6tA"
        )

        raise SystemExit(1)

    video_id = sys.argv[1].strip()

    if not video_id:

        print(
            "Error: video_id cannot be empty."
        )

        raise SystemExit(1)

    try:

        ingest_video(
            video_id
        )

    except KeyboardInterrupt:

        print(
            "\nIngestion cancelled by user."
        )

        raise SystemExit(130)

    except Exception as error:

        print()
        print("=" * 60)
        print("INGESTION FAILED")
        print("=" * 60)

        print(
            f"Error: {error}"
        )

        raise SystemExit(1)


# ============================================================
# PYTHON ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()