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
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence


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
            sections.append(
                "\n".join(
                    [
                        f"[Context {item.rank}]",
                        f"Point ID: {item.point_id}",
                        f"Video ID: {item.video_id or 'unknown'}",
                        f"Pattern: {item.pattern or 'unknown'}",
                        f"Sub-pattern: {item.sub_pattern or 'unknown'}",
                        (
                            "Timestamp: "
                            f"{_format_timestamp(item.timestamp_start)}"
                            " -> "
                            f"{_format_timestamp(item.timestamp_end)}"
                        ),
                        "",
                        item.text,
                    ]
                )
            )

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


def _format_timestamp(
    value: float | None,
) -> str:
    """
    Format timestamps consistently for LLM context.
    """

    if value is None:
        return "unknown"

    return f"{value:.2f}s"


# ============================================================
# TEXT EXTRACTION
# ============================================================


def _extract_text(
    result: Any,
) -> str:
    """
    Extract chunk text from the preferred semantic result.

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

    Parameters
    ----------
    query:
        Original user query.

    results:
        Final reranked hybrid retrieval results.

    pattern:
        Optional DSA pattern.

    sub_pattern:
        Optional DSA sub-pattern.

    top_k:
        Maximum number of context items.

    Returns
    -------
    AssembledContext
        Structured context ready for downstream LLM generation.
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

        # ----------------------------------------------------
        # Stable ID deduplication
        # ----------------------------------------------------

        if point_id in seen_point_ids:
            continue

        seen_point_ids.add(
            point_id
        )

        # ----------------------------------------------------
        # Extract chunk text
        # ----------------------------------------------------

        text = _extract_text(
            result
        )

        if not text:
            continue

        # ----------------------------------------------------
        # Extract metadata
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Ranking metadata
        # ----------------------------------------------------

        rrf_score = _get_value(
            result,
            "rrf_score",
        )

        reranker_score = _get_value(
            result,
            "reranker_score",
            "reranker",
        )

        # ----------------------------------------------------
        # Build context item
        # ----------------------------------------------------

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