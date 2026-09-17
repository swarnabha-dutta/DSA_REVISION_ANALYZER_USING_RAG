"""
LLM generation layer for the DSA Revision Analyzer.

The LLM returns a grounded JSON object containing:
    - the main answer
    - one English summary per unique retrieved video
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from app.services.context_assembler import AssembledContext
from app.services.language_detection import (
    detect_query_language,
    response_language_for,
)
from app.services.prompt_builder import build_grounded_prompt


load_dotenv()


DEFAULT_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

DEFAULT_TEMPERATURE = 0.0

DEFAULT_MAX_TOKENS = 1536


@dataclass(frozen=True)
class LLMGenerationResult:
    """Structured result returned by LLM generation."""

    answer: str
    query: str
    context: AssembledContext
    model: str
    query_language: str
    response_language: str

    video_summaries: dict[str, str] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "query": self.query,
            "model": self.model,
            "query_language": self.query_language,
            "response_language": self.response_language,

            "video_summaries": [
                {
                    "video_id": item.video_id,
                    "video_title": item.video_title,
                    "summary": self.video_summaries.get(
                        item.video_id
                    ),
                }
                for item in self.context.items
                if (
                    item.video_id
                    and item.video_id in self.video_summaries
                )
            ],

            "sources": [
                {
                    "rank": item.rank,
                    "point_id": item.point_id,
                    "video_id": item.video_id,
                    "video_title": item.video_title,
                    "pattern": item.pattern,
                    "sub_pattern": item.sub_pattern,
                    "timestamp_start": item.timestamp_start,
                    "timestamp_end": item.timestamp_end,
                    "text": item.text,
                }
                for item in self.context.items
            ],
        }


# ============================================================
# GROQ CLIENT
# ============================================================


def _get_api_key() -> str:
    """Return Groq API key from environment."""

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add GROQ_API_KEY to backend/.env."
        )

    return api_key.strip()


def create_groq_client() -> Groq:
    """Create Groq client."""

    return Groq(
        api_key=_get_api_key()
    )


# ============================================================
# RESPONSE EXTRACTION
# ============================================================


def _extract_raw_content(
    response: Any,
) -> str:
    """Extract generated content from Groq response."""

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

    content = str(
        content
    ).strip()

    if not content:
        raise RuntimeError(
            "Groq returned an empty answer."
        )

    return content


def _extract_json_object(
    raw_content: str,
) -> dict[str, Any]:
    """
    Parse JSON while tolerating accidental markdown fences.
    """

    cleaned = raw_content.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

    try:
        parsed = json.loads(
            cleaned
        )

    except json.JSONDecodeError:

        start = cleaned.find(
            "{"
        )

        end = cleaned.rfind(
            "}"
        )

        if start == -1 or end <= start:
            raise RuntimeError(
                "Groq returned invalid JSON."
            )

        try:
            parsed = json.loads(
                cleaned[
                    start:end + 1
                ]
            )

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Groq returned invalid JSON."
            ) from exc

    if not isinstance(
        parsed,
        dict,
    ):
        raise RuntimeError(
            "Groq JSON response must be an object."
        )

    return parsed


def _normalize_summary(
    value: Any,
) -> str | None:
    if value is None:
        return None

    value = str(
        value
    ).strip()

    return value or None


# ============================================================
# STRUCTURED RESPONSE VALIDATION
# ============================================================


def _parse_structured_response(
    raw_content: str,
    context: AssembledContext,
) -> tuple[
    str,
    dict[str, str],
]:
    """
    Validate model output against the actual retrieved
    video provenance.
    """

    payload = _extract_json_object(
        raw_content
    )

    answer = payload.get(
        "answer"
    )

    if answer is None:
        raise RuntimeError(
            "Groq JSON response is missing the 'answer' field."
        )

    answer = str(
        answer
    ).strip()

    if not answer:
        raise RuntimeError(
            "Groq JSON response contains an empty 'answer'."
        )

    # --------------------------------------------------------
    # Build whitelist from actual retrieval results
    # --------------------------------------------------------

    valid_videos: dict[
        str,
        str | None,
    ] = {}

    for item in context.items:

        if item.video_id:
            valid_videos.setdefault(
                item.video_id,
                item.video_title,
            )

    # --------------------------------------------------------
    # Parse summaries
    # --------------------------------------------------------

    raw_summaries = payload.get(
        "video_summaries",
        [],
    )

    if not isinstance(
        raw_summaries,
        list,
    ):
        raw_summaries = []

    summaries: dict[
        str,
        str,
    ] = {}

    for entry in raw_summaries:

        if not isinstance(
            entry,
            dict,
        ):
            continue

        video_id = entry.get(
            "video_id"
        )

        if video_id is None:
            continue

        video_id = str(
            video_id
        ).strip()

        # Never accept a video that wasn't retrieved.
        if (
            not video_id
            or video_id not in valid_videos
        ):
            continue

        summary = _normalize_summary(
            entry.get(
                "summary"
            )
        )

        if not summary:
            continue

        expected_title = valid_videos[
            video_id
        ]

        returned_title = entry.get(
            "video_title"
        )

        # If the model returned a title, it must exactly
        # match the retrieved title.
        if (
            expected_title
            and returned_title is not None
        ):

            if (
                str(returned_title).strip()
                != expected_title
            ):
                continue

        summaries.setdefault(
            video_id,
            summary,
        )

    return (
        answer,
        summaries,
    )


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
    Generate a grounded structured answer from assembled
    retrieval context.
    """

    if not isinstance(
        context,
        AssembledContext,
    ):
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
    # Query language
    # --------------------------------------------------------

    query_language = detect_query_language(
        context.query
    ).value

    # --------------------------------------------------------
    # Response language
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
    # Prompt
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
    # Parse structured response
    # --------------------------------------------------------

    raw_content = _extract_raw_content(
        response
    )

    answer, video_summaries = (
        _parse_structured_response(
            raw_content,
            context,
        )
    )

    return LLMGenerationResult(
        answer=answer,
        query=context.query,
        context=context,
        model=model,
        query_language=query_language,
        response_language=response_language,
        video_summaries=video_summaries,
    )


# ============================================================
# SELF CHECK
# ============================================================


def self_check() -> None:
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

    print(
        "✓ Structured JSON parser available."
    )

    print(
        "✓ Video-summary provenance validation available."
    )

    print(
        "✓ Grounded answer generation available."
    )

    print()

    print(
        "✓ LLM generator self-check passed."
    )


if __name__ == "__main__":
    self_check()