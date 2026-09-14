"""
Phase 14.5 — Context Provenance Test

Verifies that provenance information from retrieved course chunks
remains available after Context Assembly.

Run from:
    backend/

Command:
    python .\scripts\test_context_provenance.py
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PATH SETUP
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# IMPORT
# ============================================================

from app.services.context_assembler import assemble_context  # noqa: E402


# ============================================================
# ASSERTION HELPER
# ============================================================

def check(
    name: str,
    condition: bool,
) -> None:
    """
    Validate one test condition.
    """

    if not condition:
        raise AssertionError(
            f"{name}: condition failed."
        )

    print(f"✓ {name}")


# ============================================================
# MAIN TEST
# ============================================================

def main() -> None:

    print("=" * 60)
    print("PHASE 14.5 — CONTEXT PROVENANCE TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Synthetic retrieved result.
    #
    # This represents the metadata that comes from the
    # retrieval layer for a course chunk.
    # --------------------------------------------------------

    results = [
        {
            "point_id": "provenance-001",

            "semantic_result": {
                "text": (
                    "Two Pointer is a technique where two indices "
                    "move through a sequence according to a "
                    "problem-specific condition."
                ),

                "metadata": {
                    "video_id": "dyG4JBKh6tA",
                    "pattern": "two_pointer",
                    "sub_pattern": "opposite_direction",
                    "timestamp_start": 83.5,
                    "timestamp_end": 127.9,
                },
            },

            "rrf_score": 0.95,
            "reranker_score": 0.92,
        }
    ]

    # --------------------------------------------------------
    # Assemble the context.
    # --------------------------------------------------------

    context = assemble_context(
        query="Explain Two Pointer",
        results=results,
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        top_k=5,
    )

    check(
        "Context item created",
        len(context.items) == 1,
    )

    item = context.items[0]

    # --------------------------------------------------------
    # Provenance identity
    # --------------------------------------------------------

    check(
        "Point ID preserved",
        item.point_id == "provenance-001",
    )

    check(
        "Video ID preserved",
        item.video_id == "dyG4JBKh6tA",
    )

    # --------------------------------------------------------
    # DSA classification provenance
    # --------------------------------------------------------

    check(
        "Pattern provenance preserved",
        item.pattern == "two_pointer",
    )

    check(
        "Sub-pattern provenance preserved",
        item.sub_pattern == "opposite_direction",
    )

    # --------------------------------------------------------
    # Temporal provenance
    # --------------------------------------------------------

    check(
        "Timestamp start preserved",
        item.timestamp_start == 83.5,
    )

    check(
        "Timestamp end preserved",
        item.timestamp_end == 127.9,
    )

    # --------------------------------------------------------
    # Ranking provenance
    # --------------------------------------------------------

    check(
        "RRF score preserved",
        item.rrf_score == 0.95,
    )

    check(
        "Reranker score preserved",
        item.reranker_score == 0.92,
    )

    # --------------------------------------------------------
    # Text provenance
    # --------------------------------------------------------

    check(
        "Original chunk text preserved",
        "Two Pointer is a technique"
        in item.text,
    )

    # --------------------------------------------------------
    # Final context representation
    # --------------------------------------------------------

    context_text = context.text

    check(
        "Point ID present in assembled context",
        "Point ID: provenance-001"
        in context_text,
    )

    check(
        "Video provenance present in assembled context",
        "Video ID: dyG4JBKh6tA"
        in context_text,
    )

    check(
        "Pattern provenance present in assembled context",
        "Pattern: two_pointer"
        in context_text,
    )

    check(
        "Sub-pattern provenance present in assembled context",
        "Sub-pattern: opposite_direction"
        in context_text,
    )

    check(
        "Temporal provenance present in assembled context",
        "Timestamp: 01:23 -> 02:07"
        in context_text,
    )

    check(
        "Video jump link present in assembled context",
        "https://www.youtube.com/watch?"
        "v=dyG4JBKh6tA&t=83s"
        in context_text,
    )

    # --------------------------------------------------------
    # Print assembled context for manual inspection.
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("ASSEMBLED PROVENANCE-AWARE CONTEXT")
    print("-" * 60)
    print(context_text)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_checks = 15

    print()
    print("=" * 60)
    print("PHASE 14.5 SUMMARY")
    print("=" * 60)
    print(f"Passed : {total_checks}/{total_checks}")

    print()
    print("✓ CONTEXT PROVENANCE TEST PASSED")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()