"""
YouTube Transcript Extraction Utility

This script:
1. Accepts a YouTube video ID or full YouTube URL.
2. Extracts the actual 11-character video ID.
3. Fetches the available transcript from YouTube.
4. Preserves timestamp information for every transcript segment.
5. Normalizes the transcript into our internal JSON structure.
6. Saves the result under data/transcripts/.

Example:

    python .\scripts\youtube_transcribe.py "dyG4JBKh6tA"

or:

    python .\scripts\youtube_transcribe.py "https://www.youtube.com/watch?v=dyG4JBKh6tA"
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi


# ============================================================
# PATH CONFIGURATION
# ============================================================

# __file__ points to:
# backend/scripts/youtube_transcribe.py
#
# parents[1] moves us to:
# backend/
#
# Therefore transcripts are always stored at:
# backend/data/transcripts/
#
# Using Path instead of hard-coded Windows paths makes the
# project portable across different machines and operating systems.
OUTPUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "transcripts"
)


# ============================================================
# YOUTUBE VIDEO ID EXTRACTION
# ============================================================

def extract_video_id(value: str) -> str:
    """
    Extract a YouTube video ID from either:

    1. A raw YouTube video ID
       Example:
       dyG4JBKh6tA

    2. A standard YouTube URL
       Example:
       https://www.youtube.com/watch?v=dyG4JBKh6tA

    3. A shortened YouTube URL
       Example:
       https://youtu.be/dyG4JBKh6tA

    4. An embedded YouTube URL
       Example:
       https://www.youtube.com/embed/dyG4JBKh6tA

    Returns:
        str: The 11-character YouTube video ID.

    Raises:
        ValueError: If the input does not contain a valid
                    YouTube video ID.
    """

    # Remove leading/trailing whitespace.
    value = value.strip()

    # --------------------------------------------------------
    # Case 1: The user directly supplied the video ID.
    # --------------------------------------------------------
    #
    # Standard YouTube video IDs contain exactly 11 characters
    # and may contain:
    # - letters
    # - numbers
    # - underscore
    # - hyphen
    #
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    # --------------------------------------------------------
    # Case 2/3/4: The user supplied a YouTube URL.
    # --------------------------------------------------------
    #
    # We support the most common YouTube URL formats.
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, value)

        if match:
            return match.group(1)

    # If none of the supported formats matched,
    # fail explicitly instead of silently continuing.
    raise ValueError(
        "Invalid YouTube URL or video ID."
    )


# ============================================================
# FETCH TRANSCRIPT
# ============================================================

def fetch_transcript(
    video_id: str,
    languages: list[str] | None = None,
) -> list[dict]:
    """
    Fetch a YouTube transcript and normalize every transcript
    segment into our application's internal structure.

    We prefer English first, then Hindi, then Bengali.

    Why?

    The course may contain:
    - English transcripts
    - Hindi transcripts
    - Bengali transcripts

    YouTubeTranscriptApi will try the languages in the supplied
    order and use an available transcript.

    Each returned segment contains:

        segment_id
        start
        end
        duration
        text

    Most importantly, timestamps are preserved because the
    future RAG system will use them to jump the user directly
    to the relevant part of the YouTube video.
    """

    # Default language preference.
    if languages is None:
        languages = [
            "en",
            "hi",
            "bn",
        ]

    # Create the YouTube transcript API client.
    api = YouTubeTranscriptApi()

    # Fetch the transcript for the requested video.
    transcript = api.fetch(
        video_id,
        languages=languages,
    )

    # This list will contain our normalized transcript data.
    segments: list[dict] = []

    # Iterate through every transcript segment.
    for index, item in enumerate(transcript):

        # Transcript start time in seconds.
        start = float(item.start)

        # Duration of the spoken segment.
        duration = float(item.duration)

        # End timestamp = start + duration.
        end = start + duration

        # Remove unnecessary whitespace.
        text = item.text.strip()

        # Ignore completely empty transcript segments.
        if not text:
            continue

        # Convert the API response into our own stable format.
        #
        # This is important because later components should not
        # depend directly on YouTubeTranscriptApi's internal model.
        segments.append(
            {
                "segment_id": index,
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(duration, 3),
                "text": text,
            }
        )

    return segments


# ============================================================
# SAVE TRANSCRIPT
# ============================================================

def save_transcript(
    video_id: str,
    segments: list[dict],
) -> Path:
    """
    Save the normalized transcript as JSON.

    Output example:

        data/
        └── transcripts/
            └── dyG4JBKh6tA.json

    The JSON contains:
        - video_id
        - source
        - segment_count
        - segments

    The original timestamp information is preserved.
    """

    # Create the directory if it does not already exist.
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # One JSON file per YouTube video.
    output_file = (
        OUTPUT_DIR
        / f"{video_id}.json"
    )

    # Build the final JSON structure.
    payload = {
        "video_id": video_id,
        "source": "youtube-transcript",
        "segment_count": len(segments),
        "segments": segments,
    }

    # Serialize JSON.
    #
    # ensure_ascii=False is important because Hindi/Hinglish
    # text should remain readable instead of becoming Unicode
    # escape sequences.
    output_file.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_file


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main() -> None:
    """
    Command-line entry point.

    The user only needs to provide:
        - YouTube URL
        OR
        - YouTube video ID
    """

    parser = argparse.ArgumentParser(
        description=(
            "Fetch a YouTube transcript "
            "with timestamps."
        )
    )

    parser.add_argument(
        "video",
        help="YouTube URL or video ID",
    )

    args = parser.parse_args()

    # Convert whatever the user supplied into a clean
    # YouTube video ID.
    video_id = extract_video_id(
        args.video
    )

    print(
        f"Fetching transcript for: {video_id}"
    )

    # Fetch transcript.
    segments = fetch_transcript(
        video_id
    )

    # Save transcript.
    output_file = save_transcript(
        video_id,
        segments,
    )

    print(
        f"Transcript saved to:\n{output_file}"
    )

    print(
        f"Segments: {len(segments)}"
    )


# This ensures main() runs only when this file is executed
# directly from the command line.
if __name__ == "__main__":
    main()