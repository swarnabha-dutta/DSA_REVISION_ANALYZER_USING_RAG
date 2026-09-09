"""
Metadata Storage Helpers

Purpose:
    Bridge validated video-level metadata into the existing chunk-based
    ingestion pipeline.

The existing DSA Revision Analyzer stores transcript chunks and later sends
those chunks to Qdrant. This module enriches each chunk with canonical
pattern metadata before embedding ingestion.

Design:

    VideoMetadata
          ↓
    enrich_chunks_with_metadata()
          ↓
    enriched chunk JSON
          ↓
    ingest_embeddings.py
          ↓
    Qdrant payload

Important:
    - `video_id` remains the chunk/video identity.
    - `pattern`, `playlist`, and video metadata are propagated to every chunk.
    - A chunk may optionally have one specific `sub_pattern`.
    - If no chunk-specific sub-pattern is known, `sub_pattern` is omitted
      rather than guessing.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .dsa_taxonomy import (
    get_playlist_name,
    is_valid_pattern,
    is_valid_sub_pattern,
)
from .video_metadata_schema import VideoMetadata, validate_video_metadata


# ============================================================
# CHUNK METADATA ENRICHMENT
# ============================================================

def enrich_chunks_with_metadata(
    chunks: list[dict[str, Any]],
    video_metadata: VideoMetadata,
) -> list[dict[str, Any]]:
    """
    Add canonical video metadata to every transcript chunk.

    Existing chunk data is preserved.

    The function returns new dictionaries instead of mutating the input list,
    which makes the transformation safer and easier to test.

    Chunk-level `sub_pattern` behavior:
        1. If a chunk already has a valid `sub_pattern`, preserve it.
        2. If the chunk has no sub-pattern and the video covers exactly one
           sub-pattern, inherit that one.
        3. If the video covers multiple sub-patterns, do not guess.
           Leave the chunk without a sub-pattern.

    This prevents an entire multi-topic video from being incorrectly labeled
    as one sub-pattern.
    """

    validate_video_metadata(video_metadata)

    enriched_chunks: list[dict[str, Any]] = []

    for chunk in chunks:
        enriched = deepcopy(chunk)

        # ----------------------------------------------------
        # Video-level metadata.
        # ----------------------------------------------------

        enriched["video_id"] = video_metadata.video_id
        enriched["video_title"] = video_metadata.video_title
        enriched["pattern"] = video_metadata.pattern
        enriched["playlist"] = video_metadata.playlist

        if video_metadata.playlist_id is not None:
            enriched["playlist_id"] = video_metadata.playlist_id

        if video_metadata.video_order is not None:
            enriched["video_order"] = video_metadata.video_order

        if video_metadata.source_url is not None:
            enriched["source_url"] = video_metadata.source_url

        # ----------------------------------------------------
        # Chunk-level sub-pattern.
        # ----------------------------------------------------

        existing_sub_pattern = enriched.get("sub_pattern")

        if existing_sub_pattern is not None:
            if not is_valid_sub_pattern(
                video_metadata.pattern,
                existing_sub_pattern,
            ):
                raise ValueError(
                    f"Chunk {chunk.get('chunk_id')!r} contains invalid "
                    f"sub_pattern {existing_sub_pattern!r} for pattern "
                    f"{video_metadata.pattern!r}."
                )
        elif len(video_metadata.sub_patterns) == 1:
            enriched["sub_pattern"] = (
                video_metadata.sub_patterns[0]
            )

        enriched_chunks.append(enriched)

    return enriched_chunks


# ============================================================
# METADATA PAYLOAD
# ============================================================

def build_metadata_payload(
    video_metadata: VideoMetadata,
) -> dict[str, Any]:
    """
    Build the video-level portion of a Qdrant payload.

    `playlist` is derived again from the canonical pattern as a defensive
    consistency check.
    """

    if not is_valid_pattern(video_metadata.pattern):
        raise ValueError(
            f"Unknown DSA pattern: {video_metadata.pattern!r}"
        )

    expected_playlist = get_playlist_name(
        video_metadata.pattern
    )

    if video_metadata.playlist != expected_playlist:
        raise ValueError(
            f"Playlist mismatch for pattern "
            f"{video_metadata.pattern!r}: "
            f"expected {expected_playlist!r}, "
            f"received {video_metadata.playlist!r}."
        )

    payload: dict[str, Any] = {
        "video_id": video_metadata.video_id,
        "video_title": video_metadata.video_title,
        "playlist": video_metadata.playlist,
        "pattern": video_metadata.pattern,
    }

    if video_metadata.playlist_id is not None:
        payload["playlist_id"] = video_metadata.playlist_id

    if video_metadata.video_order is not None:
        payload["video_order"] = video_metadata.video_order

    if video_metadata.sub_patterns:
        payload["video_sub_patterns"] = list(
            video_metadata.sub_patterns
        )

    if video_metadata.source_url is not None:
        payload["source_url"] = video_metadata.source_url

    return payload


# ============================================================
# EXAMPLE SELF-CHECK
# ============================================================

if __name__ == "__main__":
    metadata = VideoMetadata(
        video_id="abc123",
        video_title="Two Pointer - Episode 1",
        pattern="two_pointer",
        playlist="DSA_Patterns_Two_Pointer",
        video_order=1,
        sub_patterns=("pair_search",),
    )

    chunks = [
        {
            "chunk_id": 0,
            "segment_start": 0,
            "segment_end": 5,
            "text": "Find a pair with target sum.",
            "text_en": "Find a pair with target sum.",
        },
        {
            "chunk_id": 1,
            "segment_start": 5,
            "segment_end": 10,
            "text": "Move the pointers.",
            "text_en": "Move the pointers.",
        },
    ]

    enriched = enrich_chunks_with_metadata(
        chunks,
        metadata,
    )

    assert len(enriched) == 2
    assert enriched[0]["pattern"] == "two_pointer"
    assert enriched[0]["playlist"] == "DSA_Patterns_Two_Pointer"
    assert enriched[0]["sub_pattern"] == "pair_search"

    payload = build_metadata_payload(metadata)

    assert payload["playlist"] == "DSA_Patterns_Two_Pointer"

    print("Metadata storage self-check: PASSED")
