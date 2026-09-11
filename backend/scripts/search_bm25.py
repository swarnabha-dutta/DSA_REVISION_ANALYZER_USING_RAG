"""
Standalone BM25 Search
=======================

Purpose:
    Query the reusable BM25 index created by:

        scripts/build_bm25_index.py

This script is intentionally independent from the hybrid retrieval
pipeline.

It allows us to validate lexical retrieval before integrating BM25
with Qdrant semantic search and Reciprocal Rank Fusion (RRF).

Usage:

    python scripts/search_bm25.py "dynamic programming"

Optional Top-K:

    python scripts/search_bm25.py "dynamic programming" 10

Optional metadata filters:

    python scripts/search_bm25.py "memoization" 5 dynamic_programming

    python scripts/search_bm25.py \
        "memoization" \
        5 \
        dynamic_programming \
        memoization
"""

from __future__ import annotations

import sys
from pathlib import Path


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
    BM25Index,
    BM25_INDEX_FILE,
    get_allowed_document_indices,
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_TOP_K = 5


# ============================================================
# CLI HELPERS
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


def print_usage() -> None:
    """
    Print command-line usage information.
    """

    print(
        "Usage:"
    )

    print(
        '  python scripts/search_bm25.py '
        '"your query"'
    )

    print()

    print(
        "Optional Top-K:"
    )

    print(
        '  python scripts/search_bm25.py '
        '"your query" 10'
    )

    print()

    print(
        "Optional pattern:"
    )

    print(
        '  python scripts/search_bm25.py '
        '"your query" 5 dynamic_programming'
    )

    print()

    print(
        "Optional pattern + sub-pattern:"
    )

    print(
        '  python scripts/search_bm25.py '
        '"your query" 5 '
        'dynamic_programming memoization'
    )


# ============================================================
# RESULT DISPLAY
# ============================================================

def display_results(
    results,
) -> None:
    """
    Display BM25 results in a readable format.
    """

    if not results:

        print(
            "No BM25 results found."
        )

        return

    for rank, (
        document,
        score,
    ) in enumerate(
        results,
        start=1,
    ):

        print()

        print(
            f"[{rank}] "
            f"BM25 Score: "
            f"{score:.4f}"
        )

        print(
            f"Point ID   : "
            f"{document.point_id}"
        )

        print(
            f"Chunk ID   : "
            f"{document.chunk_id}"
        )

        print(
            f"Video ID   : "
            f"{document.video_id}"
        )

        print(
            f"Title      : "
            f"{document.video_title}"
        )

        print(
            f"Pattern    : "
            f"{document.pattern}"
        )

        print(
            f"Sub-pattern: "
            f"{document.sub_pattern}"
        )

        print(
            f"Playlist   : "
            f"{document.playlist}"
        )

        print(
            f"Timestamp  : "
            f"{document.start:.2f}s"
            f" → "
            f"{document.end:.2f}s"
        )

        # Keep CLI output compact while still showing
        # enough text to manually verify lexical relevance.

        preview = (
            document.text_en
            or document.text
            or ""
        )

        preview = (
            preview
            .replace(
                "\n",
                " ",
            )
            .strip()
        )

        max_preview_length = 240

        if len(preview) > (
            max_preview_length
        ):

            preview = (
                preview[
                    :max_preview_length
                ]
                + "..."
            )

        print(
            f"Text       : "
            f"{preview}"
        )


# ============================================================
# SEARCH
# ============================================================

def search_bm25(
    *,
    query: str,
    top_k: int,
    pattern: str | None = None,
    sub_pattern: str | None = None,
) -> None:
    """
    Load the persisted BM25 index and perform lexical retrieval.
    """

    print_section(
        "BM25 SEARCH CONFIGURATION"
    )

    print(
        f"Query       : {query}"
    )

    print(
        f"Top-K       : {top_k}"
    )

    print(
        f"Pattern     : "
        f"{pattern or 'None'}"
    )

    print(
        f"Sub-pattern : "
        f"{sub_pattern or 'None'}"
    )

    print(
        f"Index       : "
        f"{BM25_INDEX_FILE}"
    )

    # --------------------------------------------------------
    # Load persisted index.
    # --------------------------------------------------------

    print_section(
        "Loading BM25 Index"
    )

    index = BM25Index.load(
        BM25_INDEX_FILE
    )

    print(
        f"Documents : "
        f"{index.document_count}"
    )

    print(
        f"Vocabulary: "
        f"{len(index.document_frequency)}"
    )

    # --------------------------------------------------------
    # Build metadata restriction.
    # --------------------------------------------------------

    allowed_indices = (
        get_allowed_document_indices(
            index,
            pattern=pattern,
            sub_pattern=sub_pattern,
        )
    )

    print(
        f"Allowed documents: "
        f"{len(allowed_indices)}"
    )

    # --------------------------------------------------------
    # Perform BM25 search.
    # --------------------------------------------------------

    print_section(
        "Searching BM25"
    )

    results = index.search(
        query=query,
        top_k=top_k,
        allowed_document_indices=(
            allowed_indices
        ),
    )

    print(
        f"Retrieved results: "
        f"{len(results)}"
    )

    # --------------------------------------------------------
    # Display results.
    # --------------------------------------------------------

    print_section(
        "BM25 RESULTS"
    )

    display_results(
        results
    )


# ============================================================
# CLI ARGUMENT PARSING
# ============================================================

def main() -> None:
    """
    Command-line entry point.
    """

    if len(sys.argv) < 2:

        print_usage()

        raise SystemExit(1)

    query = sys.argv[1].strip()

    if not query:

        print(
            "Error: query cannot be empty."
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # Optional Top-K.
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

    if top_k <= 0:

        print(
            "Error: Top-K must be greater than 0."
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # Optional pattern.
    # --------------------------------------------------------

    pattern = None

    if len(sys.argv) >= 4:

        pattern = (
            sys.argv[3].strip()
            or None
        )

    # --------------------------------------------------------
    # Optional sub-pattern.
    # --------------------------------------------------------

    sub_pattern = None

    if len(sys.argv) >= 5:

        sub_pattern = (
            sys.argv[4].strip()
            or None
        )

    # --------------------------------------------------------
    # Execute search.
    # --------------------------------------------------------

    try:

        search_bm25(
            query=query,
            top_k=top_k,
            pattern=pattern,
            sub_pattern=sub_pattern,
        )

    except KeyboardInterrupt:

        print()

        print(
            "Search interrupted."
        )

        raise SystemExit(130)


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()