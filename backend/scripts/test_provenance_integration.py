"""
Phase 14.5 — Provenance Integration Test

Verifies that retrieval metadata survives the complete
retrieval-result -> Context Assembly flow.

Run from:
    backend/

Command:
    python .\scripts\test_provenance_integration.py
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
    print("PHASE 14.5 — PROVENANCE INTEGRATION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Simulated final retrieval result.
    #
    # The structure intentionally contains provenance inside
    # semantic_result.metadata, matching the retrieval output
    # consumed by Context Assembly.
    # --------------------------------------------------------

    retrieval_results = [
        {
            "point_id": "integration-point-001",

            "semantic_result": {
                "text": (
                    "Opposite-direction Two Pointer starts with "
                    "one pointer at the beginning and one pointer "
                    "at the end of the sequence."
                ),

                "metadata": {
                    "video_id": "dyG4JBKh6tA",
                    "pattern": "two_pointer",
                    "sub_pattern": "opposite_direction",
                    "timestamp_start": 83.5,
                    "timestamp_end": 127.9,
                },
            },

            "rrf_score": 0.97,
            "reranker_score": 0.94,
        },

        {
            "point_id": "integration-point-002",

            "semantic_result": {
                "text": (
                    "The two pointers move according to the "
                    "condition required by the problem."
                ),

                "metadata": {
                    "video_id": "dyG4JBKh6tA",
                    "pattern": "two_pointer",
                    "sub_pattern": "opposite_direction",
                    "timestamp_start": 146.0,
                    "timestamp_end": 170.25,
                },
            },

            "rrf_score": 0.91,
            "reranker_score": 0.88,
        },
    ]

    # --------------------------------------------------------
    # Run Context Assembly.
    # --------------------------------------------------------

    context = assemble_context(
        query="Explain opposite-direction Two Pointer",
        results=retrieval_results,
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        top_k=5,
    )

    # --------------------------------------------------------
    # Validate item count.
    # --------------------------------------------------------

    check(
        "All retrieved context items assembled",
        len(context.items) == 2,
    )

    first = context.items[0]
    second = context.items[1]

    # --------------------------------------------------------
    # First item's provenance.
    # --------------------------------------------------------

    check(
        "First point ID preserved",
        first.point_id == "integration-point-001",
    )

    check(
        "First video ID preserved",
        first.video_id == "dyG4JBKh6tA",
    )

    check(
        "First pattern preserved",
        first.pattern == "two_pointer",
    )

    check(
        "First sub-pattern preserved",
        first.sub_pattern == "opposite_direction",
    )

    check(
        "First timestamp range preserved",
        (
            first.timestamp_start == 83.5
            and first.timestamp_end == 127.9
        ),
    )

    check(
        "First ranking scores preserved",
        (
            first.rrf_score == 0.97
            and first.reranker_score == 0.94
        ),
    )

    # --------------------------------------------------------
    # Second item's provenance.
    # --------------------------------------------------------

    check(
        "Second point ID preserved",
        second.point_id == "integration-point-002",
    )

    check(
        "Second video ID preserved",
        second.video_id == "dyG4JBKh6tA",
    )

    check(
        "Second pattern preserved",
        second.pattern == "two_pointer",
    )

    check(
        "Second sub-pattern preserved",
        second.sub_pattern == "opposite_direction",
    )

    check(
        "Second timestamp range preserved",
        (
            second.timestamp_start == 146.0
            and second.timestamp_end == 170.25
        ),
    )

    check(
        "Second ranking scores preserved",
        (
            second.rrf_score == 0.91
            and second.reranker_score == 0.88
        ),
    )

    # --------------------------------------------------------
    # Validate final assembled text.
    # --------------------------------------------------------

    assembled_text = context.text

    check(
        "First point provenance present in context",
        "Point ID: integration-point-001"
        in assembled_text,
    )

    check(
        "Second point provenance present in context",
        "Point ID: integration-point-002"
        in assembled_text,
    )

    check(
        "First timestamp present in context",
        "Timestamp: 01:23 -> 02:07"
        in assembled_text,
    )

    check(
        "Second timestamp present in context",
        "Timestamp: 02:26 -> 02:50"
        in assembled_text,
    )

    check(
        "First video jump link present",
        "https://www.youtube.com/watch?"
        "v=dyG4JBKh6tA&t=83s"
        in assembled_text,
    )

    check(
        "Second video jump link present",
        "https://www.youtube.com/watch?"
        "v=dyG4JBKh6tA&t=146s"
        in assembled_text,
    )

    # --------------------------------------------------------
    # Print assembled context.
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("PROVENANCE-AWARE ASSEMBLED CONTEXT")
    print("-" * 60)
    print(assembled_text)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_checks = 20

    print()
    print("=" * 60)
    print("PHASE 14.5 INTEGRATION SUMMARY")
    print("=" * 60)
    print(f"Passed : {total_checks}/{total_checks}")

    print()
    print(
        "✓ PROVENANCE INTEGRATION TEST PASSED"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()