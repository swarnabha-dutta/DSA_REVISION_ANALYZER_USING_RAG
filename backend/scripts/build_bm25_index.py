"""
Build Reusable BM25 Index
==========================

Purpose:
    Build a persistent BM25 lexical index from the canonical chunks
    already stored in the Qdrant collection.

Pipeline:

    Qdrant
        ↓
    Scroll all points
        ↓
    Extract payloads
        ↓
    Convert to BM25Document
        ↓
    Build BM25Index
        ↓
    Persist index.json

The resulting index is reused during query-time lexical retrieval.

Important:
    This script does NOT modify the Qdrant collection.

    It only reads existing Qdrant points and creates a local BM25 index.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BASE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# PROJECT IMPORTS
# ============================================================

from app.services.bm25_index import (  # noqa: E402
    BM25Document,
    BM25_INDEX_FILE,
    build_document_from_payload,
    build_bm25_index,
)

from app.services.retrieval import (  # noqa: E402
    COLLECTION_NAME,
    create_qdrant_client,
)


# ============================================================
# CONFIGURATION
# ============================================================

QDRANT_SCROLL_BATCH_SIZE = 256


# ============================================================
# CLI OUTPUT
# ============================================================

def print_section(
    title: str,
) -> None:
    """
    Print a visually separated CLI section.
    """

    print()

    print(
        "=" * 60
    )

    print(title)

    print(
        "=" * 60
    )


# ============================================================
# QDRANT COLLECTION VALIDATION
# ============================================================

def verify_collection(
    client: Any,
) -> None:
    """
    Verify that the configured Qdrant collection exists.
    """

    collections = (
        client.get_collections()
    )

    collection_names = {
        collection.name
        for collection
        in collections.collections
    }

    if COLLECTION_NAME not in collection_names:
        raise RuntimeError(
            f"Qdrant collection "
            f"'{COLLECTION_NAME}' "
            "does not exist."
        )


# ============================================================
# QDRANT POINT LOADING
# ============================================================

def load_qdrant_documents(
    client: Any,
) -> list[BM25Document]:
    """
    Read every point from the Qdrant collection and convert each
    point into a BM25Document.

    Qdrant scrolling is used instead of vector search because we
    need the complete corpus, not only the top semantic matches.
    """

    documents: list[
        BM25Document
    ] = []

    offset: Any = None

    total_points_seen = 0

    skipped_points = 0

    while True:

        points, next_offset = (
            client.scroll(
                collection_name=COLLECTION_NAME,
                limit=QDRANT_SCROLL_BATCH_SIZE,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
        )

        if not points:
            break

        total_points_seen += len(
            points
        )

        for point in points:

            payload = (
                point.payload
            )

            if not isinstance(
                payload,
                dict,
            ):
                skipped_points += 1

                continue

            point_id = str(
                point.id
            )

            search_text = str(
                payload.get(
                    "text_en",
                    "",
                )
                or payload.get(
                    "text",
                    "",
                )
                or ""
            ).strip()

            if not search_text:
                skipped_points += 1

                continue

            document = (
                build_document_from_payload(
                    point_id=point_id,
                    payload=payload,
                )
            )

            if not document.tokens:
                skipped_points += 1

                continue

            documents.append(
                document
            )

        print(
            f"Loaded Qdrant points: "
            f"{total_points_seen}",
            end="\r",
        )

        if next_offset is None:
            break

        offset = next_offset

    print()

    print(
        f"Total Qdrant points : "
        f"{total_points_seen}"
    )

    print(
        f"Indexed documents   : "
        f"{len(documents)}"
    )

    print(
        f"Skipped documents   : "
        f"{skipped_points}"
    )

    return documents


# ============================================================
# DUPLICATE PROTECTION
# ============================================================

def deduplicate_documents(
    documents: list[BM25Document],
) -> list[BM25Document]:
    """
    Remove duplicate Qdrant point IDs.

    A BM25 corpus should contain one lexical document per Qdrant point.
    """

    seen_ids: set[str] = set()

    unique_documents: list[
        BM25Document
    ] = []

    for document in documents:

        if document.point_id in seen_ids:
            continue

        seen_ids.add(
            document.point_id
        )

        unique_documents.append(
            document
        )

    return unique_documents


# ============================================================
# INDEX VALIDATION
# ============================================================

def validate_index(
    documents: list[BM25Document],
) -> None:
    """
    Validate the corpus before building the persistent index.
    """

    if not documents:
        raise RuntimeError(
            "No valid documents were found "
            "in the Qdrant collection."
        )

    point_ids = {
        document.point_id
        for document in documents
    }

    if len(point_ids) != len(
        documents
    ):
        raise RuntimeError(
            "Duplicate Qdrant point IDs "
            "remain after deduplication."
        )

    empty_token_documents = [
        document
        for document in documents
        if not document.tokens
    ]

    if empty_token_documents:
        raise RuntimeError(
            "Some documents contain no searchable tokens."
        )


# ============================================================
# BUILD AND SAVE
# ============================================================

def build_and_save_index(
    documents: list[BM25Document],
) -> None:
    """
    Build the BM25 index and persist it to disk.
    """

    print_section(
        "Building BM25 Index"
    )

    index = build_bm25_index(
        documents
    )

    print(
        f"Documents        : "
        f"{index.document_count}"
    )

    print(
        f"Vocabulary size   : "
        f"{len(index.document_frequency)}"
    )

    print(
        f"Average doc length: "
        f"{index.average_document_length:.2f}"
    )

    print(
        f"BM25 k1          : "
        f"{index.k1}"
    )

    print(
        f"BM25 b           : "
        f"{index.b}"
    )

    print_section(
        "Persisting BM25 Index"
    )

    index.save(
        BM25_INDEX_FILE
    )

    print(
        f"Index saved to:"
    )

    print(
        f"  {BM25_INDEX_FILE}"
    )


# ============================================================
# SELF-VERIFICATION
# ============================================================

def verify_persisted_index() -> None:
    """
    Load the persisted index again to verify that serialization
    and deserialization work correctly.
    """

    print_section(
        "Verifying Persisted Index"
    )

    from app.services.bm25_index import (
        BM25Index,
    )

    loaded_index = (
        BM25Index.load(
            BM25_INDEX_FILE
        )
    )

    print(
        f"Loaded documents : "
        f"{loaded_index.document_count}"
    )

    print(
        f"Loaded vocabulary: "
        f"{len(loaded_index.document_frequency)}"
    )

    if (
        loaded_index.document_count
        == 0
    ):
        raise RuntimeError(
            "Persisted BM25 index contains zero documents."
        )

    print(
        "✓ Persistent BM25 index "
        "loaded successfully."
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """
    Build the reusable BM25 index from Qdrant.

    Usage:

        python scripts/build_bm25_index.py
    """

    print_section(
        "BM25 INDEX BUILD"
    )

    print(
        f"Qdrant collection: "
        f"{COLLECTION_NAME}"
    )

    print(
        f"Output index      : "
        f"{BM25_INDEX_FILE}"
    )

    print_section(
        "Connecting to Qdrant"
    )

    client = (
        create_qdrant_client()
    )

    print(
        "Qdrant client created."
    )

    print_section(
        "Checking Qdrant Collection"
    )

    verify_collection(
        client
    )

    print(
        f"Collection found: "
        f"{COLLECTION_NAME}"
    )

    print_section(
        "Loading Qdrant Corpus"
    )

    documents = (
        load_qdrant_documents(
            client
        )
    )

    print_section(
        "Deduplicating Corpus"
    )

    before_count = len(
        documents
    )

    documents = (
        deduplicate_documents(
            documents
        )
    )

    after_count = len(
        documents
    )

    print(
        f"Before deduplication: "
        f"{before_count}"
    )

    print(
        f"After deduplication : "
        f"{after_count}"
    )

    print_section(
        "Validating Corpus"
    )

    validate_index(
        documents
    )

    print(
        "✓ Corpus validation passed."
    )

    build_and_save_index(
        documents
    )

    verify_persisted_index()

    print_section(
        "BM25 INDEX BUILD COMPLETE"
    )

    print(
        "✓ Reusable BM25 index is ready."
    )


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()