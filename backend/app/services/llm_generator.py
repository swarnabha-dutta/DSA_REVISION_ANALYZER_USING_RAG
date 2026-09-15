"""
LLM generation layer for the DSA Revision Analyzer.

This module sends grounded prompts to Groq and returns a
structured answer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from app.services.context_assembler import AssembledContext
from app.services.prompt_builder import build_grounded_prompt
from app.services.language_detection import (
    detect_query_language,
    response_language_for,
)


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
    Structured result returned by LLM generation.
    """

    answer: str
    query: str
    context: AssembledContext
    model: str
    query_language: str
    response_language: str

    def to_dict(self) -> dict[str, Any]:
        """
        Convert result to JSON-serializable dictionary.
        """

        return {
            "answer": self.answer,
            "query": self.query,
            "model": self.model,
            "query_language": self.query_language,
            "response_language": self.response_language,
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
# GROQ CLIENT
# ============================================================

def _get_api_key() -> str:
    """
    Return Groq API key from environment.
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
    Create Groq client.
    """

    return Groq(
        api_key=_get_api_key(),
    )


# ============================================================
# RESPONSE EXTRACTION
# ============================================================

def _extract_answer(response: Any) -> str:
    """
    Extract generated text from Groq response.
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
    response_language: str | None = None,
) -> LLMGenerationResult:
    """
    Generate grounded answer from assembled retrieval context.
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

    # --------------------------------------------------------
    # Detect query language
    # --------------------------------------------------------

    query_language = detect_query_language(
        context.query
    ).value

    # --------------------------------------------------------
    # Determine response language
    # --------------------------------------------------------

    if response_language is None:
        response_language = response_language_for(
            context.query
        )

    response_language = response_language.strip()

    if not response_language:
        raise ValueError(
            "response_language cannot be empty."
        )

    # --------------------------------------------------------
    # Build grounded prompt
    # --------------------------------------------------------

    prompt = build_grounded_prompt(
        context=context,
        response_language=response_language,
    )

    # --------------------------------------------------------
    # Groq
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Extract answer
    # --------------------------------------------------------

    answer = _extract_answer(response)

    return LLMGenerationResult(
        answer=answer,
        query=context.query,
        context=context,
        model=model,
        query_language=query_language,
        response_language=response_language,
    )


# ============================================================
# SELF CHECK
# ============================================================

def self_check() -> None:
    """
    Lightweight self-check.
    """

    print("=" * 60)
    print("LLM GENERATOR SELF-CHECK")
    print("=" * 60)

    print(
        f"✓ Default model: {DEFAULT_MODEL}"
    )

    print(
        f"✓ Default temperature: {DEFAULT_TEMPERATURE}"
    )

    print(
        f"✓ Default max tokens: {DEFAULT_MAX_TOKENS}"
    )

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


if __name__ == "__main__":
    self_check()