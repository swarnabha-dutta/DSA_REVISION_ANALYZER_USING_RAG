"""
Metadata API routes for the DSA Revision Analyzer.

Provides:
    - Pattern -> video playlist
    - Single video metadata

The source of truth is the existing Qdrant collection.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.dsa_taxonomy import is_valid_pattern
from app.services.qdrant_client import (
    get_qdrant_client,
)


router = APIRouter(
    prefix="/api",
    tags=["Metadata"],
)


# ============================================================
# CONSTANTS
# ============================================================

QDRANT_COLLECTION = "dsa_revision"


# ============================================================
# HELPERS
# ============================================================


def normalize_pattern_id(
    pattern_id: str,
) -> str:
    """
    Convert frontend pattern IDs into backend canonical IDs.

    Example:
        two-pointer -> two_pointer
        two_pointer -> two_pointer
    """

    return (
        str(pattern_id)
        .strip()
        .lower()
        .replace("-", "_")
    )


def payload_to_video(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert a Qdrant payload into the frontend video shape.
    """

    video_id = payload.get(
        "video_id"
    )

    if not video_id:
        return {}

    video_title = (
        payload.get("video_title")
        or payload.get("title")
        or video_id
    )

    return {
        "id": video_id,
        "video_id": video_id,
        "title": video_title,
        "video_title": video_title,
        "description": "",
        "pattern": payload.get(
            "pattern"
        ),
        "playlist": payload.get(
            "playlist"
        ),
        "playlist_id": payload.get(
            "playlist_id"
        ),
        "video_order": payload.get(
            "video_order"
        ),
        "source_url": payload.get(
            "source_url"
        ),
        "thumbnail": (
            f"https://img.youtube.com/vi/"
            f"{video_id}/hqdefault.jpg"
        ),
        "duration": 0,
        "currentTime": 0,
        "completed": False,
    }


# ============================================================
# PATTERN VIDEOS
# ============================================================


@router.get(
    "/patterns/{pattern_id}/videos"
)
def get_pattern_videos(
    pattern_id: str,
) -> dict[str, Any]:
    """
    Return unique videos for a DSA pattern.

    Multiple Qdrant points can belong to the same video
    because each transcript chunk is stored separately.

    Therefore videos are deduplicated by video_id.
    """

    canonical_pattern = (
        normalize_pattern_id(
            pattern_id
        )
    )

    if not is_valid_pattern(
        canonical_pattern
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown DSA pattern: "
                f"{pattern_id}"
            ),
        )

    client = get_qdrant_client()

    try:
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            scroll_filter={
                "must": [
                    {
                        "key": "pattern",
                        "match": {
                            "value": canonical_pattern
                        },
                    }
                ]
            },
            limit=1000,
            with_payload=True,
            with_vectors=False,
        )

        videos = OrderedDict()

        for point in points:
            payload = (
                point.payload or {}
            )

            video = payload_to_video(
                payload
            )

            video_id = video.get(
                "video_id"
            )

            if not video_id:
                continue

            if video_id not in videos:
                videos[video_id] = video

        result = list(
            videos.values()
        )

        # ----------------------------------------------------
        # Playlist order
        # ----------------------------------------------------

        result.sort(
            key=lambda video: (
                video.get(
                    "video_order"
                )
                if video.get(
                    "video_order"
                )
                is not None
                else 999999
            )
        )

        return {
            "pattern": canonical_pattern,
            "count": len(result),
            "videos": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to load pattern videos."
            ),
        ) from exc


# ============================================================
# SINGLE VIDEO
# ============================================================


@router.get(
    "/videos/{video_id}"
)
def get_video(
    video_id: str,
) -> dict[str, Any]:
    """
    Return metadata for one video.
    """

    video_id = (
        str(video_id)
        .strip()
    )

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="video_id is required.",
        )

    client = get_qdrant_client()

    try:
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            scroll_filter={
                "must": [
                    {
                        "key": "video_id",
                        "match": {
                            "value": video_id
                        },
                    }
                ]
            },
            limit=1,
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Video not found: "
                    f"{video_id}"
                ),
            )

        payload = (
            points[0].payload or {}
        )

        video = payload_to_video(
            payload
        )

        if not video:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Video metadata not found: "
                    f"{video_id}"
                ),
            )

        return video

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to load video."
            ),
        ) from exc