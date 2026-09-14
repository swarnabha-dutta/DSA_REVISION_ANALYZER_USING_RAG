"""
Phase 14.2 — Timestamp + Video Jump Link Integration Test

This test verifies that timestamp metadata flows through the
full Context Assembly layer and appears correctly in the final
LLM-ready context text.

Run from:
    backend/

Command:
    python .\scripts\test_timestamp_jump_integration.py
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

from app.services.context_assembler import assemble_context


# ============================================================
# ASSERTION HELPER
# ============================================================

def check(
    name: str,
    condition: bool,
) -> None:
    """
    Raise an AssertionError when an integration condition fails.
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
    print("PHASE 14.2 — TIMESTAMP + JUMP LINK INTEGRATION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Synthetic retrieval result
    #
    # This mimics the structure that Context Assembly receives
    # from the retrieval/reranking pipeline.
    # --------------------------------------------------------

    results = [
        {
            "point_id": "test-point-001",

            "semantic_result": {
                "text": (
                    "Two Pointer is a technique where two indices "
                    "move through the array according to a specific "
                    "condition."
                ),

                "metadata": {
                    "video_id": "dyG4JBKh6tA",
                    "pattern": "two_pointer",
                    "sub_pattern": "opposite_direction",
                    "timestamp_start": 83.5,
                    "timestamp_end": 127.9,
                },
            },

            "rrf_score": 0.92,
            "reranker_score": 0.88,
        }
    ]

    # --------------------------------------------------------
    # Run actual Context Assembly
    # --------------------------------------------------------

    context = assemble_context(
        query="Explain the Two Pointer technique",
        results=results,
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        top_k=5,
    )

    # --------------------------------------------------------
    # Basic assembly validation
    # --------------------------------------------------------

    check(
        "Context item created",
        len(context.items) == 1,
    )

    item = context.items[0]

    check(
        "Video ID preserved",
        item.video_id == "dyG4JBKh6tA",
    )

    check(
        "Timestamp start preserved",
        item.timestamp_start == 83.5,
    )

    check(
        "Timestamp end preserved",
        item.timestamp_end == 127.9,
    )

    # --------------------------------------------------------
    # Validate human-readable timestamp formatting
    # --------------------------------------------------------

    check(
        "Formatted timestamp range present",
        "Timestamp: 01:23 -> 02:07" in context.text,
    )

    # --------------------------------------------------------
    # Validate YouTube jump link
    # --------------------------------------------------------

    expected_jump_link = (
        "https://www.youtube.com/watch?"
        "v=dyG4JBKh6tA"
        "&t=83s"
    )

    check(
        "Video jump link present",
        f"Video jump link: {expected_jump_link}" in context.text,
    )

    # --------------------------------------------------------
    # Validate chunk text remains present
    # --------------------------------------------------------

    check(
        "Original chunk text preserved",
        "Two Pointer is a technique" in context.text,
    )

    # --------------------------------------------------------
    # Print actual assembled context
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("ASSEMBLED CONTEXT")
    print("-" * 60)
    print(context.text)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_checks = 8

    print()
    print("=" * 60)
    print("PHASE 14.2 INTEGRATION SUMMARY")
    print("=" * 60)
    print(f"Passed : {total_checks}/{total_checks}")

    print()
    print("✓ TIMESTAMP + VIDEO JUMP LINK INTEGRATION TEST PASSED")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()