"""
Grounding quality and hallucination-resistance tests for Phase 13.4.

Tests:

    1. Explicit grounding restrictions
    2. Empty-context safety
    3. Retrieved evidence visibility
    4. Source metadata visibility
    5. Structured retrieval context
    6. Query + evidence preservation
    7. Explicit empty-retrieval representation
    8. Adversarial unsupported-query behavior

The first seven tests are deterministic.

The final test performs a real Groq API request and checks whether
the model refuses to invent an answer when the supplied course
context does not contain the requested information.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

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
)

from app.services.llm_generator import (
    generate_answer,
)


# ============================================================
# TEST DATA
# ============================================================


def build_grounded_context() -> AssembledContext:
    """
    Build a small deterministic retrieval context.

    The context contains only basic information about the
    two-pointer technique.
    """

    item = ContextItem(
        rank=1,
        point_id="grounding-point-001",
        text=(
            "Two pointers use two indices. One pointer can start "
            "from the left and another can start from the right. "
            "The pointers move according to the comparison."
        ),
        video_id="grounding-video-001",
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        timestamp_start=100.0,
        timestamp_end=130.0,
        rrf_score=0.03,
        reranker_score=0.90,
    )

    return AssembledContext(
        query="How does the two pointer technique work?",
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        items=[item],
    )


# ============================================================
# TEST 1
# ============================================================


def test_grounding_instruction_is_explicit() -> None:
    """
    The system instruction must explicitly restrict the model
    to the supplied retrieval context.
    """

    context = build_grounded_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    system_prompt = prompt.system_instruction.lower()

    assert (
        "only from the supplied retrieved context"
        in system_prompt
    )

    assert (
        "do not use outside knowledge"
        in system_prompt
    )

    assert "do not invent" in system_prompt

    print("✓ Explicit grounding restrictions present.")


# ============================================================
# TEST 2
# ============================================================


def test_insufficient_context_has_safe_behavior() -> None:
    """
    When retrieval returns nothing, the prompt must instruct
    the model not to guess.
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

    user_prompt = prompt.user_instruction.lower()

    assert (
        "[no retrieved course context available]"
        in user_prompt
    )

    assert "do not guess" in user_prompt

    print("✓ Empty-context safety guard present.")


# ============================================================
# TEST 3
# ============================================================


def test_retrieved_text_is_visible_to_grounding_layer() -> None:
    """
    The exact retrieved text must be present in the user
    instruction sent to the LLM.
    """

    context = build_grounded_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    assert (
        context.items[0].text
        in prompt.user_instruction
    )

    print("✓ Retrieved evidence is visible to the LLM.")


# ============================================================
# TEST 4
# ============================================================


def test_source_metadata_is_visible() -> None:
    """
    Source metadata must survive prompt construction so that
    later answer/source formatting can use it.
    """

    context = build_grounded_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    user_prompt = prompt.user_instruction

    assert "grounding-point-001" in user_prompt
    assert "grounding-video-001" in user_prompt
    assert "two_pointer" in user_prompt
    assert "opposite_direction" in user_prompt
    assert "100.00s" in user_prompt
    assert "130.00s" in user_prompt

    print(
        "✓ Source metadata is available to the grounding layer."
    )


# ============================================================
# TEST 5
# ============================================================


def test_prompt_has_single_grounding_context() -> None:
    """
    The prompt should expose one explicit retrieved-context
    section rather than hiding evidence across unrelated fields.
    """

    context = build_grounded_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    user_prompt = prompt.user_instruction

    assert "RETRIEVED COURSE CONTEXT" in user_prompt

    assert (
        user_prompt.count("grounding-point-001")
        >= 1
    )

    print("✓ Retrieved context is explicitly structured.")


# ============================================================
# TEST 6
# ============================================================


def test_query_and_context_are_both_present() -> None:
    """
    Grounding requires both:

        - the original question
        - the evidence used to answer it
    """

    context = build_grounded_context()

    prompt = build_grounded_prompt(
        context=context,
    )

    assert context.query in prompt.user_instruction

    assert (
        context.items[0].text
        in prompt.user_instruction
    )

    print("✓ Query and evidence are jointly available.")


# ============================================================
# TEST 7
# ============================================================


def test_no_context_cannot_be_silently_treated_as_evidence() -> None:
    """
    An empty retrieval result must be represented explicitly,
    rather than producing an empty context block that could be
    mistaken for missing-but-valid evidence.
    """

    context = AssembledContext(
        query="Explain a completely unknown topic.",
        pattern="unknown",
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

    print("✓ Empty retrieval is explicitly represented.")


# ============================================================
# TEST 8 — ADVERSARIAL GROUNDING TEST
# ============================================================


def test_adversarial_unsupported_query() -> None:
    """
    Perform a real Groq request with intentionally insufficient
    retrieval evidence.

    The supplied context talks only about how two pointers work.

    The query asks for the exact historical origin of the
    technique.

    The model should NOT invent a historical answer from its
    general knowledge.

    This test therefore checks for a clear insufficiency/refusal
    signal in the generated answer.
    """

    context = AssembledContext(
        query=(
            "What is the exact historical origin of the "
            "two pointer technique, including who invented it "
            "and the year it was first introduced?"
        ),
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        items=[
            ContextItem(
                rank=1,
                point_id="adversarial-point-001",
                text=(
                    "Two pointers use two indices. One pointer "
                    "can start from the left and another can start "
                    "from the right. The pointers move according "
                    "to the comparison."
                ),
                video_id="adversarial-video-001",
                pattern="two_pointer",
                sub_pattern="opposite_direction",
                timestamp_start=100.0,
                timestamp_end=130.0,
                rrf_score=0.03,
                reranker_score=0.90,
            )
        ],
    )

    print()
    print(
        "  Sending adversarial unsupported query to Groq..."
    )

    result = generate_answer(
        context=context,
    )

    answer = result.answer.strip()

    assert answer

    print()
    print("  Model response:")
    print("  " + answer.replace("\n", "\n  "))

    # --------------------------------------------------------
    # Look for explicit insufficiency/refusal signals.
    #
    # We intentionally accept several reasonable phrasings.
    # The model does not need to use one exact sentence.
    # --------------------------------------------------------

    answer_lower = answer.lower()

    refusal_signals = [
    "not enough information",
    "insufficient information",
    "does not provide",
    "doesn't provide",
    "does not contain",
    "doesn't contain",
    "not provided",
    "cannot determine",
    "can't determine",
    "cannot answer",
    "can't answer",
    "cannot be determined",
    "not mentioned",
    "not stated",
    "no information",
    "not available",
    "i don't have enough",
    "i do not have enough",
    "outside the provided context",
    "outside the supplied context",
    "not contained in the provided context",
    "not contained in the supplied context",
]

    grounded_refusal_detected = any(
        signal in answer_lower
        for signal in refusal_signals
    )

    assert grounded_refusal_detected, (
        "The adversarial query did not produce an explicit "
        "insufficiency/refusal signal. The model may have "
        "answered using information outside the supplied "
        "retrieval context.\n\n"
        f"Generated answer:\n{answer}"
    )

    print(
        "✓ Unsupported query triggered a grounded refusal."
    )


# ============================================================
# TEST RUNNER
# ============================================================


def main() -> None:
    """
    Run all grounding-quality tests.
    """

    print("=" * 60)
    print("GROUNDING QUALITY TEST")
    print("=" * 60)
    print()

    deterministic_tests = [
        test_grounding_instruction_is_explicit,
        test_insufficient_context_has_safe_behavior,
        test_retrieved_text_is_visible_to_grounding_layer,
        test_source_metadata_is_visible,
        test_prompt_has_single_grounding_context,
        test_query_and_context_are_both_present,
        test_no_context_cannot_be_silently_treated_as_evidence,
    ]

    passed = 0

    # --------------------------------------------------------
    # Deterministic tests
    # --------------------------------------------------------

    for test in deterministic_tests:
        test()
        passed += 1

    # --------------------------------------------------------
    # Real LLM adversarial test
    # --------------------------------------------------------

    test_adversarial_unsupported_query()
    passed += 1

    print()
    print("=" * 60)
    print(
        f"RESULT: {passed}/{len(deterministic_tests) + 1} "
        "TESTS PASSED"
    )
    print("=" * 60)


# ============================================================
# MODULE ENTRY POINT
# ============================================================


if __name__ == "__main__":
    main()