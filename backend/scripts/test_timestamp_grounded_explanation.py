"""
Phase 14 — Timestamp-Grounded Explanation Test

Verifies that timestamp-aware retrieval context survives the
Context Assembly -> Grounded Prompt pipeline.

Run from:
    backend/

Command:
    python .\scripts\test_timestamp_grounded_explanation.py
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
from app.services.prompt_builder import build_grounded_prompt  # noqa: E402


# ============================================================
# ASSERTION HELPER
# ============================================================

def check(name: str, condition: bool) -> None:
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
    print("PHASE 14 — TIMESTAMP-GROUNDED EXPLANATION TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Simulated retrieval result.
    #
    # This represents the output of the retrieval/reranking
    # pipeline before Context Assembly.
    # --------------------------------------------------------

    retrieval_results = [
        {
            "point_id": "grounded-001",

            "semantic_result": {
                "text": (
                    "The opposite-direction Two Pointer technique "
                    "uses one pointer at the beginning and another "
                    "pointer at the end of the array."
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
    # STEP 1 — Assemble timestamp-aware retrieval context.
    # --------------------------------------------------------

    context = assemble_context(
        query="Explain the opposite-direction Two Pointer technique",
        results=retrieval_results,
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        top_k=5,
    )

    check(
        "Context assembled",
        len(context.items) == 1,
    )

    # --------------------------------------------------------
    # STEP 2 — Build the grounded LLM prompt.
    #
    # IMPORTANT:
    # build_grounded_prompt() receives the complete
    # AssembledContext object. It does not receive query/context
    # as separate keyword arguments.
    # --------------------------------------------------------

    prompt = build_grounded_prompt(
        context=context,
    )

    check(
        "Grounded prompt created",
        prompt is not None,
    )

    user_instruction = prompt.user_instruction
    system_instruction = prompt.system_instruction

    # --------------------------------------------------------
    # USER QUERY
    # --------------------------------------------------------

    check(
        "User query present",
        "Explain the opposite-direction Two Pointer technique"
        in user_instruction,
    )

    # --------------------------------------------------------
    # TIMESTAMP EVIDENCE
    # --------------------------------------------------------

    check(
        "Timestamp range preserved",
        "01:23 -> 02:07"
        in user_instruction,
    )

    # --------------------------------------------------------
    # VIDEO PROVENANCE
    # --------------------------------------------------------

    check(
        "Video ID preserved",
        "dyG4JBKh6tA"
        in user_instruction,
    )

    check(
        "Video jump link preserved",
        "https://www.youtube.com/watch?v=dyG4JBKh6tA&t=83s"
        in user_instruction,
    )

    # --------------------------------------------------------
    # DSA PROVENANCE
    # --------------------------------------------------------

    check(
        "Pattern preserved",
        "Pattern: two_pointer"
        in user_instruction,
    )

    check(
        "Sub-pattern preserved",
        "Sub-pattern: opposite_direction"
        in user_instruction,
    )

    # --------------------------------------------------------
    # COURSE CONTENT
    # --------------------------------------------------------

    check(
        "Retrieved explanation preserved",
        "opposite-direction Two Pointer technique"
        in user_instruction,
    )

    # --------------------------------------------------------
    # EXISTING GROUNDING RULES
    # --------------------------------------------------------

    normalized_system = system_instruction.lower()
    normalized_user = user_instruction.lower()

    check(
        "Grounding instruction present",
        "only from the supplied retrieved context"
        in normalized_system,
    )

    check(
        "Outside knowledge restriction present",
        "do not use outside knowledge"
        in normalized_system,
    )

    check(
        "Hallucination prevention present",
        "do not invent"
        in normalized_system,
    )

    # --------------------------------------------------------
    # TEMPORAL GROUNDING
    #
    # These checks represent the final Phase 14 requirement.
    # They may fail initially because the current Phase 13
    # prompt rules do not yet explicitly describe timestamp-
    # grounded explanation behavior.
    # --------------------------------------------------------

    check(
        "Timestamp grounding instruction present",
        (
            "timestamp" in normalized_system
            and (
                "ground" in normalized_system
                or "evidence" in normalized_system
            )
        ),
    )

    check(
        "Video evidence instruction present",
        (
            "video" in normalized_system
            and (
                "evidence" in normalized_system
                or "timestamp" in normalized_system
            )
        ),
    )

    check(
        "Unsupported temporal claim guard present",
        (
            "unsupported" in normalized_system
            or "do not guess" in normalized_system
            or "invent" in normalized_system
        ),
    )

    # --------------------------------------------------------
    # PRINT FINAL PROMPT
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("SYSTEM INSTRUCTION")
    print("-" * 60)
    print(system_instruction)

    print()
    print("-" * 60)
    print("USER INSTRUCTION")
    print("-" * 60)
    print(user_instruction)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_checks = 14

    print()
    print("=" * 60)
    print("PHASE 14 TIMESTAMP-GROUNDED SUMMARY")
    print("=" * 60)
    print(f"Passed : {total_checks}/{total_checks}")

    print()
    print("✓ TIMESTAMP-GROUNDED EXPLANATION TEST PASSED")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()