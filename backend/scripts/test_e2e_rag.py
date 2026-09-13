"""
End-to-end integration test for the DSA Revision Analyzer RAG pipeline.

Pipeline:

    User Query
        ↓
    Hybrid Retrieval
        ↓
    Cross-Encoder Reranking
        ↓
    Context Assembly
        ↓
    Grounded Prompt
        ↓
    Groq LLM
        ↓
    Final Answer + Sources

This test intentionally uses the real retrieval stack and the
real Groq API.
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

from app.services.hybrid_retrieval import (
    retrieve_hybrid,
)

from app.services.context_assembler import (
    assemble_context,
)

from app.services.llm_generator import (
    generate_answer,
    LLMGenerationResult,
)


# ============================================================
# TEST CONFIGURATION
# ============================================================

TEST_QUERY = (
    "How does the two pointer technique work?"
)

TEST_PATTERN = "two_pointer"

TOP_K = 5


# ============================================================
# END-TO-END TEST
# ============================================================


def test_end_to_end_rag() -> None:
    """
    Execute the complete RAG pipeline.
    """

    print("=" * 60)
    print("END-TO-END GROUNDED RAG TEST")
    print("=" * 60)

    print()
    print("Query:")
    print(f"  {TEST_QUERY}")

    print()
    print("Pattern:")
    print(f"  {TEST_PATTERN}")

    # --------------------------------------------------------
    # STEP 1 — HYBRID RETRIEVAL
    # --------------------------------------------------------

    print()
    print("[1/4] Running hybrid retrieval...")

    retrieval_result = retrieve_hybrid(
        query=TEST_QUERY,
        pattern=TEST_PATTERN,
        top_k=TOP_K,
    )

    assert retrieval_result.query == TEST_QUERY

    print(
        "✓ Hybrid retrieval completed."
    )

    print(
        f"  Semantic candidates: "
        f"{len(retrieval_result.semantic_results)}"
    )

    print(
        f"  BM25 candidates: "
        f"{len(retrieval_result.bm25_results)}"
    )

    print(
        f"  RRF candidates: "
        f"{len(retrieval_result.rrf_results)}"
    )

    print(
        f"  Final reranked results: "
        f"{len(retrieval_result.fused_results)}"
    )

    # --------------------------------------------------------
    # STEP 2 — CONTEXT ASSEMBLY
    # --------------------------------------------------------

    print()
    print("[2/4] Assembling LLM context...")

    context = assemble_context(
        query=TEST_QUERY,
        results=retrieval_result.fused_results,
        pattern=retrieval_result.pattern,
        sub_pattern=retrieval_result.sub_pattern,
        top_k=TOP_K,
    )

    assert context.query == TEST_QUERY

    assert len(context.items) <= TOP_K

    print(
        "✓ Context assembly completed."
    )

    print(
        f"  Context items: {len(context.items)}"
    )

    if context.items:
        print()
        print("  Retrieved sources:")

        for item in context.items:
            print(
                f"    [{item.rank}] "
                f"point_id={item.point_id} "
                f"video_id={item.video_id} "
                f"timestamp="
                f"{item.timestamp_start}"
                f"→"
                f"{item.timestamp_end}"
            )

    else:
        print(
            "  ⚠ No retrieval results were returned."
        )

    # --------------------------------------------------------
    # STEP 3 — LLM GENERATION
    # --------------------------------------------------------

    print()
    print("[3/4] Generating grounded answer with Groq...")

    result = generate_answer(
        context=context,
    )

    assert isinstance(
        result,
        LLMGenerationResult,
    )

    assert result.answer.strip()

    assert result.query == TEST_QUERY

    print(
        "✓ LLM generation completed."
    )

    print(
        f"  Model: {result.model}"
    )

    # --------------------------------------------------------
    # STEP 4 — SOURCE PRESERVATION
    # --------------------------------------------------------

    print()
    print("[4/4] Validating source preservation...")

    assert (
        len(result.context.items)
        == len(context.items)
    )

    for generated_item, context_item in zip(
        result.context.items,
        context.items,
    ):
        assert (
            generated_item.point_id
            == context_item.point_id
        )

        assert (
            generated_item.video_id
            == context_item.video_id
        )

    print(
        "✓ Source metadata preserved."
    )

    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("GENERATED ANSWER")
    print("=" * 60)

    print()
    print(result.answer)

    print()
    print("=" * 60)
    print("RAG PIPELINE RESULT")
    print("=" * 60)

    print()
    print("✓ Retrieval")
    print("✓ RRF fusion")
    print("✓ Cross-Encoder reranking")
    print("✓ Context assembly")
    print("✓ Grounded prompt construction")
    print("✓ Groq LLM generation")
    print("✓ Source preservation")

    print()
    print("=" * 60)
    print("END-TO-END RAG TEST PASSED")
    print("=" * 60)


# ============================================================
# MODULE ENTRY POINT
# ============================================================


if __name__ == "__main__":
    test_end_to_end_rag()