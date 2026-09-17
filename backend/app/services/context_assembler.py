"""
Context assembly layer for the DSA Revision Analyzer.

This module converts final hybrid-retrieval results into a
structured, deterministic context suitable for downstream
LLM generation.

Phase 12 responsibilities:
    - Preserve final reranked order
    - Enforce Top-K
    - Preserve stable point IDs
    - Preserve chunk text
    - Preserve video/pattern/sub-pattern metadata
    - Preserve timestamps when available
    - Remove duplicate point IDs
    - Handle empty retrieval results safely

Phase 14.1 responsibilities:
    - Format retrieved timestamp ranges consistently for human/LLM-readable
      context without changing the underlying numeric timestamp metadata

Phase 14.2 responsibilities:
    - Generate safe YouTube jump links from video ID + timestamp_start
    - Omit jump links when required metadata is missing
    - Expose links in deterministic assembled context output

Phase 14.3 responsibilities:
    - Extract and validate the relevant timestamp range
    - Normalize start/end values to floats
    - Calculate the duration of the relevant range
    - Reject incomplete or invalid timestamp ranges
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence
from urllib.parse import quote


# ============================================================
# CONTEXT ITEM
# ============================================================


@dataclass(frozen=True)
class ContextItem:
    """
    One retrieved chunk prepared for downstream LLM usage.
    """

    rank: int
    point_id: str
    text: str

    video_id: str | None
    pattern: str | None
    sub_pattern: str | None

    timestamp_start: float | None
    timestamp_end: float | None

    rrf_score: float | None
    reranker_score: float | None

    # Optional metadata added for video-level search summaries.
    video_title: str | None = None


# ============================================================
# CONTEXT RESULT
# ============================================================


@dataclass(frozen=True)
class AssembledContext:
    """
    Final structured context produced by the context assembly layer.
    """

    query: str
    pattern: str | None
    sub_pattern: str | None
    items: list[ContextItem]

    @property
    def text(self) -> str:
        """
        Return a deterministic text representation for LLM input.
        """

        if not self.items:
            return ""

        sections: list[str] = []

        for item in self.items:
            lines = [
                f"[Context {item.rank}]",
                f"Point ID: {item.point_id}",
                f"Video ID: {item.video_id or 'unknown'}",
                f"Video Title: {item.video_title or 'unknown'}",
                f"Pattern: {item.pattern or 'unknown'}",
                f"Sub-pattern: {item.sub_pattern or 'unknown'}",
                (
                    "Timestamp: "
                    f"{_format_timestamp_range(item.timestamp_start, item.timestamp_end)}"
                ),
            ]

            jump_link = _build_youtube_jump_link(
                item.video_id,
                item.timestamp_start,
            )

            if jump_link:
                lines.append(
                    f"Video jump link: {jump_link}"
                )

            lines.extend(
                [
                    "",
                    item.text,
                ]
            )

            sections.append("\n".join(lines))

        return "\n\n".join(sections)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the assembled context into a JSON-serializable dictionary.
        """

        return {
            "query": self.query,
            "pattern": self.pattern,
            "sub_pattern": self.sub_pattern,
            "items": [
                asdict(item)
                for item in self.items
            ],
        }


# ============================================================
# VALUE EXTRACTION HELPERS
# ============================================================


def _get_value(
    source: Any,
    *names: str,
    default: Any = None,
) -> Any:
    """
    Read a value from either:
        - an object attribute
        - a dictionary key
    """

    if source is None:
        return default

    for name in names:
        if isinstance(source, dict):
            if name in source:
                return source[name]

        else:
            value = getattr(
                source,
                name,
                None,
            )

            if value is not None:
                return value

    return default


def _get_nested_value(
    source: Any,
    names: Sequence[str],
) -> Any:
    """
    Search for a value across a small number of likely
    metadata containers.
    """

    if source is None:
        return None

    value = _get_value(
        source,
        *names,
    )

    if value is not None:
        return value

    for container_name in (
        "metadata",
        "payload",
        "meta",
    ):
        container = _get_value(
            source,
            container_name,
        )

        value = _get_value(
            container,
            *names,
        )

        if value is not None:
            return value

    return None


def _to_float(
    value: Any,
) -> float | None:
    """
    Safely convert a value to float.
    """

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# PHASE 14.3 — RELEVANT TIME-RANGE EXTRACTION
# ============================================================


def _extract_relevant_time_range(
    start: Any,
    end: Any,
) -> dict[str, float] | None:
    """
    Extract and validate a relevant video time range.

    Parameters
    ----------
    start:
        Start timestamp of the retrieved video segment.

    end:
        End timestamp of the retrieved video segment.

    Returns
    -------
    dict[str, float] | None
        A normalized range containing:
            - start
            - end
            - duration

        Returns None when:
            - either timestamp is missing
            - either timestamp is non-numeric
            - either timestamp is negative
            - start is greater than end
    """

    normalized_start = _to_float(start)
    normalized_end = _to_float(end)

    if normalized_start is None or normalized_end is None:
        return None

    if normalized_start < 0 or normalized_end < 0:
        return None

    if normalized_start > normalized_end:
        return None

    duration = round(
        normalized_end - normalized_start,
        3,
    )

    return {
        "start": normalized_start,
        "end": normalized_end,
        "duration": duration,
    }


# ============================================================
# PHASE 14.2 — VIDEO JUMP LINK
# ============================================================


def _build_youtube_jump_link(
    video_id: str | None,
    timestamp_start: float | None,
) -> str | None:
    """
    Build a safe YouTube jump link for a retrieved video segment.

    A link is returned only when both the video ID and start timestamp
    are available. The underlying metadata remains unchanged.
    """

    if video_id is None or timestamp_start is None:
        return None

    normalized_video_id = str(video_id).strip()

    if not normalized_video_id:
        return None

    seconds = max(
        0,
        int(timestamp_start),
    )

    encoded_video_id = quote(
        normalized_video_id,
        safe="-_",
    )

    return (
        "https://www.youtube.com/watch?v="
        f"{encoded_video_id}"
        f"&t={seconds}s"
    )


# ============================================================
# PHASE 14.1 — TIMESTAMP FORMATTING
# ============================================================


def _format_timestamp(
    value: float | None,
) -> str:
    """
    Format a timestamp as a human-readable video position.

    Examples
    --------
    0.0     -> "00:00"
    83.5    -> "01:23"
    3725.2  -> "01:02:05"

    ``None`` remains explicit as ``"unknown"`` so missing timestamp
    metadata is never silently converted into a misleading position.
    """

    if value is None:
        return "unknown"

    # Timestamps should represent positions in a video. Keep the existing
    # numeric value untouched in ContextItem and only change its display form.
    total_seconds = max(
        0,
        int(value),
    )

    hours, remainder = divmod(
        total_seconds,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


def _format_timestamp_range(
    start: float | None,
    end: float | None,
) -> str:
    """
    Format a timestamp range for deterministic context output.
    """

    return (
        f"{_format_timestamp(start)}"
        " -> "
        f"{_format_timestamp(end)}"
    )


# ============================================================
# TEXT EXTRACTION
# ============================================================


def _extract_text(
    result: Any,
) -> str:
    """
    Extract chunk text from the preferred semantic result.

    English translated text is preferred when available because
    the video-level summaries must be generated in English.

    BM25 document is used as fallback.
    """

    semantic_result = _get_value(
        result,
        "semantic_result",
    )

    bm25_document = _get_value(
        result,
        "bm25_document",
    )

    for source in (
        semantic_result,
        bm25_document,
        result,
    ):
        text = _get_nested_value(
            source,
            (
                "text_en",
                "text",
                "chunk_text",
                "content",
                "document",
            ),
        )

        if text is not None:
            text = str(text).strip()

            if text:
                return text

    return ""


# ============================================================
# METADATA EXTRACTION
# ============================================================


def _extract_metadata(
    result: Any,
) -> dict[str, Any]:
    """
    Extract application metadata from the result.
    """

    semantic_result = _get_value(
        result,
        "semantic_result",
    )

    bm25_document = _get_value(
        result,
        "bm25_document",
    )

    sources = (
        semantic_result,
        bm25_document,
        result,
    )

    video_id = None
    video_title = None
    pattern = None
    sub_pattern = None
    timestamp_start = None
    timestamp_end = None

    for source in sources:

        if video_id is None:
            video_id = _get_nested_value(
                source,
                (
                    "video_id",
                ),
            )

        if video_title is None:
            video_title = _get_nested_value(
                source,
                (
                    "video_title",
                    "title",
                ),
            )

        if pattern is None:
            pattern = _get_nested_value(
                source,
                (
                    "pattern",
                ),
            )

        if sub_pattern is None:
            sub_pattern = _get_nested_value(
                source,
                (
                    "sub_pattern",
                    "subpattern",
                ),
            )

        if timestamp_start is None:
            timestamp_start = _get_nested_value(
                source,
                (
                    "timestamp_start",
                    "start_time",
                    "start",
                ),
            )

        if timestamp_end is None:
            timestamp_end = _get_nested_value(
                source,
                (
                    "timestamp_end",
                    "end_time",
                    "end",
                ),
            )

    return {
        "video_id": (
            str(video_id)
            if video_id is not None
            else None
        ),
        "video_title": (
            str(video_title).strip()
            if video_title is not None
            and str(video_title).strip()
            else None
        ),
        "pattern": (
            str(pattern)
            if pattern is not None
            else None
        ),
        "sub_pattern": (
            str(sub_pattern)
            if sub_pattern is not None
            else None
        ),
        "timestamp_start": _to_float(
            timestamp_start
        ),
        "timestamp_end": _to_float(
            timestamp_end
        ),
    }


# ============================================================
# MAIN ASSEMBLY FUNCTION
# ============================================================


def assemble_context(
    *,
    query: str,
    results: Sequence[Any],
    pattern: str | None = None,
    sub_pattern: str | None = None,
    top_k: int = 5,
) -> AssembledContext:
    """
    Assemble final reranked retrieval results into structured context.
    """

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "query must be a string."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "query cannot be empty."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than 0."
        )

    if results is None:
        raise TypeError(
            "results cannot be None."
        )

    assembled_items: list[ContextItem] = []

    seen_point_ids: set[str] = set()

    for result in results:

        if len(assembled_items) >= top_k:
            break

        point_id = _get_value(
            result,
            "point_id",
        )

        if point_id is None:
            continue

        point_id = str(point_id).strip()

        if not point_id:
            continue

        if point_id in seen_point_ids:
            continue

        seen_point_ids.add(
            point_id
        )

        text = _extract_text(
            result
        )

        if not text:
            continue

        metadata = _extract_metadata(
            result
        )

        item_pattern = (
            metadata["pattern"]
            if metadata["pattern"] is not None
            else pattern
        )

        item_sub_pattern = (
            metadata["sub_pattern"]
            if metadata["sub_pattern"] is not None
            else sub_pattern
        )

        rrf_score = _get_value(
            result,
            "rrf_score",
        )

        reranker_score = _get_value(
            result,
            "reranker_score",
            "reranker",
        )

        assembled_items.append(
            ContextItem(
                rank=len(
                    assembled_items
                ) + 1,

                point_id=point_id,

                text=text,

                video_id=metadata[
                    "video_id"
                ],

                pattern=item_pattern,

                sub_pattern=item_sub_pattern,

                timestamp_start=metadata[
                    "timestamp_start"
                ],

                timestamp_end=metadata[
                    "timestamp_end"
                ],

                rrf_score=_to_float(
                    rrf_score
                ),

                reranker_score=_to_float(
                    reranker_score
                ),

                video_title=metadata[
                    "video_title"
                ],
            )
        )

    return AssembledContext(
        query=query,
        pattern=pattern,
        sub_pattern=sub_pattern,
        items=assembled_items,
    )


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================


def build_context(
    *,
    query: str,
    results: Sequence[Any],
    pattern: str | None = None,
    sub_pattern: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Convenience wrapper returning a dictionary.
    """

    context = assemble_context(
        query=query,
        results=results,
        pattern=pattern,
        sub_pattern=sub_pattern,
        top_k=top_k,
    )

    return context.to_dict()