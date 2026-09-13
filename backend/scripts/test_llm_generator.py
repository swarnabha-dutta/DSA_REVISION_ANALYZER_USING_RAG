"""
Integration test for the Phase 13.2 LLM generator.

This test performs a real Groq API request.

Pipeline tested:
    AssembledContext
        ↓
    Grounded Prompt Builder
        ↓
    Groq LLM
        ↓
    LLMGenerationResult
        ↓
    Source metadata preservation
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

from app.services.llm_generator import (
    LLMGenerationResult,
    generate_answer,
)


# ============================================================
# TEST DATA
# ============================================================


def build_sample_context() -> AssembledContext:
    """
    Build deterministic retrieval context for the test.

    This deliberately uses fake retrieved chunks so that the test
    isolates the LLM generation layer.
    """

    item_1 = ContextItem(
        rank=1,
        point_id="test-point-001",
        text=(
            "Two pointers use two indices to process an array "
            "efficiently. In the opposite-direction approach, "
            "one pointer starts from the left and another starts "
            "from the right."
        ),
        video_id="test-video-001",
        pattern="two_pointer",
        sub_pattern="opposite_direction",
        timestamp_start=120.5,
        timestamp_end=145.75,
        rrf_score=0.032,
        reranker_score=0.91,
    )

    item_2 = ContextItem(
        rank=2,
        point_id="test-point-002",
        text=(
            "The left pointer moves forward and the right pointer "
            "moves backward according to the conditions of the "
            "algorithm."
        ),
        video_id="test-video-001",
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


def test_generation_returns_result() -> None:
    """
    Verify that a real Groq request returns a structured result.
    """

    context = build_sample_context()

    result = generate_answer(
        context=context,
    )

    assert isinstance(
        result,
        LLMGenerationResult,
    )

    print("✓ LLM generation returned a structured result.")


# ============================================================
# TEST 2
# ============================================================


def test_answer_is_non_empty() -> None:
    """
    Verify that the LLM returned a non-empty answer.
    """

    context = build_sample_context()

    result = generate_answer(
        context=context,
    )

    assert isinstance(result.answer, str)
    assert result.answer.strip()

    print("✓ Generated answer is non-empty.")


# ============================================================
# TEST 3
# ============================================================


def test_query_is_preserved() -> None:
    """
    Verify that the original query survives generation.
    """

    context = build_sample_context()

    result = generate_answer(
        context=context,
    )

    assert result.query == context.query

    print("✓ Original query preserved.")


# ============================================================
# TEST 4
# ============================================================


def test_model_is_preserved() -> None:
    """
    Verify that the model identifier is stored in the result.
    """

    context = build_sample_context()

    result = generate_answer(
        context=context,
    )

    assert result.model
    assert isinstance(result.model, str)

    print(f"✓ Model recorded: {result.model}")


# ============================================================
# TEST 5
# ============================================================


def test_sources_are_preserved() -> None:
    """
    Verify that retrieved source metadata remains available
    after LLM generation.
    """

    context = build_sample_context()

    result = generate_answer(
        context=context,
    )

    assert len(result.context.items) == 2

    assert (
        result.context.items[0].point_id
        == "test-point-001"
    )

    assert (
        result.context.items[0].video_id
        == "test-video-001"
    )

    assert (
        result.context.items[0].timestamp_start
        == 120.5
    )

    assert (
        result.context.items[0].timestamp_end
        == 145.75
    )

    print("✓ Retrieved source metadata preserved.")


# ============================================================
# TEST 6
# ============================================================


def test_result_is_serializable() -> None:
    """
    Verify that the generation result can be converted into
    an API-friendly dictionary.
    """

    context = build_sample_context()

    result = generate_answer(
        context=context,
    )

    data = result.to_dict()

    assert isinstance(data, dict)

    assert "answer" in data
    assert "query" in data
    assert "model" in data
    assert "sources" in data

    assert len(data["sources"]) == 2

    print("✓ Generation result is API-serializable.")


# ============================================================
# TEST RUNNER
# ============================================================


def main() -> None:
    """
    Run all LLM generator integration tests.
    """

    print("=" * 60)
    print("LLM GENERATOR INTEGRATION TEST")
    print("=" * 60)
    print()

    tests = [
        test_generation_returns_result,
        test_answer_is_non_empty,
        test_query_is_preserved,
        test_model_is_preserved,
        test_sources_are_preserved,
        test_result_is_serializable,
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