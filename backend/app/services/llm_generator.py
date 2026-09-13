"""
LLM generation layer for the DSA Revision Analyzer.

This module sends grounded prompts to Groq and returns a
structured answer.

Phase 13 responsibilities:
    - Load Groq configuration safely
    - Accept the grounded prompt from prompt_builder
    - Generate an LLM answer
    - Preserve the retrieved source context
    - Handle missing configuration
    - Handle API failures
    - Avoid mixing retrieval logic with generation logic
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from app.services.context_assembler import AssembledContext
from app.services.prompt_builder import build_grounded_prompt


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

DEFAULT_TEMPERATURE = 0.0

DEFAULT_MAX_TOKENS = 1024


# ============================================================
# RESULT MODEL
# ============================================================


@dataclass(frozen=True)
class LLMGenerationResult:
    """
    Structured result returned by the LLM generation layer.

    Attributes
    ----------
    answer:
        Generated answer from the LLM.

    query:
        Original user query.

    context:
        Original assembled retrieval context.

    model:
        Groq model used for generation.
    """

    answer: str
    query: str
    context: AssembledContext
    model: str

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result into a JSON-serializable dictionary.
        """

        return {
            "answer": self.answer,
            "query": self.query,
            "model": self.model,
            "sources": [
                {
                    "rank": item.rank,
                    "point_id": item.point_id,
                    "video_id": item.video_id,
                    "pattern": item.pattern,
                    "sub_pattern": item.sub_pattern,
                    "timestamp_start": item.timestamp_start,
                    "timestamp_end": item.timestamp_end,
                }
                for item in self.context.items
            ],
        }


# ============================================================
# CLIENT
# ============================================================


def _get_api_key() -> str:
    """
    Return the Groq API key from the environment.

    Raises
    ------
    RuntimeError
        If GROQ_API_KEY is missing.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add GROQ_API_KEY to backend/.env."
        )

    return api_key.strip()


def create_groq_client() -> Groq:
    """
    Create a Groq client using the configured API key.
    """

    return Groq(
        api_key=_get_api_key(),
    )


# ============================================================
# RESPONSE EXTRACTION
# ============================================================


def _extract_answer(response: Any) -> str:
    """
    Extract the generated text from a Groq chat-completion response.
    """

    try:
        content = response.choices[0].message.content
    except (
        AttributeError,
        IndexError,
        TypeError,
    ) as exc:
        raise RuntimeError(
            "Groq returned an unexpected response structure."
        ) from exc

    if content is None:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    answer = str(content).strip()

    if not answer:
        raise RuntimeError(
            "Groq returned an empty answer."
        )

    return answer


# ============================================================
# GENERATION
# ============================================================


def generate_answer(
    *,
    context: AssembledContext,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> LLMGenerationResult:
    """
    Generate a grounded answer from assembled retrieval context.

    Parameters
    ----------
    context:
        Structured retrieval context produced by Phase 12.

    model:
        Groq model identifier.

    temperature:
        Sampling temperature.

    max_tokens:
        Maximum number of generated tokens.

    Returns
    -------
    LLMGenerationResult
        Generated answer plus original query and source metadata.

    Notes
    -----
    This function does NOT perform retrieval.

    Retrieval and context construction remain owned by the
    previous pipeline stages.
    """

    if not isinstance(context, AssembledContext):
        raise TypeError(
            "context must be an AssembledContext instance."
        )

    if not model or not model.strip():
        raise ValueError(
            "model cannot be empty."
        )

    if temperature < 0:
        raise ValueError(
            "temperature cannot be negative."
        )

    if max_tokens <= 0:
        raise ValueError(
            "max_tokens must be greater than zero."
        )

    prompt = build_grounded_prompt(
        context=context,
    )

    client = create_groq_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=prompt.messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    except Exception as exc:
        raise RuntimeError(
            "Groq LLM generation failed."
        ) from exc

    answer = _extract_answer(response)

    return LLMGenerationResult(
        answer=answer,
        query=context.query,
        context=context,
        model=model,
    )


# ============================================================
# SELF CHECK
# ============================================================


def self_check() -> None:
    """
    Lightweight module self-check.

    This does NOT make a real Groq API request.
    """

    print("=" * 60)
    print("LLM GENERATOR SELF-CHECK")
    print("=" * 60)

    print(f"✓ Default model: {DEFAULT_MODEL}")
    print(f"✓ Default temperature: {DEFAULT_TEMPERATURE}")
    print(f"✓ Default max tokens: {DEFAULT_MAX_TOKENS}")
    print("✓ Groq client factory available.")
    print("✓ Response extraction available.")
    print("✓ Grounded answer generation available.")
    print()

    if os.getenv("GROQ_API_KEY"):
        print("✓ GROQ_API_KEY detected.")
    else:
        print("⚠ GROQ_API_KEY not detected.")

    print()
    print("✓ LLM generator self-check passed.")


# ============================================================
# MODULE ENTRY POINT
# ============================================================


if __name__ == "__main__":
    self_check()