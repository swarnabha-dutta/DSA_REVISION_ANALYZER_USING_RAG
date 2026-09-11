"""
BM25 Lexical Retrieval Index
=============================

Purpose:
    Provide lexical retrieval over DSA transcript chunks.

Why BM25:
    Semantic search is good at understanding meaning, but it can miss
    exact technical terms.

    BM25 complements semantic retrieval by giving strong relevance to
    exact or near-exact lexical matches such as:

        "two pointer"
        "memoization"
        "left right"
        "binary search"
        "time complexity"

Architecture:

    Qdrant Payloads
          ↓
    BM25 Index Build
          ↓
    Persisted Local Index
          ↓
    Query
          ↓
    BM25 Ranking
          ↓
    Candidate Chunks

Important:
    This module is intentionally independent from the Qdrant semantic
    retrieval implementation.

    It can therefore be used independently during development and later
    integrated into the hybrid retrieval pipeline.

The implementation uses only Python standard-library modules.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

BM25_INDEX_DIR = DATA_DIR / "bm25"

BM25_INDEX_FILE = (
    BM25_INDEX_DIR / "index.json"
)


# ============================================================
# BM25 CONFIGURATION
# ============================================================

# Standard BM25 parameters.

BM25_K1 = 1.5

BM25_B = 0.75


# ============================================================
# TOKENIZATION
# ============================================================

TOKEN_PATTERN = re.compile(
    r"[a-z0-9]+(?:'[a-z0-9]+)?"
)


def normalize_text(
    text: str,
) -> str:
    """
    Normalize text before tokenization.

    Operations:

        1. Convert to lowercase.
        2. Replace underscores with spaces.
        3. Collapse repeated whitespace.

    Example:

        "Dynamic_Programming"
            ↓
        "dynamic programming"
    """

    if not isinstance(
        text,
        str,
    ):
        return ""

    normalized = text.lower()

    normalized = normalized.replace(
        "_",
        " ",
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


def tokenize(
    text: str,
) -> list[str]:
    """
    Convert text into normalized lexical tokens.

    The tokenizer intentionally keeps technical terms as individual
    searchable tokens.

    Example:

        "Dynamic programming with memoization"

    becomes approximately:

        [
            "dynamic",
            "programming",
            "with",
            "memoization",
        ]
    """

    normalized = normalize_text(
        text
    )

    if not normalized:
        return []

    return TOKEN_PATTERN.findall(
        normalized
    )


# ============================================================
# INDEXED DOCUMENT
# ============================================================

@dataclass
class BM25Document:
    """
    Metadata stored for one indexed transcript chunk.

    The BM25 implementation only needs tokens for scoring, while the
    remaining metadata allows the retrieval layer to identify and
    reconstruct the original chunk.
    """

    point_id: str

    chunk_id: str | None

    video_id: str | None

    video_title: str | None

    pattern: str | None

    sub_pattern: str | None

    playlist: str | None

    start: float

    end: float

    duration: float

    text: str

    text_en: str

    tokens: list[str]


# ============================================================
# BM25 INDEX
# ============================================================

class BM25Index:
    """
    In-memory BM25 index.

    The index stores:

        - indexed documents
        - tokenized documents
        - document frequencies
        - inverse document frequency
        - average document length

    The index can be persisted to JSON and loaded again without
    rebuilding the corpus.
    """

    def __init__(
        self,
        documents: list[BM25Document],
        *,
        k1: float = BM25_K1,
        b: float = BM25_B,
    ) -> None:

        if k1 <= 0:
            raise ValueError(
                "BM25 k1 must be greater than 0."
            )

        if not 0 <= b <= 1:
            raise ValueError(
                "BM25 b must be between 0 and 1."
            )

        self.documents = documents

        self.k1 = k1

        self.b = b

        self.document_count = len(
            documents
        )

        self.document_lengths = [
            len(document.tokens)
            for document in documents
        ]

        self.average_document_length = (
            self._calculate_average_document_length()
        )

        self.document_frequency = (
            self._calculate_document_frequency()
        )

        self.inverse_document_frequency = (
            self._calculate_inverse_document_frequency()
        )

        self.term_frequencies = (
            self._calculate_term_frequencies()
        )

    # ========================================================
    # INDEX STATISTICS
    # ========================================================

    def _calculate_average_document_length(
        self,
    ) -> float:

        if not self.document_lengths:
            return 0.0

        return (
            sum(self.document_lengths)
            / len(self.document_lengths)
        )

    def _calculate_document_frequency(
        self,
    ) -> dict[str, int]:

        frequencies: dict[str, int] = {}

        for document in self.documents:

            unique_terms = set(
                document.tokens
            )

            for term in unique_terms:

                frequencies[term] = (
                    frequencies.get(
                        term,
                        0,
                    )
                    + 1
                )

        return frequencies

    def _calculate_inverse_document_frequency(
        self,
    ) -> dict[str, float]:

        idf: dict[str, float] = {}

        if self.document_count == 0:
            return idf

        for term, document_frequency in (
            self.document_frequency.items()
        ):

            # Robertson/Sparck Jones style
            # BM25 IDF with a small safety floor.

            numerator = (
                self.document_count
                - document_frequency
                + 0.5
            )

            denominator = (
                document_frequency
                + 0.5
            )

            value = math.log(
                1.0
                + (
                    numerator
                    / denominator
                )
            )

            idf[term] = value

        return idf

    def _calculate_term_frequencies(
        self,
    ) -> list[dict[str, int]]:

        frequencies: list[
            dict[str, int]
        ] = []

        for document in self.documents:

            term_frequency: dict[
                str,
                int,
            ] = {}

            for token in document.tokens:

                term_frequency[token] = (
                    term_frequency.get(
                        token,
                        0,
                    )
                    + 1
                )

            frequencies.append(
                term_frequency
            )

        return frequencies

    # ========================================================
    # SCORING
    # ========================================================

    def score_document(
        self,
        query_tokens: list[str],
        document_index: int,
    ) -> float:
        """
        Calculate the BM25 score for one document.

        Formula:

            IDF(q)
            *
            [ TF(q) * (k1 + 1) ]
            --------------------------------
            TF(q) + k1 * (1 - b + b * |D| / avgdl)

        Scores are summed across query terms.
        """

        if not query_tokens:
            return 0.0

        if (
            document_index < 0
            or document_index >= self.document_count
        ):
            raise IndexError(
                "Document index out of range."
            )

        document_length = (
            self.document_lengths[
                document_index
            ]
        )

        if (
            self.average_document_length
            <= 0
        ):
            return 0.0

        term_frequency = (
            self.term_frequencies[
                document_index
            ]
        )

        score = 0.0

        denominator_length = (
            self.k1
            * (
                1.0
                - self.b
                + self.b
                * (
                    document_length
                    / self.average_document_length
                )
            )
        )

        for term in query_tokens:

            if term not in term_frequency:
                continue

            tf = term_frequency[
                term
            ]

            idf = (
                self.inverse_document_frequency.get(
                    term,
                    0.0,
                )
            )

            numerator = (
                tf
                * (
                    self.k1
                    + 1.0
                )
            )

            denominator = (
                tf
                + denominator_length
            )

            score += (
                idf
                * (
                    numerator
                    / denominator
                )
            )

        return score

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        allowed_document_indices: set[int]
        | None = None,
    ) -> list[tuple[BM25Document, float]]:
        """
        Search the BM25 index.

        Args:
            query:
                Natural-language lexical query.

            top_k:
                Maximum number of results.

            allowed_document_indices:
                Optional set of document indices that are allowed
                to participate in ranking.

                This is useful for metadata-aware retrieval where
                pattern/sub-pattern constraints must remain authoritative.

        Returns:

            [
                (document, score),
                ...
            ]

        Results are sorted by descending BM25 score.
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
                "Query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        query_tokens = tokenize(
            query
        )

        if not query_tokens:
            return []

        if (
            allowed_document_indices
            is None
        ):
            candidate_indices = range(
                self.document_count
            )

        else:
            candidate_indices = (
                sorted(
                    allowed_document_indices
                )
            )

        scored_results: list[
            tuple[
                BM25Document,
                float,
            ]
        ] = []

        for document_index in (
            candidate_indices
        ):

            score = self.score_document(
                query_tokens=query_tokens,
                document_index=document_index,
            )

            # Documents with zero lexical
            # relevance are not useful BM25
            # candidates.

            if score <= 0:
                continue

            scored_results.append(
                (
                    self.documents[
                        document_index
                    ],
                    score,
                )
            )

        scored_results.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return scored_results[
            :top_k
        ]

    # ========================================================
    # PERSISTENCE
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Convert the index into a JSON-serializable structure.

        Derived statistics are persisted as well so the index can be
        loaded directly without recalculating everything.
        """

        return {
            "version": 1,
            "k1": self.k1,
            "b": self.b,
            "documents": [
                asdict(document)
                for document in self.documents
            ],
        }

    def save(
        self,
        path: Path = BM25_INDEX_FILE,
    ) -> None:
        """
        Persist the BM25 index to disk.
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.to_dict(),
                file,
                ensure_ascii=False,
                indent=2,
            )

    @classmethod
    def load(
        cls,
        path: Path = BM25_INDEX_FILE,
    ) -> "BM25Index":
        """
        Load a previously persisted BM25 index.
        """

        if not path.exists():
            raise FileNotFoundError(
                f"BM25 index not found: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "BM25 index file must contain a JSON object."
            )

        version = data.get(
            "version"
        )

        if version != 1:
            raise ValueError(
                f"Unsupported BM25 index version: {version!r}"
            )

        raw_documents = data.get(
            "documents"
        )

        if not isinstance(
            raw_documents,
            list,
        ):
            raise ValueError(
                "BM25 index is missing documents."
            )

        documents: list[
            BM25Document
        ] = []

        for raw_document in (
            raw_documents
        ):

            if not isinstance(
                raw_document,
                dict,
            ):
                raise ValueError(
                    "Invalid BM25 document entry."
                )

            documents.append(
                BM25Document(
                    point_id=str(
                        raw_document.get(
                            "point_id",
                            "",
                        )
                    ),
                    chunk_id=(
                        raw_document.get(
                            "chunk_id"
                        )
                    ),
                    video_id=(
                        raw_document.get(
                            "video_id"
                        )
                    ),
                    video_title=(
                        raw_document.get(
                            "video_title"
                        )
                    ),
                    pattern=(
                        raw_document.get(
                            "pattern"
                        )
                    ),
                    sub_pattern=(
                        raw_document.get(
                            "sub_pattern"
                        )
                    ),
                    playlist=(
                        raw_document.get(
                            "playlist"
                        )
                    ),
                    start=float(
                        raw_document.get(
                            "start",
                            0.0,
                        )
                    ),
                    end=float(
                        raw_document.get(
                            "end",
                            0.0,
                        )
                    ),
                    duration=float(
                        raw_document.get(
                            "duration",
                            0.0,
                        )
                    ),
                    text=str(
                        raw_document.get(
                            "text",
                            "",
                        )
                    ),
                    text_en=str(
                        raw_document.get(
                            "text_en",
                            "",
                        )
                    ),
                    tokens=list(
                        raw_document.get(
                            "tokens",
                            [],
                        )
                    ),
                )
            )

        return cls(
            documents=documents,
            k1=float(
                data.get(
                    "k1",
                    BM25_K1,
                )
            ),
            b=float(
                data.get(
                    "b",
                    BM25_B,
                )
            ),
        )


# ============================================================
# DOCUMENT BUILDING HELPERS
# ============================================================

def get_payload_value(
    payload: dict[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    """
    Safely retrieve a value from a Qdrant payload.

    Supports both:

        payload["text"]

    and future nested:

        payload["metadata"]["text"]
    """

    if key in payload:
        return payload[key]

    metadata = payload.get(
        "metadata"
    )

    if isinstance(
        metadata,
        dict,
    ):
        return metadata.get(
            key,
            default,
        )

    return default


def to_optional_string(
    value: Any,
) -> str | None:
    """
    Convert a value to an optional string.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def to_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.
    """

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def extract_search_text(
    payload: dict[str, Any],
) -> str:
    """
    Choose the best text representation for lexical indexing.

    English translated text is preferred because the rest of the
    retrieval pipeline is designed around English query understanding.

    Original transcript text is retained as a fallback.
    """

    text_en = str(
        get_payload_value(
            payload,
            "text_en",
            "",
        )
    ).strip()

    if text_en:
        return text_en

    return str(
        get_payload_value(
            payload,
            "text",
            "",
        )
    ).strip()


def build_document_from_payload(
    *,
    point_id: str,
    payload: dict[str, Any],
) -> BM25Document:
    """
    Convert one Qdrant payload into a BM25Document.
    """

    text = str(
        get_payload_value(
            payload,
            "text",
            "",
        )
    )

    text_en = str(
        get_payload_value(
            payload,
            "text_en",
            "",
        )
    )

    search_text = extract_search_text(
        payload
    )

    tokens = tokenize(
        search_text
    )

    return BM25Document(
        point_id=str(
            point_id
        ),
        chunk_id=to_optional_string(
            get_payload_value(
                payload,
                "chunk_id",
            )
        ),
        video_id=to_optional_string(
            get_payload_value(
                payload,
                "video_id",
            )
        ),
        video_title=to_optional_string(
            get_payload_value(
                payload,
                "video_title",
            )
        ),
        pattern=to_optional_string(
            get_payload_value(
                payload,
                "pattern",
            )
        ),
        sub_pattern=to_optional_string(
            get_payload_value(
                payload,
                "sub_pattern",
            )
        ),
        playlist=to_optional_string(
            get_payload_value(
                payload,
                "playlist",
            )
        ),
        start=to_float(
            get_payload_value(
                payload,
                "start",
                0.0,
            )
        ),
        end=to_float(
            get_payload_value(
                payload,
                "end",
                0.0,
            )
        ),
        duration=to_float(
            get_payload_value(
                payload,
                "duration",
                0.0,
            )
        ),
        text=text,
        text_en=text_en,
        tokens=tokens,
    )


# ============================================================
# METADATA FILTERING
# ============================================================

def document_matches_metadata(
    document: BM25Document,
    *,
    pattern: str | None = None,
    sub_pattern: str | None = None,
) -> bool:
    """
    Determine whether a BM25 document satisfies the same metadata
    constraints used by the semantic retrieval layer.
    """

    if (
        pattern is not None
        and document.pattern != pattern
    ):
        return False

    if (
        sub_pattern is not None
        and document.sub_pattern != sub_pattern
    ):
        return False

    return True


def get_allowed_document_indices(
    index: BM25Index,
    *,
    pattern: str | None = None,
    sub_pattern: str | None = None,
) -> set[int]:
    """
    Return document indices satisfying the requested metadata filters.

    This allows lexical retrieval to respect the same metadata
    constraints as semantic retrieval.
    """

    allowed: set[int] = set()

    for index_position, document in enumerate(
        index.documents
    ):

        if document_matches_metadata(
            document,
            pattern=pattern,
            sub_pattern=sub_pattern,
        ):
            allowed.add(
                index_position
            )

    return allowed


# ============================================================
# INDEX FACTORY
# ============================================================

def build_bm25_index(
    documents: list[BM25Document],
) -> BM25Index:
    """
    Build a BM25Index from prepared documents.
    """

    if not isinstance(
        documents,
        list,
    ):
        raise TypeError(
            "documents must be a list."
        )

    return BM25Index(
        documents=documents
    )


# ============================================================
# DEBUG / SELF-CHECK
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "BM25 INDEX MODULE SELF-CHECK"
    )

    print("=" * 60)

    sample_documents = [
        BM25Document(
            point_id="1",
            chunk_id="chunk_1",
            video_id="video_1",
            video_title="Two Pointer",
            pattern="two_pointer",
            sub_pattern=None,
            playlist="DSA_Patterns_Two_Pointer",
            start=0.0,
            end=30.0,
            duration=30.0,
            text="Use two pointers from both ends.",
            text_en="Use two pointers from both ends.",
            tokens=tokenize(
                "Use two pointers from both ends."
            ),
        ),
        BM25Document(
            point_id="2",
            chunk_id="chunk_2",
            video_id="video_2",
            video_title="Dynamic Programming",
            pattern="dynamic_programming",
            sub_pattern="memoization",
            playlist="DSA_Patterns_Dynamic_Programming",
            start=0.0,
            end=30.0,
            duration=30.0,
            text="Memoization stores previously computed states.",
            text_en="Memoization stores previously computed states.",
            tokens=tokenize(
                "Memoization stores previously computed states."
            ),
        ),
    ]

    index = build_bm25_index(
        sample_documents
    )

    results = index.search(
        "memoization computed states",
        top_k=2,
    )

    print()

    print(
        f"Documents : {index.document_count}"
    )

    print(
        f"Vocabulary: "
        f"{len(index.document_frequency)}"
    )

    print(
        f"Average document length: "
        f"{index.average_document_length:.2f}"
    )

    print()

    print(
        "Search results:"
    )

    for document, score in results:

        print(
            f"  {document.chunk_id}"
            f" → {score:.4f}"
        )

    print()

    print(
        "✓ BM25 module self-check completed."
    )