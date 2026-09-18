"""
Pattern playlist API routes.

Responsibilities:
    - Return ordered videos for a DSA pattern.
    - Read video metadata from Qdrant.
    - Keep playlist retrieval separate from semantic search.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
)


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
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

VIDEO_CATALOG_PATH = (
    BASE_DIR
    / "data"
    / "video_catalog.json"
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/patterns",
    tags=["Patterns"],
)


# ============================================================
# VIDEO CATALOG
# ============================================================

def load_video_catalog() -> dict[str, Any]:
    """
    Load the canonical pattern -> ordered video catalog.

    The catalog is intentionally kept separate from Qdrant.

    Why?

    Qdrant contains transcript chunks.

    One video can have many chunks.

    The playlist, however, needs exactly one
    entry per video.

    Therefore:

        video_catalog.json
                ↓
        canonical playlist

        Qdrant
                ↓
        transcript / metadata enrichment
    """

    if not VIDEO_CATALOG_PATH.exists():
        return {}

    try:
        with VIDEO_CATALOG_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def get_catalog_videos(
    pattern_id: str,
) -> list[dict[str, Any]]:
    """
    Return ordered catalog entries for one
    canonical pattern.
    """

    catalog = load_video_catalog()

    pattern = catalog.get(
        pattern_id
    )

    if not isinstance(pattern, dict):
        return []

    videos = pattern.get(
        "videos",
        []
    )

    if not isinstance(videos, list):
        return []

    normalized: list[dict[str, Any]] = []

    for item in videos:

        if not isinstance(item, dict):
            continue

        video_id = str(
            item.get(
                "video_id",
                "",
            )
        ).strip()

        if not video_id:
            continue

        try:
            video_order = int(
                item.get(
                    "video_order",
                    999999,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            video_order = 999999

        video_title = str(
            item.get(
                "video_title"
            )
            or video_id
        ).strip()

        normalized.append(
            {
                "id": video_id,

                "video_id": video_id,

                "title": video_title,

                "video_title": video_title,

                "pattern": pattern_id,

                "playlist": (
                    "DSA_Patterns_Two_Pointer"
                    if pattern_id == "two_pointer"
                    else None
                ),

                "playlist_id": (
                    item.get(
                        "playlist_id"
                    )
                    or pattern.get(
                        "playlist_id"
                    )
                ),

                "video_order": video_order,

                "original_episode": (
                    item.get(
                        "original_episode"
                    )
                ),

                "source_url": (
                    item.get(
                        "source_url"
                    )
                ),

                "currentTime": 0,

                "completed": False,
            }
        )

    normalized.sort(
        key=lambda video: (
            video["video_order"],
            video["id"],
        )
    )

    return normalized


# ============================================================
# QDRANT CLIENT
# ============================================================

def get_qdrant_client() -> QdrantClient:
    """
    Create a Qdrant client using the
    existing environment configuration.
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

    Playlist source:

        video_catalog.json

    Metadata enrichment:

        Qdrant

    Important:

    Qdrant contains multiple transcript chunks
    for the same video.

    Therefore video IDs are deduplicated.

    Ordering:

        video_order ASC
        then video_id ASC
    """

    # ========================================================
    # NORMALIZE PATTERN ID
    # ========================================================

    pattern_id = (
        pattern_id
        .strip()
        .lower()
    )

    if not pattern_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "pattern_id cannot be empty."
            ),
        )


    # ========================================================
    # LOAD CANONICAL CATALOG
    # ========================================================

    catalog_videos = get_catalog_videos(
        pattern_id
    )


    # ========================================================
    # INITIAL VIDEO MAP
    # ========================================================

    videos_by_id: dict[
        str,
        dict[str, Any]
    ] = {
        video["id"]: video
        for video in catalog_videos
    }


    # ========================================================
    # QDRANT CLIENT
    # ========================================================

    client = get_qdrant_client()


    # ========================================================
    # QDRANT FILTER
    # ========================================================

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


    # ========================================================
    # QDRANT SCROLL
    # ========================================================

    try:

        points, _ = client.scroll(
            collection_name=QDRANT_COLLECTION,

            scroll_filter=query_filter,

            limit=10000,

            with_payload=True,

            with_vectors=False,
        )

    except Exception as exc:

        # ----------------------------------------------------
        # FALLBACK TO CATALOG
        # ----------------------------------------------------
        #
        # Playlist navigation should continue to work
        # even if Qdrant is unavailable.
        #
        # This is important because:
        #
        # playlist != semantic search
        #
        # ----------------------------------------------------

        if catalog_videos:

            return {
                "pattern": pattern_id,

                "count": len(
                    catalog_videos
                ),

                "videos": catalog_videos,

                "source": "catalog",
            }

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

    for point in points:

        payload = (
            point.payload
            or {}
        )

        video_id = payload.get(
            "video_id"
        )

        if not video_id:
            continue

        video_id = str(
            video_id
        ).strip()

        if not video_id:
            continue


        # Existing canonical catalog entry
        existing = (
            videos_by_id.get(
                video_id,
                {}
            )
        )


        # ----------------------------------------------------
        # VIDEO ORDER
        # ----------------------------------------------------

        video_order = (
            payload.get(
                "video_order"
            )
            or existing.get(
                "video_order",
                999999,
            )
        )

        try:

            normalized_order = int(
                video_order
            )

        except (
            TypeError,
            ValueError,
        ):

            normalized_order = 999999


        # ----------------------------------------------------
        # VIDEO TITLE
        # ----------------------------------------------------

        video_title = str(
            payload.get(
                "video_title"
            )
            or existing.get(
                "video_title"
            )
            or video_id
        ).strip()


        # ----------------------------------------------------
        # MERGE CATALOG + QDRANT
        # ----------------------------------------------------

        videos_by_id[
            video_id
        ] = {

            **existing,

            "id": video_id,

            "video_id": video_id,

            "title": video_title,

            "video_title": video_title,

            "pattern": (
                payload.get(
                    "pattern"
                )
                or existing.get(
                    "pattern"
                )
                or pattern_id
            ),

            "playlist": (
                payload.get(
                    "playlist"
                )
                or existing.get(
                    "playlist"
                )
            ),

            "playlist_id": (
                payload.get(
                    "playlist_id"
                )
                or existing.get(
                    "playlist_id"
                )
            ),

            "video_order": (
                normalized_order
            ),

            "original_episode": (
                existing.get(
                    "original_episode"
                )
            ),

            "source_url": (
                payload.get(
                    "source_url"
                )
                or existing.get(
                    "source_url"
                )
            ),

            "currentTime": 0,

            "completed": False,
        }


    # ========================================================
    # CONVERT MAP → LIST
    # ========================================================

    videos = list(
        videos_by_id.values()
    )


    # ========================================================
    # ORDER VIDEOS
    # ========================================================

    videos.sort(
        key=lambda video: (
            video["video_order"],
            video["id"],
        )
    )


    # ========================================================
    # NORMALIZE UNKNOWN ORDERS
    # ========================================================

    for index, video in enumerate(
        videos,
        start=1,
    ):

        if (
            video["video_order"]
            == 999999
        ):

            video["video_order"] = index


    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "pattern": pattern_id,

        "count": len(
            videos
        ),

        "videos": videos,

        "source": "catalog+qdrant",
    }