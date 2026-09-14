"""
Phase 14.4 — Prompt / Context Integration Test

Verifies that the structured context produced by Context Assembly
is correctly incorporated into the final grounded prompt.

Run from:
    backend/

Command:
    python .\scripts\test_prompt_context_integration.py
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

from app.services.context_assembler import assemble_context  # noqa: E402
from app.services.prompt_builder import build_prompt  # noqa: E402


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
    print("PHASE 14.4 — PROMPT / CONTEXT INTEGRATION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Synthetic retrieval result.
    #
    # This mimics the final result entering Context Assembly.
    # --------------------------------------------------------

    results = [
        {
            "point_id": "test-prompt-001",

            "semantic_result": {
                "text": (
                    "Two Pointer uses two indices that move through "
                    "a sequence while maintaining a problem-specific "
                    "invariant."
                ),

                "metadata": {
                    "video_id": "dyG4JBKh6tA",
                    "pattern": "two_pointer",
                    "sub_pattern": "opposite_direction",
                    "timestamp_start": 83.5,
                    "timestamp_end": 127.9,
                },
            },

            "rrf_score": 0.93,
            "reranker_score": 0.90,
        }
    ]

    # --------------------------------------------------------
    # Step 1 — Assemble retrieval context.
    # --------------------------------------------------------

    context = assemble_context(
        query="Explain the Two Pointer technique",
        results=results,
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        top_k=5,
    )

    check(
        "Context assembled",
        len(context.items) == 1,
    )

    # --------------------------------------------------------
    # Step 2 — Build the grounded prompt.
    #
    # NOTE:
    # Use the actual prompt_builder interface from the project.
    # --------------------------------------------------------

    prompt_messages = build_prompt(
        context=context,
    )

    prompt = "\n".join(
        message["content"]
        for message in prompt_messages
    )

    # --------------------------------------------------------
    # Step 3 — Validate query presence.
    # --------------------------------------------------------

    check(
        "User query present in prompt",
        "Explain the Two Pointer technique" in prompt,
    )

    # --------------------------------------------------------
    # Step 4 — Validate retrieved chunk text.
    # --------------------------------------------------------

    check(
        "Retrieved chunk present in prompt",
        "Two Pointer uses two indices" in prompt,
    )

    # --------------------------------------------------------
    # Step 5 — Validate video metadata.
    # --------------------------------------------------------

    check(
        "Video ID present in prompt",
        "dyG4JBKh6tA" in prompt,
    )

    # --------------------------------------------------------
    # Step 6 — Validate timestamp range.
    # --------------------------------------------------------

    check(
        "Timestamp range present in prompt",
        "Timestamp: 01:23 -> 02:07" in prompt,
    )

    # --------------------------------------------------------
    # Step 7 — Validate YouTube jump link.
    # --------------------------------------------------------

    expected_jump_link = (
        "https://www.youtube.com/watch?"
        "v=dyG4JBKh6tA"
        "&t=83s"
    )

    check(
        "Video jump link present in prompt",
        expected_jump_link in prompt,
    )

    # --------------------------------------------------------
    # Step 8 — Validate pattern metadata.
    # --------------------------------------------------------

    check(
        "Pattern present in prompt",
        "two_pointer" in prompt,
    )

    # --------------------------------------------------------
    # Step 9 — Validate sub-pattern metadata.
    # --------------------------------------------------------

    check(
        "Sub-pattern present in prompt",
        "opposite_direction" in prompt,
    )

    # --------------------------------------------------------
    # Print final prompt for manual inspection.
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("FINAL GROUNDED PROMPT")
    print("-" * 60)
    print(prompt)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_checks = 9

    print()
    print("=" * 60)
    print("PHASE 14.4 INTEGRATION SUMMARY")
    print("=" * 60)
    print(f"Passed : {total_checks}/{total_checks}")

    print()
    print(
        "✓ PROMPT / CONTEXT INTEGRATION TEST PASSED"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()