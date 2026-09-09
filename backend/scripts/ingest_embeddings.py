"""
Generate embeddings for transcript chunks and store them in Qdrant.

Pipeline:

    Chunked Transcript
            ↓
    Video / Pattern Metadata
            ↓
    English Text Extraction
            ↓
    Local Embedding Model
            ↓
    Vector Generation
            ↓
    Qdrant Vector Database

This script keeps ingestion separate from retrieval.

Metadata design:
    Every ingested chunk carries the canonical DSA pattern and its
    pattern-specific playlist.

Example:
    pattern  = "two_pointer"
    playlist = "DSA_Patterns_Two_Pointer"

The playlist is ALWAYS derived from the canonical pattern taxonomy.
It is never manually constructed here.

Usage:
    python scripts/ingest_embeddings.py <video_id> --pattern <pattern>

Examples:
    python scripts/ingest_embeddings.py dyG4JBKh6tA --pattern two_pointer

    python scripts/ingest_embeddings.py dyG4JBKh6tA \
        --pattern two_pointer \
        --sub-pattern pair_search

Notes:
    - Existing chunk metadata is preserved.
    - If chunks already contain pattern metadata, it can be reused.
    - Explicit CLI metadata takes precedence over missing chunk metadata.
    - A missing pattern is treated as an error instead of guessing.
    - Qdrant payload indexes are ensured for filterable metadata fields.
"""

from __future__ import annotations


# ============================================================
# STANDARD LIBRARY IMPORTS
# ============================================================

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any


# ============================================================
# PROJECT PATH CONFIGURATION
# ============================================================

# Resolve the backend directory from:
#
#     backend/scripts/ingest_embeddings.py
#
# parent        -> backend/scripts
# parent.parent -> backend

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CHUNKS_DIR = DATA_DIR / "chunks"


# ============================================================
# PYTHON PATH
# ============================================================

# The script is normally executed directly:
#
#     python scripts/ingest_embeddings.py ...
#
# In that situation Python starts with `backend/scripts` on sys.path.
# Add the backend root so that project services can be imported reliably.

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# PROJECT METADATA IMPORTS
# ============================================================

from app.services.dsa_taxonomy import (  # noqa: E402
    get_playlist_name,
    is_valid_pattern,
    is_valid_sub_pattern,
)

from app.services.video_metadata_schema import (  # noqa: E402
    VideoMetadata,
    validate_video_metadata,
)


# ============================================================
# THIRD-PARTY IMPORTS
# ============================================================

from dotenv import load_dotenv  # noqa: E402

from qdrant_client import QdrantClient  # noqa: E402

from qdrant_client.models import (  # noqa: E402
    Distance,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from sentence_transformers import SentenceTransformer  # noqa: E402


load_dotenv()


# ============================================================
# QDRANT CONFIGURATION
# ============================================================

# Qdrant can run locally or remotely.
#
# Local development defaults to:
#
#     http://localhost:6333
#
# These values can later be moved into a dedicated settings module.

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

# Local Sentence Transformers model.
#
# Using a local model keeps transcript content out of external
# embedding APIs and keeps ingestion inexpensive and reproducible.

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


# ============================================================
# BATCH CONFIGURATION
# ============================================================

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
    """Print a visually separated command-line section."""

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


# ============================================================
# CHUNK LOADING
# ============================================================

def load_chunks(
    video_id: str,
) -> dict[str, Any]:
    """
    Load the chunked transcript JSON for one video.

    Expected file:
        backend/data/chunks/<video_id>.json
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

    English translated text is preferred.
    Original transcript text is the fallback.
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

        text = extract_chunk_text(chunk)

        if not text:
            raise ValueError(
                f"Chunk {chunk.get('chunk_id')} "
                "does not contain usable text."
            )


# ============================================================
# VIDEO METADATA
# ============================================================

def build_video_metadata_from_chunks(
    video_id: str,
    chunks: list[dict[str, Any]],
    *,
    pattern_override: str | None = None,
    sub_pattern_override: str | None = None,
) -> VideoMetadata:
    """
    Build validated VideoMetadata from the chunk data.

    Metadata resolution order:

        1. Explicit CLI pattern
        2. Pattern already present in the chunks

    For sub-pattern:

        1. Explicit CLI sub-pattern
        2. A single sub-pattern already present in chunks
        3. No sub-pattern at video level

    The function deliberately refuses to guess the DSA pattern.
    """

    first_chunk = chunks[0]

    pattern = (
        pattern_override
        or first_chunk.get("pattern")
    )

    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError(
            "DSA pattern is required. "
            "Pass it with --pattern or add 'pattern' "
            "metadata to the chunk JSON."
        )

    pattern = pattern.strip()

    if not is_valid_pattern(pattern):
        raise ValueError(
            f"Unknown DSA pattern: {pattern!r}."
        )

    # --------------------------------------------------------
    # Video title.
    #
    # Prefer an existing chunk value. If it does not exist,
    # use a safe fallback rather than inventing a title.
    # --------------------------------------------------------

    video_title = str(
        first_chunk.get(
            "video_title",
            video_id,
        )
    ).strip()

    if not video_title:
        video_title = video_id

    # --------------------------------------------------------
    # Playlist is ALWAYS derived from pattern.
    # --------------------------------------------------------

    playlist = get_playlist_name(pattern)

    # --------------------------------------------------------
    # Optional playlist ID.
    # --------------------------------------------------------

    playlist_id = first_chunk.get(
        "playlist_id"
    )

    if playlist_id is not None:
        playlist_id = str(playlist_id)

    # --------------------------------------------------------
    # Optional video order.
    # --------------------------------------------------------

    video_order = first_chunk.get(
        "video_order"
    )

    if video_order is not None:
        try:
            video_order = int(video_order)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "video_order must be an integer."
            ) from error

    # --------------------------------------------------------
    # Collect existing video-level sub-patterns.
    # --------------------------------------------------------

    discovered_sub_patterns: list[str] = []

    existing_video_sub_patterns = first_chunk.get(
        "video_sub_patterns"
    )

    if isinstance(
        existing_video_sub_patterns,
        list,
    ):
        for value in existing_video_sub_patterns:
            if isinstance(value, str):
                value = value.strip()

                if value:
                    discovered_sub_patterns.append(value)

    for chunk in chunks:
        value = chunk.get(
            "sub_pattern"
        )

        if isinstance(value, str):
            value = value.strip()

            if value and value not in discovered_sub_patterns:
                discovered_sub_patterns.append(value)

    # --------------------------------------------------------
    # Explicit CLI sub-pattern takes precedence.
    # --------------------------------------------------------

    if sub_pattern_override:
        sub_patterns = (
            sub_pattern_override.strip(),
        )

    else:
        sub_patterns = tuple(
            discovered_sub_patterns
        )

    # --------------------------------------------------------
    # Validate every discovered sub-pattern.
    # --------------------------------------------------------

    for sub_pattern in sub_patterns:

        if not is_valid_sub_pattern(
            pattern,
            sub_pattern,
        ):
            raise ValueError(
                f"Invalid sub-pattern {sub_pattern!r} "
                f"for pattern {pattern!r}."
            )

    # --------------------------------------------------------
    # Source URL.
    # --------------------------------------------------------

    source_url = first_chunk.get(
        "source_url"
    )

    if source_url is not None:
        source_url = str(source_url)

    metadata = VideoMetadata(
        video_id=video_id,
        video_title=video_title,
        pattern=pattern,
        playlist=playlist,
        playlist_id=playlist_id,
        video_order=video_order,
        sub_patterns=tuple(sub_patterns),
        source_url=source_url,
    )

    validate_video_metadata(metadata)

    return metadata


def enrich_chunks_with_metadata(
    chunks: list[dict[str, Any]],
    metadata: VideoMetadata,
) -> list[dict[str, Any]]:
    """
    Add canonical video metadata to every chunk.

    Existing chunk-specific fields are preserved.

    Sub-pattern rules:

        - Keep an existing valid chunk-level sub_pattern.
        - If the video has exactly one sub-pattern, inherit it.
        - If the video has multiple sub-patterns, do not guess.

    This prevents incorrectly labeling every chunk in a multi-topic
    video with one arbitrary sub-pattern.
    """

    validate_video_metadata(metadata)

    enriched_chunks: list[dict[str, Any]] = []

    for chunk in chunks:

        enriched = dict(chunk)

        # ----------------------------------------------------
        # Canonical video metadata.
        # ----------------------------------------------------

        enriched["video_id"] = metadata.video_id
        enriched["video_title"] = metadata.video_title
        enriched["pattern"] = metadata.pattern
        enriched["playlist"] = metadata.playlist

        if metadata.playlist_id is not None:
            enriched["playlist_id"] = metadata.playlist_id

        if metadata.video_order is not None:
            enriched["video_order"] = metadata.video_order

        if metadata.source_url is not None:
            enriched["source_url"] = metadata.source_url

        if metadata.sub_patterns:
            enriched["video_sub_patterns"] = list(
                metadata.sub_patterns
            )

        # ----------------------------------------------------
        # Chunk-level sub-pattern.
        # ----------------------------------------------------

        existing_sub_pattern = enriched.get(
            "sub_pattern"
        )

        if existing_sub_pattern is not None:

            if not isinstance(
                existing_sub_pattern,
                str,
            ):
                raise ValueError(
                    f"Chunk {chunk.get('chunk_id')!r} "
                    "'sub_pattern' must be a string."
                )

            existing_sub_pattern = (
                existing_sub_pattern.strip()
            )

            if not is_valid_sub_pattern(
                metadata.pattern,
                existing_sub_pattern,
            ):
                raise ValueError(
                    f"Chunk {chunk.get('chunk_id')!r} "
                    f"contains invalid sub_pattern "
                    f"{existing_sub_pattern!r} for pattern "
                    f"{metadata.pattern!r}."
                )

            enriched["sub_pattern"] = (
                existing_sub_pattern
            )

        elif len(metadata.sub_patterns) == 1:

            enriched["sub_pattern"] = (
                metadata.sub_patterns[0]
            )

        enriched_chunks.append(enriched)

    return enriched_chunks


# ============================================================
# EMBEDDING MODEL
# ============================================================

def load_embedding_model() -> SentenceTransformer:
    """Load the local Sentence Transformers embedding model."""

    print(
        f"Loading embedding model: "
        f"{EMBEDDING_MODEL_NAME}"
    )

    return SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )


def generate_embeddings(
    model: SentenceTransformer,
    texts: list[str],
) -> list[list[float]]:
    """
    Generate normalized embeddings in batches.

    Normalization makes the vectors suitable for cosine similarity.
    """

    embeddings = model.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    return embeddings.tolist()


# ============================================================
# QDRANT CLIENT
# ============================================================

def create_qdrant_client() -> QdrantClient:
    """Create a Qdrant client using environment configuration."""

    print(
        f"Connecting to Qdrant: {QDRANT_URL}"
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
# QDRANT PAYLOAD INDEX MANAGEMENT
# ============================================================

def ensure_payload_indexes(
    client: QdrantClient,
) -> None:
    """
    Ensure all metadata fields used by retrieval filters have
    Qdrant payload indexes.

    Qdrant requires an appropriate payload index for efficient
    filtered search on keyword metadata fields.

    This function is intentionally called even when the collection
    already exists. That is important because an older collection
    may contain vectors and payloads but still be missing the
    required payload indexes.
    """

    print(
        "Checking Qdrant payload indexes..."
    )

    collection_info = client.get_collection(
        collection_name=COLLECTION_NAME,
    )

    existing_payload_schema = (
        collection_info.payload_schema
        or {}
    )

    # These fields are currently used by retrieval.py filters.
    #
    # pattern:
    #     Primary DSA pattern filter.
    #
    # sub_pattern:
    #     More specific pattern filter.

    required_indexes = (
        "pattern",
        "sub_pattern",
    )

    for field_name in required_indexes:

        if field_name in existing_payload_schema:

            print(
                f"Payload index already exists: "
                f"{field_name}"
            )

            continue

        print(
            f"Creating payload index: "
            f"{field_name}"
        )

        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=PayloadSchemaType.KEYWORD,
            wait=True,
        )

        print(
            f"Payload index created: "
            f"{field_name}"
        )

    print(
        "Qdrant payload index check completed."
    )


# ============================================================
# COLLECTION MANAGEMENT
# ============================================================

def ensure_collection(
    client: QdrantClient,
    vector_size: int,
) -> None:
    """
    Create the Qdrant collection if it does not already exist.

    Vector size is detected from the embedding model instead of
    being hard-coded.

    If the collection already exists, its required payload indexes
    are still checked and created when missing.
    """

    existing_collections = (
        client.get_collections()
    )

    collection_names = {
        collection.name
        for collection in (
            existing_collections.collections
        )
    }

    if COLLECTION_NAME in collection_names:

        print(
            f"Qdrant collection already exists: "
            f"{COLLECTION_NAME}"
        )

        # IMPORTANT:
        # Existing collections may have been created before the
        # retrieval filters were introduced. Therefore, do not
        # return before ensuring payload indexes.
        ensure_payload_indexes(
            client=client,
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

    # The collection is new, so create the payload indexes now.
    ensure_payload_indexes(
        client=client,
    )


# ============================================================
# PAYLOAD CREATION
# ============================================================

def build_payload(
    video_id: str,
    chunk: dict[str, Any],
) -> dict[str, Any]:
    """
    Build the complete Qdrant payload for one transcript chunk.

    Pattern-specific metadata is intentionally stored directly in
    the payload because Qdrant can later filter on these fields.

    Example filters:

        pattern = "two_pointer"

        sub_pattern = "pair_search"

        playlist = "DSA_Patterns_Two_Pointer"
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
    # Canonical DSA metadata.
    #
    # These fields should already have been enriched before this
    # function is called.
    # --------------------------------------------------------

    metadata_fields = [
        "video_title",
        "playlist",
        "playlist_id",
        "pattern",
        "sub_pattern",
        "video_sub_patterns",
        "video_order",
        "source_url",
        "topic",
    ]

    for field in metadata_fields:

        if field in chunk:

            value = chunk[field]

            # Do not store empty optional strings.
            if value == "":
                continue

            payload[field] = value

    return payload


# ============================================================
# VECTOR POINT CREATION
# ============================================================

def build_points(
    video_id: str,
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> list[PointStruct]:
    """
    Convert enriched chunks and embeddings into Qdrant points.

    Point IDs are deterministic based on:

        video_id + chunk_id

    Re-running ingestion therefore updates the same Qdrant point
    instead of creating duplicates.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Chunk count and embedding count must match."
        )

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

        point_key = (
            f"{video_id}_{chunk_id}"
        )

        deterministic_uuid = uuid.uuid5(
            uuid.NAMESPACE_URL,
            point_key,
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


# ============================================================
# QDRANT UPLOAD
# ============================================================

def upload_points(
    client: QdrantClient,
    points: list[PointStruct],
) -> None:
    """
    Upload vector points and metadata to Qdrant.

    Qdrant upsert keeps ingestion idempotent.
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
    *,
    pattern: str | None = None,
    sub_pattern: str | None = None,
) -> None:
    """
    Execute the complete ingestion pipeline for one video.

    Steps:

        1. Load chunked transcript.
        2. Resolve and validate DSA metadata.
        3. Enrich every chunk with metadata.
        4. Extract embedding text.
        5. Load embedding model.
        6. Generate vectors.
        7. Connect to Qdrant.
        8. Ensure collection exists.
        9. Ensure payload indexes exist.
        10. Build deterministic Qdrant points.
        11. Upload vectors and metadata.
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
    # Load chunks.
    # --------------------------------------------------------

    print_section(
        "Loading transcript chunks"
    )

    data = load_chunks(
        video_id
    )

    chunks = data.get(
        "chunks",
        [],
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
    # Resolve video metadata.
    # --------------------------------------------------------

    print_section(
        "Resolving DSA pattern metadata"
    )

    metadata = build_video_metadata_from_chunks(
        video_id=video_id,
        chunks=chunks,
        pattern_override=pattern,
        sub_pattern_override=sub_pattern,
    )

    print(
        f"Pattern        : {metadata.pattern}"
    )

    print(
        f"Playlist       : {metadata.playlist}"
    )

    print(
        f"Video title    : {metadata.video_title}"
    )

    print(
        f"Sub-patterns   : "
        f"{list(metadata.sub_patterns) or 'Not assigned'}"
    )

    # --------------------------------------------------------
    # Enrich chunks.
    # --------------------------------------------------------

    print_section(
        "Enriching chunks with metadata"
    )

    chunks = enrich_chunks_with_metadata(
        chunks=chunks,
        metadata=metadata,
    )

    print(
        "Chunk metadata enrichment completed."
    )

    # --------------------------------------------------------
    # Extract text.
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
        f"Vector dimensions : {vector_size}"
    )

    # --------------------------------------------------------
    # Connect to Qdrant.
    # --------------------------------------------------------

    print_section(
        "Connecting to Qdrant"
    )

    client = create_qdrant_client()

    # --------------------------------------------------------
    # Ensure collection.
    #
    # This also ensures required payload indexes.
    # --------------------------------------------------------

    print_section(
        "Checking Qdrant collection"
    )

    ensure_collection(
        client=client,
        vector_size=vector_size,
    )

    # --------------------------------------------------------
    # Build points.
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
        "Uploading vectors and metadata"
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
        f"Pattern            : {metadata.pattern}"
    )

    print(
        f"Playlist           : {metadata.playlist}"
    )

    print(
        f"Chunks ingested    : {len(chunks)}"
    )

    print(
        f"Vector dimensions  : {vector_size}"
    )

    print(
        f"Qdrant collection  : {COLLECTION_NAME}"
    )

    print(
        f"Qdrant URL         : {QDRANT_URL}"
    )


# ============================================================
# CLI
# ============================================================

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate embeddings for a DSA transcript "
            "and ingest vectors + metadata into Qdrant."
        )
    )

    parser.add_argument(
        "video_id",
        help="YouTube video ID.",
    )

    parser.add_argument(
        "--pattern",
        required=False,
        help=(
            "Canonical DSA pattern slug, for example "
            "'two_pointer'. If omitted, the script attempts "
            "to read pattern metadata already present in the "
            "chunk JSON."
        ),
    )

    parser.add_argument(
        "--sub-pattern",
        required=False,
        help=(
            "Optional canonical sub-pattern slug, for example "
            "'pair_search'."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """
    Command-line entry point.

    Examples:

        python scripts/ingest_embeddings.py dyG4JBKh6tA \
            --pattern two_pointer

        python scripts/ingest_embeddings.py dyG4JBKh6tA \
            --pattern two_pointer \
            --sub-pattern pair_search
    """

    args = parse_arguments()

    video_id = args.video_id.strip()

    if not video_id:
        print(
            "Error: video_id cannot be empty."
        )

        raise SystemExit(1)

    try:

        ingest_video(
            video_id=video_id,
            pattern=args.pattern,
            sub_pattern=args.sub_pattern,
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