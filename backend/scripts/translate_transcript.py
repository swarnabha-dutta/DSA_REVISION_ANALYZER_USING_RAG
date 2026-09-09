"""
Transcript Translation Utility

This script:

1. Loads a transcript JSON from data/transcripts/.
2. Reads the original Hindi/Hinglish transcript segments.
3. Preserves source video metadata such as video_title and source_url.
4. Sends transcript segments to Groq in small batches.
5. Translates Hindi/Hinglish into clear technical English.
6. Preserves timestamps and original segment IDs.
7. Validates the LLM response.
8. Retries failed translation batches.
9. Saves the translated transcript under data/translated/.

Example:

    python .\scripts\translate_transcript.py "dyG4JBKh6tA"

Optional:

    python .\scripts\translate_transcript.py "dyG4JBKh6tA" --batch-size 25
"""

from __future__ import annotations

import argparse
import json
import os
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
# - reduce risk of malformed responses
# - make failures easier to retry
#
# Larger batches:
# - reduce number of API requests
#
# 25 is a safer starting point for this project.
DEFAULT_BATCH_SIZE = 25


# Maximum number of attempts for a failed batch.
MAX_RETRIES = 3


# Groq model used for translation.
GROQ_MODEL = "openai/gpt-oss-120b"


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

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

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

    The current transcript format contains:

        {
            "video_id": "...",
            "video_title": "...",
            "source": "...",
            "source_url": "...",
            "segment_count": 566,
            "segments": [...]
        }

    Important:

    The video metadata is intentionally loaded as part of the
    complete transcript object so downstream stages do not lose
    the actual YouTube video identity.
    """

    file_path = (
        TRANSCRIPT_DIR
        / f"{video_id}.json"
    )

    # Print useful debugging information.
    print()
    print("=" * 60)
    print("Transcript configuration")
    print("=" * 60)
    print(f"BASE_DIR       : {BASE_DIR}")
    print(f"TRANSCRIPT_DIR : {TRANSCRIPT_DIR}")
    print(f"FILE           : {file_path}")
    print(f"EXISTS         : {file_path.exists()}")
    print("=" * 60)

    # Fail early if the transcript does not exist.
    if not file_path.exists():
        raise FileNotFoundError(
            f"Transcript not found: {file_path}"
        )

    # Read JSON using UTF-8 so Hindi characters are preserved.
    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    # Validate the expected top-level structure.
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

    # Validate video identity.
    stored_video_id = data.get("video_id")

    if stored_video_id and stored_video_id != video_id:
        raise ValueError(
            "Transcript video_id does not match the requested video ID.\n"
            f"Requested: {video_id}\n"
            f"Stored: {stored_video_id}"
        )

    # The title should already exist because youtube_transcribe.py
    # now stores the actual YouTube title.
    #
    # We fail explicitly instead of silently replacing the title
    # with the video ID.
    video_title = data.get("video_title")

    if not isinstance(video_title, str) or not video_title.strip():
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

    Every segment receives an explicit index.

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

    Why explicit indexes?

    Because LLMs can occasionally:
    - merge items
    - skip items
    - reorder items

    The index allows us to detect those failures.
    """

    items: list[dict[str, Any]] = []

    for index, segment in enumerate(
        segments
    ):
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

    The model should return JSON only.

    However, defensive parsing is still useful because an LLM
    may occasionally wrap JSON inside markdown code fences.
    """

    content = content.strip()

    # Remove accidental markdown code fences.
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

        content = "\n".join(
            lines
        ).strip()

    # Parse JSON.
    try:
        data = json.loads(
            content
        )

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Groq returned invalid JSON.\n\n"
            f"Raw response:\n{content}"
        ) from error

    # We expect an object, not a JSON array.
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

    Expected response:

        {
            "translations": [
                {
                    "index": 0,
                    "translation": "..."
                }
            ]
        }

    Validation checks:

    1. translations exists.
    2. translations is a list.
    3. Number of translations matches input segments.
    4. Every item is a JSON object.
    5. Every item contains an index.
    6. Every item contains a translation.
    7. Index order is correct.
    8. Translation is a non-empty string.

    If anything fails, the batch will be retried.
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

    # The model must return exactly one translation
    # for every input segment.
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

    # Validate every translation item.
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

        # Make sure the model didn't reorder the segments.
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
# TRANSLATE ONE BATCH
# ============================================================

def translate_batch(
    client: Groq,
    segments: list[dict[str, Any]],
) -> list[str]:
    """
    Translate one batch of transcript segments.

    We send only the segment index and original text.

    Timestamp information is NOT sent to the LLM because
    timestamps do not need translation.

    The original timestamp information remains untouched in
    the final JSON.
    """

    # Build structured LLM input.
    translation_input = (
        build_translation_input(
            segments
        )
    )

    # Convert Python objects into readable JSON.
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

        # Ask the model to return a JSON object.
        response_format={
            "type": "json_object"
        },
    )

    # Extract model response.
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

    # Parse JSON.
    response_data = (
        parse_json_response(
            content
        )
    )

    # Validate and return translations.
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
    Retry a translation batch if the Groq request or response
    validation fails.

    Retry delays:

        Attempt 1 fails -> wait 2 seconds
        Attempt 2 fails -> wait 4 seconds
        Attempt 3 fails -> stop

    This protects the pipeline from temporary API failures
    and occasional malformed LLM responses.
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

            # Do not sleep after the final attempt.
            if attempt < MAX_RETRIES:

                wait_seconds = (
                    attempt * 2
                )

                print(
                    f"  Retrying in "
                    f"{wait_seconds} seconds..."
                )

                time.sleep(
                    wait_seconds
                )

    # Every attempt failed.
    raise RuntimeError(
        f"Translation failed for batch "
        f"starting at segment {start_index} "
        f"after {MAX_RETRIES} attempts."
    ) from last_error


# ============================================================
# SAVE TRANSLATED TRANSCRIPT
# ============================================================

def save_translated_transcript(
    video_id: str,
    video_title: str,
    source: str,
    source_url: str,
    translated_segments: list[dict[str, Any]],
) -> Path:
    """
    Save the translated transcript.

    Important:

    Metadata from the original transcript is preserved:

        video_id
        video_title
        source
        source_url

    The translated segments preserve:

        segment_id
        start
        end
        duration
        text

    and add:

        text_en

    Therefore a translated segment looks like:

        {
            "segment_id": 0,
            "start": 0.8,
            "end": 4.88,
            "duration": 4.08,
            "text": "original Hindi text",
            "text_en": "English translation"
        }

    This structure is extremely useful for the future RAG
    system because semantic search can use text_en while
    timestamp navigation can use start/end.
    """

    # Make sure the destination directory exists.
    TRANSLATED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        TRANSLATED_DIR
        / f"{video_id}.json"
    )

    # Build final JSON.

    # We intentionally carry forward video_title and source_url
    # instead of rebuilding them from the video ID. This prevents
    # downstream stages from losing source metadata.
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

    # Write UTF-8 JSON.
    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output_data,
            file,
            ensure_ascii=False,
            indent=2,
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
    Complete translation pipeline.

    Flow:

        transcript JSON
              ↓
        load transcript + metadata
              ↓
        split into batches
              ↓
        translate batch
              ↓
        validate response
              ↓
        preserve timestamps
              ↓
        preserve video metadata
              ↓
        save translated JSON
    """

    # Prevent invalid batch sizes.
    if batch_size <= 0:
        raise ValueError(
            "batch_size must be greater than 0."
        )

    # Create Groq client.
    client = get_groq_client()

    # Load original transcript.
    transcript = load_transcript(
        video_id
    )

    # --------------------------------------------------------
    # LOAD SOURCE METADATA
    # --------------------------------------------------------

    # These fields were created by youtube_transcribe.py.
    # They are carried through unchanged.
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

    # Defensive validation.
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

    # Extract transcript segments.
    segments = transcript[
        "segments"
    ]

    if not segments:
        raise ValueError(
            "Transcript contains no segments."
        )

    # This will contain the final translated segments.
    translated_segments: list[
        dict[str, Any]
    ] = []

    total_segments = len(
        segments
    )

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
        f"Model         : {GROQ_MODEL}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # PROCESS TRANSCRIPT IN BATCHES
    # --------------------------------------------------------

    for start_index in range(
        0,
        total_segments,
        batch_size,
    ):

        # Calculate the end of this batch.
        end_index = min(
            start_index + batch_size,
            total_segments,
        )

        # Extract current batch.
        batch = segments[
            start_index:end_index
        ]

        print()
        print(
            f"Translating segments "
            f"{start_index} - "
            f"{end_index - 1}"
        )

        # Translate current batch with retry support.
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
        #
        # We NEVER replace the original segment.
        #
        # Instead:
        #
        # original:
        #     text
        #
        # new:
        #     text_en
        #
        # This keeps the original transcript available for
        # debugging, auditing and multilingual retrieval.

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

        # Progress information.
        completed = len(
            translated_segments
        )

        print(
            f"  ✓ Completed "
            f"{completed}/{total_segments}"
        )

    # --------------------------------------------------------
    # SAVE RESULT
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
            "while preserving video metadata."
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

    # Start translation pipeline.
    translate_transcript(
        video_id=args.video_id,
        batch_size=args.batch_size,
    )


# Run CLI only when this file is executed directly.
if __name__ == "__main__":
    main()
