"""
Transcript Translation Utility

This script:

1. Loads a transcript JSON from data/transcripts/.
2. Reads the original Hindi/Hinglish transcript segments.
3. Preserves source video metadata.
4. Sends transcript segments to Groq in small batches.
5. Translates Hindi/Hinglish into clear technical English.
6. Preserves timestamps and original segment IDs.
7. Validates every LLM response.
8. Retries temporary translation failures.
9. Saves progress after every successful batch.
10. Resumes automatically from an existing partial translation.
11. Saves the final translated transcript under data/translated/.

Example:

    python .\scripts\translate_transcript.py "dyG4JBKh6tA"

Optional:

    python .\scripts\translate_transcript.py "dyG4JBKh6tA" --batch-size 25
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# PATH CONFIGURATION
# ============================================================

# Project backend directory.
#
# Current file:
# backend/scripts/translate_transcript.py
#
# parents[1] -> backend/
BASE_DIR = Path(__file__).resolve().parents[1]


# Original Hindi/Hinglish transcripts.
TRANSCRIPT_DIR = (
    BASE_DIR
    / "data"
    / "transcripts"
)


# English translated transcripts.
TRANSLATED_DIR = (
    BASE_DIR
    / "data"
    / "translated"
)


# Environment file.
ENV_FILE = BASE_DIR / ".env"


# Load environment variables from backend/.env
load_dotenv(ENV_FILE)


# ============================================================
# CONFIGURATION
# ============================================================

# Number of transcript segments sent to Groq per request.
#
# Smaller batches:
# - reduce prompt size
# - reduce malformed JSON risk
# - make failures easier to retry
#
# Larger batches:
# - reduce number of API requests
#
# 25 remains the default.
DEFAULT_BATCH_SIZE = 25


# Maximum number of attempts for ordinary failed batches.
MAX_RETRIES = 3


# Groq model used for translation.
GROQ_MODEL = "openai/gpt-oss-120b"


# Seconds between ordinary retry attempts.
RETRY_DELAY_BASE_SECONDS = 2


# When a rate-limit response contains a "try again in X seconds"
# message, wait at least this many seconds before retrying.
RATE_LIMIT_MIN_WAIT_SECONDS = 5


# ============================================================
# GROQ CLIENT
# ============================================================

def get_groq_client() -> Groq:
    """
    Create and return a Groq API client.

    The API key is intentionally loaded from .env instead of
    being hard-coded in source code.

    Required .env variable:

        GROQ_API_KEY=...
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing from .env"
        )

    return Groq(
        api_key=api_key
    )


# ============================================================
# LOAD TRANSCRIPT
# ============================================================

def load_transcript(
    video_id: str,
) -> dict[str, Any]:
    """
    Load the original transcript JSON.

    Example:

        data/transcripts/dyG4JBKh6tA.json
    """

    file_path = (
        TRANSCRIPT_DIR
        / f"{video_id}.json"
    )

    print()
    print("=" * 60)
    print("Transcript configuration")
    print("=" * 60)
    print(f"BASE_DIR       : {BASE_DIR}")
    print(f"TRANSCRIPT_DIR : {TRANSCRIPT_DIR}")
    print(f"FILE           : {file_path}")
    print(f"EXISTS         : {file_path.exists()}")
    print("=" * 60)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Transcript not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if "segments" not in data:
        raise ValueError(
            "Transcript JSON does not contain 'segments'."
        )

    if not isinstance(
        data["segments"],
        list,
    ):
        raise ValueError(
            "'segments' must be a list."
        )

    stored_video_id = data.get("video_id")

    if stored_video_id and stored_video_id != video_id:
        raise ValueError(
            "Transcript video_id does not match the requested video ID.\n"
            f"Requested: {video_id}\n"
            f"Stored: {stored_video_id}"
        )

    video_title = data.get("video_title")

    if not isinstance(
        video_title,
        str,
    ) or not video_title.strip():
        raise ValueError(
            "Transcript JSON does not contain a valid 'video_title'. "
            "Re-run youtube_transcribe.py so the actual YouTube "
            "video title is stored."
        )

    return data


# ============================================================
# BUILD TRANSLATION INPUT
# ============================================================

def build_translation_input(
    segments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert transcript segments into a minimal structure for
    the LLM.

    Every segment receives its absolute transcript index.

    Example:

        [
            {
                "index": 0,
                "text": "Aapko..."
            },
            {
                "index": 1,
                "text": "Revision..."
            }
        ]

    Explicit indexes help detect skipped, merged, or reordered
    segments.
    """

    items: list[dict[str, Any]] = []

    for index, segment in enumerate(segments):
        items.append(
            {
                "index": index,
                "text": segment.get(
                    "text",
                    "",
                ).strip(),
            }
        )

    return items


# ============================================================
# PARSE GROQ JSON RESPONSE
# ============================================================

def parse_json_response(
    content: str,
) -> dict[str, Any]:
    """
    Parse the JSON returned by Groq.

    Defensive parsing handles accidental markdown code fences.
    """

    content = content.strip()

    if content.startswith("```"):
        lines = content.splitlines()

        if (
            lines
            and lines[0].startswith("```")
        ):
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    try:
        data = json.loads(content)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Groq returned invalid JSON.\n\n"
            f"Raw response:\n{content}"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Groq response must be a JSON object."
        )

    return data


# ============================================================
# VALIDATE TRANSLATION RESPONSE
# ============================================================

def validate_translations(
    response_data: dict[str, Any],
    segments: list[dict[str, Any]],
) -> list[str]:
    """
    Validate the structure returned by Groq.

    Expected:

        {
            "translations": [
                {
                    "index": 0,
                    "translation": "..."
                }
            ]
        }

    Validation:

    1. translations exists
    2. translations is a list
    3. count matches input
    4. every item is an object
    5. every item contains index
    6. every item contains translation
    7. index order is correct
    8. translation is non-empty
    """

    translations = response_data.get(
        "translations"
    )

    if not isinstance(
        translations,
        list,
    ):
        raise RuntimeError(
            "Groq response does not contain "
            "a 'translations' list."
        )

    expected_count = len(
        segments
    )

    if len(translations) != expected_count:
        raise RuntimeError(
            "Translation count mismatch.\n"
            f"Expected: {expected_count}\n"
            f"Received: {len(translations)}"
        )

    result: list[str] = []

    for position, item in enumerate(
        translations
    ):

        if not isinstance(
            item,
            dict,
        ):
            raise RuntimeError(
                f"Translation item {position} "
                "is not a JSON object."
            )

        if "index" not in item:
            raise RuntimeError(
                f"Translation item {position} "
                "does not contain 'index'."
            )

        if "translation" not in item:
            raise RuntimeError(
                f"Translation item {position} "
                "does not contain 'translation'."
            )

        index = item["index"]

        if index != position:
            raise RuntimeError(
                "Translation index mismatch.\n"
                f"Expected index: {position}\n"
                f"Received index: {index}"
            )

        translation = item["translation"]

        if not isinstance(
            translation,
            str,
        ):
            raise RuntimeError(
                f"Translation for index {index} "
                "must be a string."
            )

        translation = translation.strip()

        if not translation:
            raise RuntimeError(
                f"Empty translation for index {index}."
            )

        result.append(
            translation
        )

    return result


# ============================================================
# RATE LIMIT HELPERS
# ============================================================

def is_rate_limit_error(
    error: Exception,
) -> bool:
    """
    Determine whether an exception represents a rate-limit
    response.
    """

    error_text = str(error).lower()

    rate_limit_markers = (
        "rate limit",
        "rate_limit_exceeded",
        "too many requests",
        "429",
        "tokens per day",
        "tpd",
    )

    return any(
        marker in error_text
        for marker in rate_limit_markers
    )


def extract_wait_seconds(
    error: Exception,
) -> int | None:
    """
    Try to extract a server-provided retry delay.

    Supports messages such as:

        "try again in 16m55.6s"

        "try again in 20 seconds"
    """

    error_text = str(error)

    # Match minutes + optional decimal seconds.
    minute_match = re.search(
        r"try again in\s+(\d+)m(?:(\d+(?:\.\d+)?)s)?",
        error_text,
        flags=re.IGNORECASE,
    )

    if minute_match:
        minutes = int(
            minute_match.group(1)
        )

        seconds_text = minute_match.group(2)

        seconds = (
            float(seconds_text)
            if seconds_text
            else 0.0
        )

        return max(
            RATE_LIMIT_MIN_WAIT_SECONDS,
            int(minutes * 60 + seconds) + 1,
        )

    # Match seconds only.
    second_match = re.search(
        r"try again in\s+(\d+(?:\.\d+)?)s",
        error_text,
        flags=re.IGNORECASE,
    )

    if second_match:
        seconds = float(
            second_match.group(1)
        )

        return max(
            RATE_LIMIT_MIN_WAIT_SECONDS,
            int(seconds) + 1,
        )

    return None


# ============================================================
# TRANSLATE ONE BATCH
# ============================================================

def translate_batch(
    client: Groq,
    segments: list[dict[str, Any]],
) -> list[str]:
    """
    Translate one batch of transcript segments.

    Timestamps are not sent to the LLM because timestamps do
    not need translation.
    """

    translation_input = (
        build_translation_input(
            segments
        )
    )

    input_json = json.dumps(
        translation_input,
        ensure_ascii=False,
        indent=2,
    )

    # --------------------------------------------------------
    # SYSTEM PROMPT
    # --------------------------------------------------------

    system_prompt = """
You are a professional technical translator.

Your task is to translate Hindi/Hinglish DSA lecture
transcripts into clear, natural English.

You MUST follow these rules:

1. Translate every input item.
2. Do NOT summarize.
3. Do NOT add explanations.
4. Preserve the original meaning.
5. Preserve DSA terminology.
6. Keep programming terminology in standard English.
7. Preserve the exact order of the input items.
8. Preserve every input index exactly.
9. Return exactly one translation for every input item.
10. Never merge two input items.
11. Never split one input item.
12. Never skip an input item.
13. If a sentence is already English, keep it natural and unchanged
    unless a small grammatical correction is required.
14. Do not translate code, variable names, function names,
    class names, algorithm names, or programming keywords unnecessarily.

The response MUST be a JSON object with this exact structure:

{
  "translations": [
    {
      "index": 0,
      "translation": "English translation"
    }
  ]
}

Do not return markdown.
Do not return ```json.
Return JSON only.
"""

    # --------------------------------------------------------
    # USER PROMPT
    # --------------------------------------------------------

    user_prompt = f"""
Translate the following DSA lecture transcript items.

INPUT:

{input_json}
"""

    # --------------------------------------------------------
    # GROQ API REQUEST
    # --------------------------------------------------------

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0,
        response_format={
            "type": "json_object"
        },
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    if not content:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    response_data = (
        parse_json_response(
            content
        )
    )

    return validate_translations(
        response_data,
        segments,
    )


# ============================================================
# RETRY FAILED BATCH
# ============================================================

def translate_batch_with_retry(
    client: Groq,
    segments: list[dict[str, Any]],
    start_index: int,
) -> list[str]:
    """
    Retry a translation batch.

    Ordinary failures use short exponential-style delays.

    Rate-limit failures are handled differently:

    - detect 429/rate-limit errors
    - extract server-provided wait time when available
    - wait for that amount
    - retry
    """

    last_error: Exception | None = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:
            print(
                f"  Attempt "
                f"{attempt}/{MAX_RETRIES}"
            )

            translations = (
                translate_batch(
                    client,
                    segments,
                )
            )

            return translations

        except Exception as error:
            last_error = error

            print(
                f"  Translation attempt failed: "
                f"{error}"
            )

            if attempt >= MAX_RETRIES:
                break

            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if is_rate_limit_error(error):

                wait_seconds = (
                    extract_wait_seconds(
                        error
                    )
                )

                if wait_seconds is None:
                    wait_seconds = 60

                print(
                    f"  Rate limit detected."
                )

                print(
                    f"  Waiting approximately "
                    f"{wait_seconds} seconds..."
                )

                time.sleep(
                    wait_seconds
                )

                continue

            # ------------------------------------------------
            # ORDINARY FAILURE
            # ------------------------------------------------

            wait_seconds = (
                attempt
                * RETRY_DELAY_BASE_SECONDS
            )

            print(
                f"  Retrying in "
                f"{wait_seconds} seconds..."
            )

            time.sleep(
                wait_seconds
            )

    raise RuntimeError(
        f"Translation failed for batch "
        f"starting at segment {start_index} "
        f"after {MAX_RETRIES} attempts."
    ) from last_error


# ============================================================
# PARTIAL TRANSLATION HELPERS
# ============================================================

def get_partial_path(
    video_id: str,
) -> Path:
    """
    Return the checkpoint file path.

    Example:

        data/translated/Fu7LD_mIo00.partial.json
    """

    return (
        TRANSLATED_DIR
        / f"{video_id}.partial.json"
    )


def save_partial_transcript(
    video_id: str,
    video_title: str,
    source: str,
    source_url: str,
    translated_segments: list[dict[str, Any]],
) -> Path:
    """
    Save the current translation checkpoint.

    This function is called after every successfully translated
    batch so progress survives process/API failures.
    """

    TRANSLATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    partial_path = get_partial_path(
        video_id
    )

    output_data = {
        "video_id": video_id,
        "video_title": video_title,
        "source": source,
        "source_url": source_url,
        "translation": "English",
        "segment_count": len(
            translated_segments
        ),
        "segments": translated_segments,
    }

    # Write to a temporary checkpoint first.
    #
    # This reduces the chance of leaving a half-written JSON
    # file if the process is interrupted during writing.
    temp_path = partial_path.with_suffix(
        ".partial.tmp"
    )

    with temp_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output_data,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.flush()
        os.fsync(
            file.fileno()
        )

    # Replace the previous checkpoint atomically.
    temp_path.replace(
        partial_path
    )

    return partial_path


def load_partial_transcript(
    video_id: str,
) -> dict[str, Any] | None:
    """
    Load an existing partial translation if present.

    Returns None when no usable checkpoint exists.
    """

    partial_path = get_partial_path(
        video_id
    )

    if not partial_path.exists():
        return None

    try:
        with partial_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ) as error:

        print(
            f"Warning: unable to load partial "
            f"translation checkpoint: {error}"
        )

        print(
            "Starting translation from the beginning."
        )

        return None

    if not isinstance(
        data,
        dict,
    ):
        print(
            "Warning: partial translation checkpoint "
            "has an invalid structure."
        )

        return None

    segments = data.get(
        "segments"
    )

    if not isinstance(
        segments,
        list,
    ):
        print(
            "Warning: partial translation checkpoint "
            "does not contain a valid segments list."
        )

        return None

    return data


def validate_partial_progress(
    partial_data: dict[str, Any],
    source_segments: list[dict[str, Any]],
) -> int:
    """
    Validate and return the number of completed segments.

    The partial file must contain a sequential prefix of the
    original transcript.

    Example:

        source segments: 0 ... 1188
        partial segments: 0 ... 1124

    Result:

        1125
    """

    partial_segments = partial_data.get(
        "segments"
    )

    if not isinstance(
        partial_segments,
        list,
    ):
        raise ValueError(
            "Partial translation does not contain "
            "a valid segments list."
        )

    completed_count = len(
        partial_segments
    )

    if completed_count > len(
        source_segments
    ):
        raise ValueError(
            "Partial translation contains more segments "
            "than the source transcript."
        )

    for index in range(
        completed_count
    ):

        partial_segment = (
            partial_segments[index]
        )

        source_segment = (
            source_segments[index]
        )

        partial_segment_id = (
            partial_segment.get(
                "segment_id"
            )
        )

        source_segment_id = (
            source_segment.get(
                "segment_id"
            )
        )

        if (
            partial_segment_id
            != source_segment_id
        ):
            raise ValueError(
                "Partial translation checkpoint does not match "
                "the source transcript at segment "
                f"{index}."
            )

        if "text_en" not in partial_segment:
            raise ValueError(
                "Partial translation checkpoint is missing "
                f"text_en at segment {index}."
            )

        text_en = partial_segment.get(
            "text_en"
        )

        if not isinstance(
            text_en,
            str,
        ) or not text_en.strip():
            raise ValueError(
                "Partial translation contains an empty "
                f"translation at segment {index}."
            )

    return completed_count


# ============================================================
# SAVE FINAL TRANSLATED TRANSCRIPT
# ============================================================

def save_translated_transcript(
    video_id: str,
    video_title: str,
    source: str,
    source_url: str,
    translated_segments: list[dict[str, Any]],
) -> Path:
    """
    Save the final translated transcript.

    Final output:

        data/translated/<video_id>.json
    """

    TRANSLATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        TRANSLATED_DIR
        / f"{video_id}.json"
    )

    output_data = {
        "video_id": video_id,
        "video_title": video_title,
        "source": source,
        "source_url": source_url,
        "translation": "English",
        "segment_count": len(
            translated_segments
        ),
        "segments": translated_segments,
    }

    # Write final output atomically as well.
    temp_path = output_path.with_suffix(
        ".tmp"
    )

    with temp_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output_data,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.flush()
        os.fsync(
            file.fileno()
        )

    temp_path.replace(
        output_path
    )

    return output_path


# ============================================================
# MAIN TRANSLATION PIPELINE
# ============================================================

def translate_transcript(
    video_id: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Path:
    """
    Complete resume-safe translation pipeline.

    Flow:

        transcript JSON
              ↓
        load transcript
              ↓
        detect checkpoint
              ↓
        resume from completed segments
              ↓
        translate next batch
              ↓
        validate response
              ↓
        save checkpoint
              ↓
        repeat
              ↓
        save final translated JSON
              ↓
        remove checkpoint
    """

    if batch_size <= 0:
        raise ValueError(
            "batch_size must be greater than 0."
        )

    # --------------------------------------------------------
    # LOAD SOURCE TRANSCRIPT
    # --------------------------------------------------------

    transcript = load_transcript(
        video_id
    )

    stored_video_id = transcript.get(
        "video_id",
        video_id,
    )

    video_title = transcript.get(
        "video_title",
    )

    source = transcript.get(
        "source",
        "youtube-transcript",
    )

    source_url = transcript.get(
        "source_url",
        f"https://www.youtube.com/watch?v={video_id}",
    )

    if stored_video_id != video_id:
        raise ValueError(
            "Loaded transcript video ID does not match "
            "the requested video ID."
        )

    if not isinstance(
        video_title,
        str,
    ) or not video_title.strip():
        raise ValueError(
            "A valid video_title is required."
        )

    segments = transcript[
        "segments"
    ]

    if not segments:
        raise ValueError(
            "Transcript contains no segments."
        )

    total_segments = len(
        segments
    )

    # --------------------------------------------------------
    # LOAD EXISTING CHECKPOINT
    # --------------------------------------------------------

    translated_segments: list[
        dict[str, Any]
    ] = []

    partial_data = (
        load_partial_transcript(
            video_id
        )
    )

    if partial_data is not None:

        try:
            completed_count = (
                validate_partial_progress(
                    partial_data,
                    segments,
                )
            )

        except ValueError as error:

            print()
            print(
                "Warning: existing partial checkpoint "
                "cannot be safely resumed."
            )

            print(
                f"Reason: {error}"
            )

            print(
                "Starting translation from the beginning."
            )

            completed_count = 0
            partial_data = None

        if partial_data is not None:

            translated_segments = list(
                partial_data["segments"]
            )

            print()
            print("=" * 60)
            print("Existing translation checkpoint found")
            print("=" * 60)
            print(
                f"Completed segments : "
                f"{completed_count}/{total_segments}"
            )
            print(
                f"Remaining segments : "
                f"{total_segments - completed_count}"
            )
            print(
                f"Checkpoint         : "
                f"{get_partial_path(video_id)}"
            )
            print("=" * 60)

    # --------------------------------------------------------
    # IF FINAL FILE ALREADY EXISTS
    # --------------------------------------------------------

    final_path = (
        TRANSLATED_DIR
        / f"{video_id}.json"
    )

    if final_path.exists():

        try:
            with final_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                existing_final = json.load(
                    file
                )

            existing_segments = (
                existing_final.get(
                    "segments"
                )
            )

            if (
                isinstance(
                    existing_segments,
                    list,
                )
                and len(existing_segments)
                == total_segments
            ):

                print()
                print("=" * 60)
                print("Translation already completed")
                print("=" * 60)
                print(
                    f"File: {final_path}"
                )
                print(
                    f"Segments: {len(existing_segments)}"
                )
                print("=" * 60)

                return final_path

        except (
            json.JSONDecodeError,
            OSError,
        ):
            print(
                "Existing final translation file is invalid "
                "or unreadable. It will be rebuilt."
            )

    # --------------------------------------------------------
    # IF NOTHING REMAINS
    # --------------------------------------------------------

    if len(
        translated_segments
    ) >= total_segments:

        output_path = (
            save_translated_transcript(
                video_id=video_id,
                video_title=video_title,
                source=source,
                source_url=source_url,
                translated_segments=translated_segments,
            )
        )

        partial_path = get_partial_path(
            video_id
        )

        if partial_path.exists():
            partial_path.unlink()

        print()
        print(
            "All segments were already translated "
            "in the checkpoint."
        )

        return output_path

    # --------------------------------------------------------
    # CREATE GROQ CLIENT ONLY WHEN WORK REMAINS
    # --------------------------------------------------------

    client = get_groq_client()

    # --------------------------------------------------------
    # PIPELINE INFORMATION
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("Starting translation")
    print("=" * 60)

    print(
        f"Video ID      : {video_id}"
    )

    print(
        f"Video title   : {video_title}"
    )

    print(
        f"Total segments: {total_segments}"
    )

    print(
        f"Batch size    : {batch_size}"
    )

    print(
        f"Already done  : "
        f"{len(translated_segments)}"
    )

    print(
        f"Remaining     : "
        f"{total_segments - len(translated_segments)}"
    )

    print(
        f"Model         : {GROQ_MODEL}"
    )

    print(
        f"Checkpoint    : "
        f"{get_partial_path(video_id)}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # PROCESS TRANSCRIPT IN BATCHES
    # --------------------------------------------------------

    start_index = len(
        translated_segments
    )

    for start_index in range(
        start_index,
        total_segments,
        batch_size,
    ):

        end_index = min(
            start_index + batch_size,
            total_segments,
        )

        batch = segments[
            start_index:end_index
        ]

        print()
        print(
            f"Translating segments "
            f"{start_index} - "
            f"{end_index - 1}"
        )

        # ----------------------------------------------------
        # TRANSLATE CURRENT BATCH
        # ----------------------------------------------------

        translations = (
            translate_batch_with_retry(
                client=client,
                segments=batch,
                start_index=start_index,
            )
        )

        # ----------------------------------------------------
        # MERGE ORIGINAL + TRANSLATED DATA
        # ----------------------------------------------------

        for segment, translation in zip(
            batch,
            translations,
        ):

            translated_segment = {
                **segment,
                "text_en": translation,
            }

            translated_segments.append(
                translated_segment
            )

        # ----------------------------------------------------
        # SAVE CHECKPOINT IMMEDIATELY
        # ----------------------------------------------------

        completed = len(
            translated_segments
        )

        checkpoint_path = (
            save_partial_transcript(
                video_id=video_id,
                video_title=video_title,
                source=source,
                source_url=source_url,
                translated_segments=translated_segments,
            )
        )

        print(
            f"  ✓ Completed "
            f"{completed}/{total_segments}"
        )

        print(
            f"  ✓ Checkpoint saved: "
            f"{checkpoint_path.name}"
        )

    # --------------------------------------------------------
    # SAVE FINAL RESULT
    # --------------------------------------------------------

    output_path = (
        save_translated_transcript(
            video_id=video_id,
            video_title=video_title,
            source=source,
            source_url=source_url,
            translated_segments=translated_segments,
        )
    )

    # --------------------------------------------------------
    # REMOVE CHECKPOINT
    # --------------------------------------------------------

    partial_path = get_partial_path(
        video_id
    )

    if partial_path.exists():
        partial_path.unlink()

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("Translation completed successfully.")
    print("=" * 60)

    print(
        f"Saved to: {output_path}"
    )

    print(
        f"Segments translated: "
        f"{len(translated_segments)}"
    )

    print(
        f"Video title preserved: "
        f"{video_title}"
    )

    print(
        "Checkpoint removed: True"
    )

    return output_path


# ============================================================
# CLI
# ============================================================

def main() -> None:
    """
    Command-line interface.

    Usage:

        python .\scripts\translate_transcript.py VIDEO_ID

    Optional:

        --batch-size 25
    """

    parser = argparse.ArgumentParser(
        description=(
            "Translate a YouTube transcript "
            "from Hindi/Hinglish to English "
            "while preserving video metadata "
            "and translation progress."
        )
    )

    parser.add_argument(
        "video_id",
        help="YouTube video ID",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=(
            "Number of transcript segments "
            "per translation batch. "
            "Default: 25"
        ),
    )

    args = parser.parse_args()

    translate_transcript(
        video_id=args.video_id,
        batch_size=args.batch_size,
    )


# ============================================================
# PYTHON ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()