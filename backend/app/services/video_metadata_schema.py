"""
Video Metadata Schema

Purpose:
    Define the canonical metadata stored for each DSA-pattern video.

Architecture:

    25 Core Patterns
            ↓
    Pattern-specific Playlist
            ↓
    Video Metadata
            ↓
    Transcript Chunks

Example:

    {
        "video_id": "abc123",
        "video_title": "Two Pointer - Episode 1",
        "playlist": "DSA_Patterns_Two_Pointer",
        "pattern": "two_pointer",
        "sub_patterns": [
            "pair_search",
            "opposite_direction"
        ],
        "video_order": 1
    }

Important design decision:
    `playlist` is derived from `pattern` using the canonical taxonomy.
    This prevents inconsistent values such as:

        DSA Patterns
        DSA_Patterns
        Two Pointer Playlist
        DSA_Patterns_TwoPointers

    The canonical value for the two_pointer pattern is:

        DSA_Patterns_Two_Pointer

Sub-patterns:
    A video may cover more than one sub-pattern, so video metadata stores
    `sub_patterns` as a list. Later, chunk-level metadata can assign the
    most specific `sub_pattern` to an individual chunk when necessary.

This module has no external dependencies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .dsa_taxonomy import (
    get_playlist_name,
    is_valid_pattern,
    is_valid_sub_pattern,
)


# ============================================================
# VIDEO METADATA
# ============================================================

@dataclass(frozen=True)
class VideoMetadata:
    """
    Canonical metadata for one DSA-pattern video.

    Required:
        video_id:
            YouTube's unique video ID.

        video_title:
            Original/display title of the video.

        pattern:
            Canonical DSA pattern slug from dsa_taxonomy.py.

    Derived:
        playlist:
            Canonical pattern-specific playlist name. It is generated from
            `pattern` and should not be manually assigned.

    Optional:
        playlist_id:
            Actual YouTube playlist ID, if available.

        video_order:
            Position of this video inside the pattern playlist.

        sub_patterns:
            Canonical sub-patterns covered by this video.

        source_url:
            YouTube URL for the video.
    """

    video_id: str
    video_title: str
    pattern: str

    playlist: str

    playlist_id: str | None = None
    video_order: int | None = None
    sub_patterns: tuple[str, ...] = ()
    source_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the metadata object into a JSON-serializable dictionary."""
        data = asdict(self)

        # JSON does not have a tuple type.
        data["sub_patterns"] = list(self.sub_patterns)

        return data


# ============================================================
# VALIDATION
# ============================================================

def validate_video_metadata(
    metadata: VideoMetadata,
) -> None:
    """
    Validate one VideoMetadata object.

    Raises:
        ValueError:
            If required fields are missing, the pattern is unknown,
            the playlist does not match the pattern, or a sub-pattern
            does not belong to the pattern.
    """

    # --------------------------------------------------------
    # Required identifiers.
    # --------------------------------------------------------

    if not metadata.video_id.strip():
        raise ValueError("video_id cannot be empty.")

    if not metadata.video_title.strip():
        raise ValueError("video_title cannot be empty.")

    # --------------------------------------------------------
    # Pattern validation.
    # --------------------------------------------------------

    if not is_valid_pattern(metadata.pattern):
        raise ValueError(
            f"Unknown DSA pattern: {metadata.pattern!r}."
        )

    # --------------------------------------------------------
    # Playlist consistency.
    #
    # Playlist must always be derived from the pattern.
    # --------------------------------------------------------

    expected_playlist = get_playlist_name(
        metadata.pattern
    )

    if metadata.playlist != expected_playlist:
        raise ValueError(
            "Playlist does not match pattern. "
            f"Expected {expected_playlist!r}, "
            f"received {metadata.playlist!r}."
        )

    # --------------------------------------------------------
    # Video order validation.
    # --------------------------------------------------------

    if metadata.video_order is not None:
        if metadata.video_order < 1:
            raise ValueError(
                "video_order must be greater than or equal to 1."
            )

    # --------------------------------------------------------
    # Sub-pattern validation.
    #
    # A video may cover multiple sub-patterns, but every one of them
    # must belong to the video's parent pattern.
    # --------------------------------------------------------

    for sub_pattern in metadata.sub_patterns:
        if not is_valid_sub_pattern(
            metadata.pattern,
            sub_pattern,
        ):
            raise ValueError(
                f"Invalid sub-pattern {sub_pattern!r} "
                f"for pattern {metadata.pattern!r}."
            )

    # --------------------------------------------------------
    # Prevent duplicate sub-pattern entries.
    # --------------------------------------------------------

    if len(metadata.sub_patterns) != len(
        set(metadata.sub_patterns)
    ):
        raise ValueError(
            "sub_patterns contains duplicate values."
        )


# ============================================================
# FACTORY
# ============================================================

def build_video_metadata(
    *,
    video_id: str,
    video_title: str,
    pattern: str,
    playlist_id: str | None = None,
    video_order: int | None = None,
    sub_patterns: list[str] | tuple[str, ...] | None = None,
    source_url: str | None = None,
) -> VideoMetadata:
    """
    Build validated video metadata.

    `playlist` is intentionally NOT accepted as an argument.

    It is derived from the canonical pattern taxonomy so that callers
    cannot accidentally create mismatched metadata.
    """

    normalized_sub_patterns = tuple(
        sub_patterns or ()
    )

    metadata = VideoMetadata(
        video_id=video_id.strip(),
        video_title=video_title.strip(),
        pattern=pattern,
        playlist=get_playlist_name(pattern),
        playlist_id=playlist_id,
        video_order=video_order,
        sub_patterns=normalized_sub_patterns,
        source_url=source_url,
    )

    validate_video_metadata(metadata)

    return metadata


# ============================================================
# EXAMPLE
# ============================================================

if __name__ == "__main__":
    example = build_video_metadata(
        video_id="abc123",
        video_title="Two Pointer - Episode 1",
        pattern="two_pointer",
        video_order=1,
        sub_patterns=[
            "pair_search",
            "opposite_direction",
        ],
        source_url="https://www.youtube.com/watch?v=abc123",
    )

    print("Video metadata schema loaded successfully.")
    print()
    print("Validated metadata:")
    print(example.to_dict())
