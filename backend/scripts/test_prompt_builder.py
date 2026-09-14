"""
Integration tests for the Phase 13 grounded prompt builder.

Tests:
    - Prompt construction from AssembledContext
    - Query preservation
    - Retrieved context preservation
    - Metadata preservation inside context
    - Empty retrieval handling
    - Grounding instructions
    - Chat-completion message structure
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

# Add the backend project root to Python's import path.
BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


# ============================================================
# IMPORTS
# ============================================================

from app.services.context_assembler import (
    AssembledContext,
    ContextItem,
)

from app.services.prompt_builder import (
    build_grounded_prompt,
    build_prompt,
)


# ============================================================
# TEST DATA
# ============================================================


def build_sample_context() -> AssembledContext:
    """
    Build deterministic fake retrieval context.

    No Qdrant, BM25, RRF, or Cross-Encoder is required here.
    """

    item_1 = ContextItem(
        rank=1,
        point_id="point-001",
        text=(
            "Two pointers use two indices to process "
            "an array efficiently."
        ),
        video_id="video-001",
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        timestamp_start=120.5,
        timestamp_end=145.75,
        rrf_score=0.032,
        reranker_score=0.91,
    )

    item_2 = ContextItem(
        rank=2,
        point_id="point-002",
        text=(
            "The left pointer starts from the beginning "
            "while the right pointer starts from the end."
        ),
        video_id="video-001",
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        timestamp_start=146.0,
        timestamp_end=170.25,
        rrf_score=0.029,
        reranker_score=0.87,
    )

    return AssembledContext(
        query="How does the two pointer technique work?",
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        items=[
            item_1,
            item_2,
        ],
    )


# ============================================================
# TEST 1
# ============================================================


def test_prompt_contains_query() -> None:
    """
    The original user query must appear in the prompt.
    """

    context = build_sample_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    assert context.query in prompt.user_instruction

    print("✓ User query preserved.")


# ============================================================
# TEST 2
# ============================================================


def test_prompt_contains_retrieved_context() -> None:
    """
    Retrieved chunk text must appear in the prompt.
    """

    context = build_sample_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    for item in context.items:
        assert item.text in prompt.user_instruction

    print("✓ Retrieved context preserved.")


# ============================================================
# TEST 3
# ============================================================


def test_metadata_survives_in_context() -> None:
    """
    Important retrieval metadata should remain available
    inside the serialized context.
    """

    context = build_sample_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    assert "point-001" in prompt.user_instruction
    assert "video-001" in prompt.user_instruction
    assert "two_pointer" in prompt.user_instruction
    assert "opposite_direction" in prompt.user_instruction
    assert "02:00 -> 02:25" in prompt.user_instruction
    assert "02:26 -> 02:50" in prompt.user_instruction

    print("✓ Retrieval metadata preserved.")


# ============================================================
# TEST 4
# ============================================================


def test_grounding_instruction_exists() -> None:
    """
    The system prompt must explicitly enforce grounding.
    """

    context = build_sample_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    system_prompt = prompt.system_instruction

    assert "ONLY from the supplied retrieved context" in (
        system_prompt
    )

    assert "Do NOT use outside knowledge" in (
        system_prompt
    )

    assert "Do NOT invent" in system_prompt

    print("✓ Grounding instructions present.")


# ============================================================
# TEST 5
# ============================================================


def test_insufficient_context_instruction_exists() -> None:
    """
    The prompt must tell the LLM not to guess when context
    is insufficient.
    """

    context = build_sample_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    system_prompt = prompt.system_instruction.lower()
    user_prompt = prompt.user_instruction.lower()

    assert (
        "enough information" in system_prompt
    )

    assert (
        "do not guess" in user_prompt
    )

    print("✓ Insufficient-context guard present.")

# ============================================================
# TEST 6
# ============================================================


def test_chat_messages_structure() -> None:
    """
    Chat-completion messages must contain:
        1. system message
        2. user message
    """

    context = build_sample_context()

    messages = build_prompt(
        context=context,
    )

    assert len(messages) == 2

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    assert messages[0]["content"]
    assert messages[1]["content"]

    print("✓ Chat message structure valid.")


# ============================================================
# TEST 7
# ============================================================


def test_empty_context_is_handled() -> None:
    """
    Empty retrieval results must still produce a valid prompt.
    """

    context = AssembledContext(
        query="What is binary search?",
        pattern="binary_search",
        sub_pattern=None,
        items=[],
    )

    prompt = build_grounded_prompt(
        context=context,
    )

    assert (
        "[NO RETRIEVED COURSE CONTEXT AVAILABLE]"
        in prompt.user_instruction
    )

    assert "do not guess" in (
        prompt.user_instruction.lower()
    )

    print("✓ Empty retrieval context handled safely.")


# ============================================================
# TEST RUNNER
# ============================================================


def main() -> None:
    """
    Run all prompt-builder tests.
    """

    print("=" * 60)
    print("PROMPT BUILDER INTEGRATION TEST")
    print("=" * 60)
    print()

    tests = [
        test_prompt_contains_query,
        test_prompt_contains_retrieved_context,
        test_metadata_survives_in_context,
        test_grounding_instruction_exists,
        test_insufficient_context_instruction_exists,
        test_chat_messages_structure,
        test_empty_context_is_handled,
    ]

    passed = 0

    for test in tests:
        test()
        passed += 1

    print()
    print("=" * 60)
    print(f"RESULT: {passed}/{len(tests)} TESTS PASSED")
    print("=" * 60)


# ============================================================
# MODULE ENTRY POINT
# ============================================================


if __name__ == "__main__":
    main()