"""
Smart Transcript Chunking Utility

The Script:

1. Loads a translated transcript JSON.
2. Groups multiple transcript segments into meaningful chunks.
3. Preserves the original timestamps.
4. Preserves the original transcript text.
5. Preserves the English translation.
6. Add chunk-level metadata.
7. Uses a small overlap between neighboring chunks.
8. Saves the generated chunks under data/chunks/.

The generated chunks will later be used for :

    Chunking
        ↓
    Embeddings
        ↓
    Qdrant
        ↓
    Semantic Retrieval
        ↓
    Timestamp-aware RAG

Example:
    python .\scripts\chunk_transcript.py "dyG4JBKh6tA"

Optional:
    python .\scripts\chunk_transcript.py "dyG4JBKh6tA" --target-chars 1000


"""


from __future__ import annotations

import argparse
import json
import re 
from pathlib import Path
from typing import Any





# ============================================================
# PATH CONFIGURATION
# ============================================================


# Current file:
#
# backend/scripts/chunk_transcript.py
#
# parents[1] points to:
#
# backend/
#
# Therefore all data paths are built relative to the backend
# directory instead of using hard-coded operating-system paths.

BASE_DIR = Path(__file__).resolve().parents[1]


# Directory containing translated transcript JSON files.
#
# Example:
#
# backend/data/translated/dyG4JBKh6tA.json
#
TRANSLATED_DIR = (
    BASE_DIR
    / "data"
    / "translated"
)



# Directory where generated chunks will be stored.
#
# Example:
#
# backend/data/chunks/dyG4JBKh6tA.json
#
CHUNKS_DIR = (
    BASE_DIR
    / "data"
    / "chunks"
)

# ============================================================
# CHUNKING CONFIGURATION
# ============================================================

# Target approximate number of characters per chunk.
#
# This is NOT a hard limit.
#
# The chunker tries to create chunks around this size while
# respecting transcript segment boundaries.
#
# Keeping chunks reasonably small helps semantic retrieval
# because each vector represents a focused piece of information.
DEFAULT_TARGET_CHARS = 1000


# Maximum number of characters allowed in a normal chunk.
#
# We use this as a safety boundary so that one chunk does not
# become unnecessarily large.
DEFAULT_MAX_CHARS = 1400


# Number of transcript segments reused between neighboring chunks.
#
# Example:
#
# Chunk 1:
#   segments 0 - 8
#
# Chunk 2:
#   segments 7 - 15
#
# Segment 7 and 8 may therefore provide contextual continuity.
#
# This overlap is useful because DSA explanations often continue
# from one transcript segment into the next.
DEFAULT_OVERLAP_SEGMENTS = 2


# ============================================================
# LOAD TRANSCRIPT
# ============================================================

def load_transcript(
    video_id: str,
) -> dict[str, Any]:
    """
    Load the translated transcript JSON.

    Expected input:

        backend/data/translated/<video_id>.json

    Expected structure:

        {
            "video_id": "...",
            "video_title": "...",
            "source": "...",
            "source_url": "...",
            "translation": "English",
            "segment_count": 566,
            "segments": [...]
        }

    Returns:
        The parsed transcript dictionary.

    Raises:
        FileNotFoundError:
            If the transcript does not exist.

        ValueError:
            If the JSON structure is invalid.
    """

    file_path = (
        TRANSLATED_DIR
        / f"{video_id}.json"
    )

    print()
    print("=" * 60)
    print("Transcript configuration")
    print("=" * 60)
    print(f"BASE_DIR       : {BASE_DIR}")
    print(f"TRANSLATED_DIR : {TRANSLATED_DIR}")
    print(f"FILE           : {file_path}")
    print(f"EXISTS         : {file_path.exists()}")
    print("=" * 60)

    # Fail early if the translated transcript does not exist.
    if not file_path.exists():
        raise FileNotFoundError(
            f"Translated transcript not found: {file_path}"
        )

    # Read the JSON using UTF-8.
    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    # Validate the expected structure.
    if "segments" not in data:
        raise ValueError(
            "Translated transcript does not contain 'segments'."
        )

    if not isinstance(
        data["segments"],
        list,
    ):
        raise ValueError(
            "'segments' must be a list."
        )

    if not data["segments"]:
        raise ValueError(
            "Translated transcript contains no segments."
        )

    # The translation stage is expected to preserve the canonical
    # YouTube metadata created by youtube_transcribe.py.
    video_title = data.get("video_title")

    if not isinstance(video_title, str) or not video_title.strip():
        raise ValueError(
            "Translated transcript does not contain a valid 'video_title'. "
            "Re-run youtube_transcribe.py and translate_transcript.py."
        )

    stored_video_id = data.get("video_id")

    if stored_video_id and stored_video_id != video_id:
        raise ValueError(
            "Translated transcript video_id does not match the requested "
            "video ID. "
            f"Requested: {video_id}, stored: {stored_video_id}"
        )

    return data



# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(
    text: str,
) -> str:
    """
    Normalize whitespace inside transcript text.

    This function intentionally performs only light normalization.

    We do NOT aggressively clean the text because the original
    transcript should remain available for auditing and debugging.

    Example:

        "Two   pointer   is useful"

    becomes:

        "Two pointer is useful"
    """

    return re.sub(
        r"\s+",
        " ",
        text.strip(),
    )




# ============================================================
# SENTENCE BOUNDARY DETECTION
# ============================================================

def ends_with_sentence_boundary(
    text: str,
) -> bool:
    """
    Check whether the current chunk appears to end at a natural
    sentence boundary.

    This is only a lightweight heuristic.

    It is NOT intended to perform full NLP sentence segmentation.

    Examples considered boundaries:

        "."
        "?"
        "!"
        ":"

    This helps avoid cutting an explanation in the middle of a
    thought whenever possible.
    """

    text = text.strip()

    if not text:
        return False

    return bool(
        re.search(
            r"[.!?:]$",
            text,
        )
    )


# ============================================================
# CREATE CHUNK
# ============================================================

def create_chunk(
    video_id: str,
    video_title: str,
    source_url: str | None,
    chunk_id: int,
    segments: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Convert a group of transcript segments into one chunk.

    Important design principle:

        A chunk is made from complete transcript segments.

    We never cut an individual transcript segment in half.

    The chunk preserves:

        - video_id
        - video_title
        - source_url
        - chunk_id
        - segment_start
        - segment_end
        - start
        - end
        - duration
        - text
        - text_en

    This makes the chunk directly usable by the future
    timestamp-aware retrieval system.
    """

    if not segments:
        raise ValueError(
            "Cannot create a chunk from an empty segment list."
        )

    # Extract the first and last segment.
    first_segment = segments[0]
    last_segment = segments[-1]

    # Combine original transcript text.
    original_text = " ".join(
        normalize_text(
            str(segment.get("text", ""))
        )
        for segment in segments
        if segment.get("text")
    )

    # Combine English transcript text.
    english_text = " ".join(
        normalize_text(
            str(segment.get("text_en", ""))
        )
        for segment in segments
        if segment.get("text_en")
    )

    # Calculate chunk duration.
    start = float(
        first_segment["start"]
    )

    end = float(
        last_segment["end"]
    )

    duration = end - start

    chunk_data: dict[str, Any] = {
        "video_id": video_id,
        "video_title": video_title,
        "chunk_id": chunk_id,

        # IDs of the first and last transcript segments
        # represented by this chunk.
        "segment_start": first_segment["segment_id"],
        "segment_end": last_segment["segment_id"],

        # Timestamp information is preserved at chunk level.
        "start": round(start, 3),
        "end": round(end, 3),
        "duration": round(duration, 3),

        # Original transcript remains available.
        "text": original_text,

        # English representation is used later for semantic
        # retrieval and embedding generation.
        "text_en": english_text,

        # Number of transcript segments represented by this chunk.
        "segment_count": len(segments),
    }

    if source_url:
        chunk_data["source_url"] = source_url

    return chunk_data

# ============================================================
# SMART CHUNKING ALGORITHM
# ============================================================

def create_chunks(
    video_id: str,
    video_title: str,
    source_url: str | None,
    segments: list[dict[str, Any]],
    target_chars: int = DEFAULT_TARGET_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_segments: int = DEFAULT_OVERLAP_SEGMENTS,
) -> list[dict[str, Any]]:
    """
    Create timestamp-aware chunks from transcript segments.

    Strategy:

    1. Keep transcript segments intact.
    2. Accumulate segments until the chunk reaches the target size.
    3. Prefer ending at a natural sentence boundary.
    4. Never exceed the maximum size unless a single transcript
       segment itself is larger than the limit.
    5. Reuse a small number of segments in the next chunk.
    6. Preserve timestamps.
    7. Stop immediately when the current chunk reaches the end
       of the transcript to avoid creating a duplicate tail chunk.

    This gives us a deterministic and retrieval-friendly chunking
    strategy without requiring an additional NLP dependency.

    Example:

        Segment 0
        Segment 1
        Segment 2
        Segment 3
        Segment 4
        Segment 5
        Segment 6

    Could become:

        Chunk 0:
            0 - 4

        Chunk 1:
            3 - 6

    Here segments 3 and 4 provide contextual overlap.
    """

    # --------------------------------------------------------
    # Validate chunking configuration.
    # --------------------------------------------------------

    if target_chars <= 0:
        raise ValueError(
            "target_chars must be greater than 0."
        )

    if max_chars <= 0:
        raise ValueError(
            "max_chars must be greater than 0."
        )

    if target_chars > max_chars:
        raise ValueError(
            "target_chars cannot be greater than max_chars."
        )

    if overlap_segments < 0:
        raise ValueError(
            "overlap_segments cannot be negative."
        )

    # --------------------------------------------------------
    # Initialize chunking state.
    # --------------------------------------------------------

    chunks: list[dict[str, Any]] = []

    total_segments = len(segments)

    current_index = 0
    chunk_id = 0

    # --------------------------------------------------------
    # Continue creating chunks until all transcript segments
    # have been processed.
    # --------------------------------------------------------

    while current_index < total_segments:

        current_segments: list[
            dict[str, Any]
        ] = []

        current_chars = 0

        index = current_index

        # ----------------------------------------------------
        # Build one chunk.
        # ----------------------------------------------------

        while index < total_segments:

            segment = segments[index]

            # Prefer the translated English representation because
            # this is the text that will eventually be embedded.
            segment_text = normalize_text(
                str(
                    segment.get(
                        "text_en",
                        "",
                    )
                )
            )

            # Fall back to the original transcript if the English
            # translation is unavailable.
            if not segment_text:
                segment_text = normalize_text(
                    str(
                        segment.get(
                            "text",
                            "",
                        )
                    )
                )

            # Ignore completely empty transcript segments.
            if not segment_text:
                index += 1
                continue

            # Calculate the number of characters this segment
            # would add to the current chunk.
            additional_chars = len(
                segment_text
            )

            # Add one character for the space between segments.
            if current_segments:
                additional_chars += 1

            proposed_size = (
                current_chars
                + additional_chars
            )

            # ------------------------------------------------
            # If this is the first segment in the chunk,
            # always add it.
            #
            # This also ensures that a single large transcript
            # segment is not lost just because it exceeds the
            # normal maximum size.
            # ------------------------------------------------

            if not current_segments:

                current_segments.append(
                    segment
                )

                current_chars = len(
                    segment_text
                )

                index += 1

                continue

            # ------------------------------------------------
            # If the chunk is still below the target size,
            # add the segment normally.
            # ------------------------------------------------

            if proposed_size <= target_chars:

                current_segments.append(
                    segment
                )

                current_chars = proposed_size

                index += 1

                continue

            # ------------------------------------------------
            # We have reached the target size.
            #
            # Before stopping, check whether the current
            # chunk ends at a natural sentence boundary.
            # ------------------------------------------------

            current_text = " ".join(
                normalize_text(
                    str(
                        item.get(
                            "text_en",
                            item.get(
                                "text",
                                "",
                            ),
                        )
                    )
                )
                for item in current_segments
            )

            if ends_with_sentence_boundary(
                current_text
            ):
                break

            # ------------------------------------------------
            # If the proposed chunk is still below the maximum
            # allowed size, allow one additional segment.
            #
            # This helps avoid cutting an explanation too early.
            # ------------------------------------------------

            if proposed_size <= max_chars:

                current_segments.append(
                    segment
                )

                current_chars = proposed_size

                index += 1

                continue

            # ------------------------------------------------
            # Maximum chunk size reached.
            #
            # Stop building the current chunk.
            # ------------------------------------------------

            break

        # --------------------------------------------------------
        # Safety check.
        #
        # This should normally never happen, but prevents an
        # infinite loop if unexpected transcript data is present.
        # --------------------------------------------------------

        if not current_segments:
            current_index += 1
            continue

        # --------------------------------------------------------
        # Create the final chunk object.
        # --------------------------------------------------------

        chunk = create_chunk(
            video_id=video_id,
            video_title=video_title,
            source_url=source_url,
            chunk_id=chunk_id,
            segments=current_segments,
        )

        chunks.append(
            chunk
        )

        chunk_id += 1

        # --------------------------------------------------------
        # Calculate how far we have consumed.
        #
        # Example:
        #
        # current_index = 100
        # len(current_segments) = 25
        #
        # consumed_until = 125
        #
        # Therefore segments 100-124 have been covered.
        # --------------------------------------------------------

        consumed_until = (
            current_index
            + len(current_segments)
        )

        # --------------------------------------------------------
        # IMPORTANT EDGE-CASE FIX
        #
        # If this chunk already reaches the end of the transcript,
        # stop immediately.
        #
        # Without this check, the overlap logic below would move
        # backwards by a few segments and create a small duplicate
        # final chunk.
        #
        # Example of the old behavior:
        #
        # Chunk 23 → segments 561-565
        # Chunk 24 → segments 564-565  ❌
        #
        # With this check:
        #
        # Chunk 23 → segments 561-565
        # STOP                      ✅
        # --------------------------------------------------------

        if consumed_until >= total_segments:
            break

        # --------------------------------------------------------
        # Calculate the next starting position.
        #
        # We intentionally move backwards by a small number of
        # segments so neighboring chunks share some context.
        #
        # Example:
        #
        # Current chunk:
        #     0 - 20
        #
        # overlap = 2
        #
        # Next chunk starts at:
        #     19
        #
        # This creates contextual continuity between chunks.
        # --------------------------------------------------------

        next_index = (
            consumed_until
            - overlap_segments
        )

        # --------------------------------------------------------
        # Safety check:
        #
        # Never allow the next index to move backwards to the
        # same position or before the current chunk start.
        #
        # This prevents an infinite loop.
        # --------------------------------------------------------

        if next_index <= current_index:

            next_index = (
                current_index
                + len(current_segments)
            )

        # --------------------------------------------------------
        # Move to the next chunk.
        # --------------------------------------------------------

        current_index = next_index

    # --------------------------------------------------------
    # Return all generated chunks.
    # --------------------------------------------------------

    return chunks




# ============================================================
# SAVE CHUNKS
# ============================================================

def save_chunks(
    video_id: str,
    chunks: list[dict[str, Any]],
) -> Path:
    """
    Save generated chunks as JSON.

    Output:

        backend/data/chunks/<video_id>.json

    The output keeps the data structured so that later stages
    can load it directly for embedding generation.
    """

    # Create the chunks directory if necessary.
    CHUNKS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        CHUNKS_DIR
        / f"{video_id}.json"
    )

    # Derive video-level metadata from the first chunk. Every chunk
    # already carries the same metadata, so this keeps the output JSON
    # convenient to inspect without introducing another source of truth.
    first_chunk = chunks[0] if chunks else {}

    output_data = {
        "video_id": video_id,
        "video_title": first_chunk.get("video_title", ""),
        "source": "translated-transcript",
        "source_url": first_chunk.get("source_url"),
        "chunk_count": len(chunks),
        "chunks": chunks,
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
# MAIN CHUNKING PIPELINE
# ============================================================

def chunk_transcript(
    video_id: str,
    target_chars: int = DEFAULT_TARGET_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_segments: int = DEFAULT_OVERLAP_SEGMENTS,
) -> Path:
    """
    Run the complete transcript chunking pipeline.

    Flow:

        translated transcript
                ↓
        load transcript
                ↓
        read segments
                ↓
        smart chunking
                ↓
        preserve timestamps
                ↓
        save chunks
    """

    # Load translated transcript.
    transcript = load_transcript(
        video_id
    )

    segments = transcript[
        "segments"
    ]

    video_title = transcript[
        "video_title"
    ]

    source_url = transcript.get(
        "source_url"
    )

    # Display pipeline configuration.
    print()
    print("=" * 60)
    print("Starting smart chunking")
    print("=" * 60)

    print(
        f"Video ID          : {video_id}"
    )

    print(
        f"Video title       : {video_title}"
    )

    print(
        f"Total segments    : {len(segments)}"
    )

    print(
        f"Target characters : {target_chars}"
    )

    print(
        f"Maximum characters: {max_chars}"
    )

    print(
        f"Overlap segments  : {overlap_segments}"
    )

    print("=" * 60)

    # Generate chunks.
    chunks = create_chunks(
        video_id=video_id,
        video_title=video_title,
        source_url=source_url,
        segments=segments,
        target_chars=target_chars,
        max_chars=max_chars,
        overlap_segments=overlap_segments,
    )

    # Save chunks.
    output_path = save_chunks(
        video_id=video_id,
        chunks=chunks,
    )

    # --------------------------------------------------------
    # Print summary.
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("Chunking completed successfully.")
    print("=" * 60)

    print(
        f"Input segments : {len(segments)}"
    )

    print(
        f"Output chunks   : {len(chunks)}"
    )

    print(
        f"Saved to        : {output_path}"
    )

    if chunks:
        average_size = sum(
            len(chunk["text_en"])
            for chunk in chunks
        ) / len(chunks)

        print(
            f"Average chunk size: "
            f"{average_size:.0f} characters"
        )

    return output_path


# ============================================================
# CLI
# ============================================================

def main() -> None:
    """
    Command-line interface.

    Usage:

        python .\scripts\chunk_transcript.py VIDEO_ID

    Optional:

        --target-chars 1000
        --max-chars 1400
        --overlap 2
    """

    parser = argparse.ArgumentParser(
        description=(
            "Create timestamp-aware smart chunks "
            "from a translated DSA transcript."
        )
    )

    parser.add_argument(
        "video_id",
        help="YouTube video ID",
    )

    parser.add_argument(
        "--target-chars",
        type=int,
        default=DEFAULT_TARGET_CHARS,
        help=(
            "Approximate target size of each chunk "
            "in characters. Default: 1000"
        ),
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=(
            "Maximum normal chunk size in characters. "
            "Default: 1400"
        ),
    )

    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_OVERLAP_SEGMENTS,
        help=(
            "Number of transcript segments shared "
            "between neighboring chunks. Default: 2"
        ),
    )

    args = parser.parse_args()

    # Start the chunking pipeline.
    chunk_transcript(
        video_id=args.video_id,
        target_chars=args.target_chars,
        max_chars=args.max_chars,
        overlap_segments=args.overlap,
    )


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

# Run main() only when this file is executed directly.
if __name__ == "__main__":
    main()