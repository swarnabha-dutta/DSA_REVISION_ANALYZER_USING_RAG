"""
Pattern playlist API routes.

Responsibilities:
    - Return ordered videos for a DSA pattern.
    - Read video metadata from Qdrant.
    - Keep playlist retrieval separate from semantic search.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY",
    "",
).strip()

QDRANT_COLLECTION = os.getenv(
    "QDRANT_COLLECTION",
    "dsa_revision_chunks",
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/patterns",
    tags=["Patterns"],
)


# ============================================================
# QDRANT CLIENT
# ============================================================

def get_qdrant_client() -> QdrantClient:
    """
    Create a Qdrant client using the existing environment config.
    """

    if QDRANT_API_KEY:
        return QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

    return QdrantClient(
        url=QDRANT_URL,
    )


# ============================================================
# PATTERN VIDEO ENDPOINT
# ============================================================

@router.get(
    "/{pattern_id}/videos",
)
def get_pattern_videos(
    pattern_id: str,
) -> dict[str, Any]:
    """
    Return unique videos belonging to a DSA pattern.

    Videos are reconstructed from the Qdrant chunk metadata.

    The same video can have many transcript chunks, so duplicate
    video IDs are removed.

    Ordering:
        video_order ASC
        then video_id ASC
    """

    pattern_id = pattern_id.strip().lower()

    if not pattern_id:
        raise HTTPException(
            status_code=400,
            detail="pattern_id cannot be empty.",
        )

    client = get_qdrant_client()

    query_filter = Filter(
        must=[
            FieldCondition(
                key="pattern",
                match=MatchValue(
                    value=pattern_id,
                ),
            ),
        ],
    )

    try:
        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,
            scroll_filter=query_filter,
            limit=10000,
            with_payload=True,
            with_vectors=False,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to load pattern videos "
                f"from Qdrant: {exc}"
            ),
        ) from exc

    # ========================================================
    # DEDUPLICATE VIDEOS
    # ========================================================

    videos_by_id: dict[str, dict[str, Any]] = {}

    for point in points:
        payload = point.payload or {}

        video_id = payload.get(
            "video_id",
        )

        if not video_id:
            continue

        video_id = str(video_id).strip()

        if not video_id:
            continue

        # ----------------------------------------------------
        # Existing video
        # ----------------------------------------------------

        if video_id in videos_by_id:
            continue

        video_order = payload.get(
            "video_order",
        )

        try:
            normalized_order = (
                int(video_order)
                if video_order is not None
                else 999999
            )
        except (
            TypeError,
            ValueError,
        ):
            normalized_order = 999999

        video_title = str(
            payload.get(
                "video_title",
                "",
            )
        ).strip()

        source_url = payload.get(
            "source_url",
        )

        playlist = payload.get(
            "playlist",
        )

        videos_by_id[video_id] = {
            "id": video_id,
            "video_id": video_id,
            "title": video_title
                or video_id,
            "video_title": video_title
                or video_id,
            "pattern": payload.get(
                "pattern",
                pattern_id,
            ),
            "playlist": playlist,
            "playlist_id": payload.get(
                "playlist_id",
            ),
            "video_order": normalized_order,
            "source_url": source_url,
            "currentTime": 0,
            "completed": False,
        }

    # ========================================================
    # ORDER VIDEOS
    # ========================================================

    videos = list(
        videos_by_id.values()
    )

    videos.sort(
        key=lambda video: (
            video["video_order"],
            video["id"],
        ),
    )

    # ========================================================
    # NORMALIZE VIDEO ORDER
    # ========================================================

    for index, video in enumerate(
        videos,
        start=1,
    ):
        if video["video_order"] == 999999:
            video["video_order"] = index

    return {
        "pattern": pattern_id,
        "count": len(videos),
        "videos": videos,
    }