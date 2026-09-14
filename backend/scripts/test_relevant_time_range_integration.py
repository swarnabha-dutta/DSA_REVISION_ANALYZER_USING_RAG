"""
Phase 14.3 — Relevant Time-Range Integration Test

Verifies that timestamp metadata survives the real Context Assembly
flow and can be extracted as a validated relevant time range.

Run from:
    backend/

Command:
    python .\scripts\test_relevant_time_range_integration.py
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
# IMPORTS
# ============================================================

from app.services.context_assembler import (  # noqa: E402
    _extract_relevant_time_range,
    assemble_context,
)


# ============================================================
# ASSERTION HELPER
# ============================================================

def check(
    name: str,
    condition: bool,
) -> None:
    """
    Validate one integration condition.
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
    print("PHASE 14.3 — RELEVANT TIME-RANGE INTEGRATION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Synthetic retrieval result
    #
    # This represents the type of result produced by the
    # retrieval/reranking pipeline.
    # --------------------------------------------------------

    results = [
        {
            "point_id": "test-range-001",

            "semantic_result": {
                "text": (
                    "The opposite-direction Two Pointer technique "
                    "uses one pointer at the beginning and another "
                    "at the end of the array."
                ),

                "metadata": {
                    "video_id": "dyG4JBKh6tA",
                    "pattern": "two_pointer",
                    "sub_pattern": "opposite_direction",
                    "timestamp_start": 83.5,
                    "timestamp_end": 127.9,
                },
            },

            "rrf_score": 0.91,
            "reranker_score": 0.89,
        }
    ]

    # --------------------------------------------------------
    # Run the actual Context Assembly layer.
    # --------------------------------------------------------

    context = assemble_context(
        query="Explain opposite-direction Two Pointer",
        results=results,
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        top_k=5,
    )

    # --------------------------------------------------------
    # Validate assembled item.
    # --------------------------------------------------------

    check(
        "Context item created",
        len(context.items) == 1,
    )

    item = context.items[0]

    check(
        "Timestamp start preserved",
        item.timestamp_start == 83.5,
    )

    check(
        "Timestamp end preserved",
        item.timestamp_end == 127.9,
    )

    # --------------------------------------------------------
    # Extract relevant range from the actual assembled item.
    # --------------------------------------------------------

    relevant_range = _extract_relevant_time_range(
        item.timestamp_start,
        item.timestamp_end,
    )

    expected_range = {
        "start": 83.5,
        "end": 127.9,
        "duration": 44.4,
    }

    check(
        "Relevant time range extracted",
        relevant_range == expected_range,
    )

    # --------------------------------------------------------
    # Validate range boundaries.
    # --------------------------------------------------------

    check(
        "Relevant range start is correct",
        relevant_range["start"] == 83.5,
    )

    check(
        "Relevant range end is correct",
        relevant_range["end"] == 127.9,
    )

    # --------------------------------------------------------
    # Validate duration.
    # --------------------------------------------------------

    check(
        "Relevant range duration is correct",
        relevant_range["duration"] == 44.4,
    )

    # --------------------------------------------------------
    # Validate that the same timestamps are represented in
    # the final assembled LLM context.
    # --------------------------------------------------------

    check(
        "Formatted range present in context",
        "Timestamp: 01:23 -> 02:07" in context.text,
    )

    # --------------------------------------------------------
    # Validate video jump link remains available alongside
    # the extracted range.
    # --------------------------------------------------------

    expected_jump_link = (
        "https://www.youtube.com/watch?"
        "v=dyG4JBKh6tA"
        "&t=83s"
    )

    check(
        "Video jump link preserved",
        f"Video jump link: {expected_jump_link}" in context.text,
    )

    # --------------------------------------------------------
    # Validate original chunk text.
    # --------------------------------------------------------

    check(
        "Original chunk text preserved",
        "opposite-direction Two Pointer technique"
        in context.text,
    )

    # --------------------------------------------------------
    # Print the final context.
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("ASSEMBLED CONTEXT")
    print("-" * 60)
    print(context.text)

    # --------------------------------------------------------
    # Print extracted range.
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("EXTRACTED RELEVANT TIME RANGE")
    print("-" * 60)
    print(
        f"Start    : {relevant_range['start']}"
    )
    print(
        f"End      : {relevant_range['end']}"
    )
    print(
        f"Duration : {relevant_range['duration']} seconds"
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_checks = 9

    print()
    print("=" * 60)
    print("PHASE 14.3 INTEGRATION SUMMARY")
    print("=" * 60)
    print(f"Passed : {total_checks}/{total_checks}")

    print()
    print(
        "✓ RELEVANT TIME-RANGE INTEGRATION TEST PASSED"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()