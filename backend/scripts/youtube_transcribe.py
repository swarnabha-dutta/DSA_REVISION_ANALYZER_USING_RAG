"""
YouTube Transcript Extraction Utility

This script:

1. Accepts a YouTube video ID or full YouTube URL.
2. Extracts the actual 11-character video ID.
3. Fetches the video's actual YouTube title.
4. Fetches the available transcript from YouTube.
5. Preserves timestamp information for every transcript segment.
6. Normalizes the transcript into our internal JSON structure.
7. Saves the result under data/transcripts/.

The video title is stored together with the transcript because downstream
stages (translation, chunking, metadata enrichment, embedding, and Qdrant
ingestion) need a stable video identity.

Example:

    python .\\scripts\\youtube_transcribe.py "dyG4JBKh6tA"

or:

    python .\\scripts\\youtube_transcribe.py \
        "https://www.youtube.com/watch?v=dyG4JBKh6tA"

Output:

    data/
    └── transcripts/
        └── dyG4JBKh6tA.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from youtube_transcript_api import YouTubeTranscriptApi


# ============================================================
# PATH CONFIGURATION
# ============================================================

# __file__ points to:
#
#     backend/scripts/youtube_transcribe.py
#
# parents[1] moves us to:
#
#     backend/
#
# Therefore transcripts are always stored at:
#
#     backend/data/transcripts/
#
# Using Path instead of hard-coded Windows paths keeps the project
# portable across different machines and operating systems.

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
        str:
            The 11-character YouTube video ID.

    Raises:
        ValueError:
            If the input does not contain a valid YouTube video ID.
    """

    # Remove leading/trailing whitespace.
    value = value.strip()

    # --------------------------------------------------------
    # Case 1: The user directly supplied the video ID.
    # --------------------------------------------------------

    # Standard YouTube video IDs contain exactly 11 characters
    # and may contain:
    #   - letters
    #   - numbers
    #   - underscore
    #   - hyphen

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    # --------------------------------------------------------
    # Case 2/3/4: The user supplied a YouTube URL.
    # --------------------------------------------------------

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

    # If none of the supported formats matched, fail explicitly
    # instead of silently continuing.

    raise ValueError(
        "Invalid YouTube URL or video ID."
    )


# ============================================================
# FETCH VIDEO TITLE
# ============================================================

def fetch_video_title(
    video_id: str,
) -> str:
    """
    Fetch the actual YouTube video title.

    YouTubeTranscriptApi provides transcript data, but it does not
    provide the video's display title. Therefore the title is fetched
    separately through YouTube's public oEmbed endpoint.

    This keeps the transcript API responsible only for transcript data
    while this function is responsible for video identity metadata.

    Returns:
        str:
            The actual YouTube video title.

    Raises:
        RuntimeError:
            If the title cannot be fetched or the response does not
            contain a usable title.
    """

    video_url = (
        f"https://www.youtube.com/watch?v={video_id}"
    )

    # YouTube oEmbed returns lightweight public metadata such as
    # the video's title without requiring an API key.
    oembed_url = (
        "https://www.youtube.com/oembed"
        f"?url={quote(video_url, safe='')}"
        "&format=json"
    )

    request = Request(
        oembed_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/120 Safari/537.36"
            )
        },
    )

    try:
        with urlopen(
            request,
            timeout=15,
        ) as response:

            payload = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

    except (
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
    ) as error:

        raise RuntimeError(
            "Could not fetch the YouTube video title. "
            f"Video ID: {video_id}"
        ) from error

    title = str(
        payload.get(
            "title",
            "",
        )
    ).strip()

    if not title:
        raise RuntimeError(
            "YouTube returned no usable video title. "
            f"Video ID: {video_id}"
        )

    return title


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

    Most importantly, timestamps are preserved because the future
    RAG system will use them to jump the user directly to the
    relevant part of the YouTube video.
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
    video_title: str,
    segments: list[dict],
) -> Path:
    """
    Save the normalized transcript and video metadata as JSON.

    Output example:

        data/
        └── transcripts/
            └── dyG4JBKh6tA.json

    The JSON contains:

        - video_id
        - video_title
        - source
        - source_url
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
        "video_title": video_title,
        "source": "youtube-transcript",
        "source_url": (
            f"https://www.youtube.com/watch?v={video_id}"
        ),
        "segment_count": len(segments),
        "segments": segments,
    }

    # Serialize JSON.
    #
    # ensure_ascii=False is important because Hindi/Hinglish/Bengali
    # text should remain readable instead of becoming Unicode escape
    # sequences.

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

    The script then automatically:

        1. Extracts the video ID.
        2. Fetches the actual YouTube title.
        3. Fetches the transcript.
        4. Saves both title and transcript metadata.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Fetch a YouTube transcript with timestamps "
            "and save the actual video title."
        )
    )

    parser.add_argument(
        "video",
        help="YouTube URL or video ID",
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Extract video ID.
    # --------------------------------------------------------

    video_id = extract_video_id(
        args.video
    )

    print(
        f"Video ID: {video_id}"
    )

    # --------------------------------------------------------
    # Fetch actual YouTube title.
    # --------------------------------------------------------

    print(
        "Fetching YouTube video title..."
    )

    video_title = fetch_video_title(
        video_id
    )

    print(
        f"Video title: {video_title}"
    )

    # --------------------------------------------------------
    # Fetch transcript.
    # --------------------------------------------------------

    print(
        f"Fetching transcript for: {video_id}"
    )

    segments = fetch_transcript(
        video_id
    )

    # --------------------------------------------------------
    # Save transcript + metadata.
    # --------------------------------------------------------

    output_file = save_transcript(
        video_id,
        video_title,
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
