"""
DSA Query Understanding Service

This module converts a natural-language DSA query into
structured metadata that can be consumed by the retrieval layer.

Pipeline:

    User Query
        ↓
    Intent Detection
        ↓
    Pattern Detection
        ↓
    Sub-pattern Detection
        ↓
    Confidence
        ↓
    QueryAnalysis

The service is taxonomy-driven.

Only canonical patterns and sub-patterns defined in
dsa_taxonomy.py are returned.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.dsa_taxonomy import (
    DSA_PATTERN_TAXONOMY,
)


# ============================================================
# CANONICAL TAXONOMY HELPERS
# ============================================================


VALID_PATTERNS: tuple[str, ...] = tuple(
    DSA_PATTERN_TAXONOMY.keys()
)


# ============================================================
# QUERY ANALYSIS MODEL
# ============================================================


@dataclass(frozen=True)
class QueryAnalysis:
    """
    Structured representation of a user's DSA query.

    Attributes:
        query:
            Original user query.

        intent:
            Detected user intent.

        pattern:
            Canonical DSA pattern, if detected.

        sub_pattern:
            Canonical sub-pattern, if detected.

        confidence:
            Lightweight heuristic confidence score.
    """

    query: str
    intent: str
    pattern: str | None
    sub_pattern: str | None
    confidence: float


# ============================================================
# QUERY NORMALIZATION
# ============================================================


def normalize_query(query: str) -> str:
    """
    Normalize a natural-language query.

    Operations:

        1. Convert to lowercase.
        2. Replace underscores with spaces.
        3. Remove unnecessary punctuation.
        4. Collapse repeated whitespace.

    Example:

        "Two_Pointer!!!"

    becomes:

        "two pointer"
    """

    normalized = query.lower()

    normalized = normalized.replace(
        "_",
        " ",
    )

    normalized = re.sub(
        r"[^a-z0-9\s+#-]",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


# ============================================================
# INTENT DETECTION
# ============================================================


INTENT_PATTERNS: dict[str, tuple[str, ...]] = {
    "optimization": (
        "optimize",
        "optimization",
        "optimise",
        "optimisation",
        "improve",
        "make it faster",
        "reduce time",
        "reduce space",
        "space optimize",
        "time optimize",
        "more efficient",
        "make this efficient",
    ),
    "complexity": (
        "time complexity",
        "space complexity",
        "complexity",
        "big o",
        "big-o",
        "runtime",
        "time and space",
    ),
    "practice": (
        "practice",
        "problem",
        "problems",
        "question",
        "questions",
        "practice problem",
        "practice problems",
        "give me problems",
        "give problems",
        "leetcode",
        "solve",
    ),
    "comparison": (
        "difference between",
        "compare",
        "comparison",
        "versus",
        "vs",
        "which is better",
    ),
    "implementation": (
        "implement",
        "implementation",
        "code",
        "coding",
        "write code",
        "how to code",
        "memoization",
        "tabulation",
    ),
    "how_it_works": (
        "how does",
        "how do",
        "how is",
        "how are",
        "how it works",
        "how this works",
        "working of",
        "works",
    ),
    "explanation": (
        "what is",
        "what are",
        "explain",
        "explanation",
        "meaning",
        "define",
        "definition",
    ),
}


# Explicit high-priority intents.

# Some queries contain multiple intent signals.
#
# Example:
#
#   "How do I optimize a recursive solution?"
#
# contains both:
#
#   "how do"  -> how_it_works
#   "optimize" -> optimization
#
# The explicit optimization signal should win because it
# expresses the user's actual objective.
INTENT_PRIORITY: tuple[str, ...] = (
    "optimization",
    "complexity",
    "practice",
    "comparison",
    "implementation",
    "how_it_works",
    "explanation",
)


def _phrase_matches(
    phrase: str,
    normalized_query: str,
) -> bool:
    """
    Match a phrase as a complete token sequence.

    This prevents accidental substring matches such as:

        "heap" matching "heapsort"

    while still allowing:

        "heap" to match "explain heap"
    """

    phrase_normalized = normalize_query(phrase)

    if not phrase_normalized:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(phrase_normalized)
        + r"(?![a-z0-9])"
    )

    return re.search(
        pattern,
        normalized_query,
    ) is not None


def detect_intent(
    query: str,
) -> tuple[str, float]:
    """
    Detect the most likely user intent.

    Returns:

        (intent, confidence)

    Confidence is heuristic and should not be treated
    as a statistical probability.

    Explicit high-priority intent signals are resolved
    before generic phrases such as "how do".
    """

    normalized = normalize_query(query)

    if not normalized:
        return (
            "general",
            0.0,
        )

    candidates: list[tuple[str, int]] = []

    for intent, phrases in INTENT_PATTERNS.items():

        score = 0

        for phrase in phrases:

            if _phrase_matches(
                phrase,
                normalized,
            ):
                # Longer phrases provide stronger evidence.
                score += max(
                    1,
                    len(
                        phrase.split()
                    ),
                )

        if score > 0:

            candidates.append(
                (
                    intent,
                    score,
                )
            )

    if not candidates:

        return (
            "general",
            0.0,
        )

    # --------------------------------------------------------
    # Explicit priority handling
    # --------------------------------------------------------
    #
    # If an explicit optimization signal exists, it should
    # override generic "how do" language.
    #
    # Example:
    #
    #   "How do I optimize a recursive solution?"
    #
    # -> optimization
    #
    # rather than:
    #
    # -> how_it_works
    # --------------------------------------------------------

    for priority_intent in INTENT_PRIORITY:

        for candidate_intent, candidate_score in candidates:

            if candidate_intent == priority_intent:

                # Strong explicit signals get high confidence.
                if priority_intent in {
                    "optimization",
                    "complexity",
                    "practice",
                    "comparison",
                }:
                    return (
                        priority_intent,
                        0.99,
                    )

                break

    # --------------------------------------------------------
    # Fallback score-based selection
    # --------------------------------------------------------

    priority_index = {
        intent: index
        for index, intent in enumerate(
            INTENT_PRIORITY
        )
    }

    candidates.sort(
        key=lambda item: (
            item[1],
            -priority_index.get(
                item[0],
                999,
            ),
        ),
        reverse=True,
    )

    best_intent, best_score = candidates[0]

    if best_score >= 3:

        confidence = 0.99

    elif best_score == 2:

        confidence = 0.90

    else:

        confidence = 0.75

    return (
        best_intent,
        confidence,
    )


# ============================================================
# PATTERN ALIAS DEFINITIONS
# ============================================================

# These aliases are intentionally kept inside this module.
#
# dsa_taxonomy.py remains the source of truth for the
# canonical pattern list and sub-pattern structure.
#
# The aliases below only help natural-language queries map
# to the canonical taxonomy.
#
# IMPORTANT:
#
# An alias can NEVER create a new pattern.
# get_valid_aliases() checks the canonical taxonomy first.
# ============================================================


PATTERN_ALIASES: dict[str, tuple[str, ...]] = {

    "two_pointer": (
        "two pointer",
        "two pointers",
        "2 pointer",
        "2 pointers",
    ),

    "sliding_window": (
        "sliding window",
        "window technique",
        "window approach",
    ),

    "binary_search": (
        "binary search",
        "binary searching",
    ),

    "dynamic_programming": (
        "dynamic programming",
        "dynamic programming dp",
        "dp",
    ),

    "divide_and_conquer": (
        "divide and conquer",
        "divide conquer",
    ),

    "greedy": (
        "greedy",
        "greedy algorithm",
        "greedy algorithms",
    ),

    "backtracking": (
        "backtracking",
        "backtracking algorithm",
    ),

    "graph_traversal": (
        "graph traversal",
        "graph traversal algorithm",
    ),

    "shortest_path": (
        "shortest path",
        "shortest paths",
    ),

    "minimum_spanning_tree": (
        "minimum spanning tree",
        "minimum spanning trees",
        "mst",
    ),

    "topological_sorting": (
        "topological sort",
        "topological sorting",
        "topo sort",
    ),

    "union_find": (
        "union find",
        "disjoint set",
        "disjoint sets",
        "dsu",
    ),

    "heap_priority_queue": (
        "heap",
        "heaps",
        "priority queue",
        "priority queues",
    ),

    "monotonic_stack": (
        "monotonic stack",
        "monotonic stacks",
    ),

    "trie": (
        "trie",
        "tries",
        "prefix tree",
    ),

    "bit_manipulation": (
        "bit manipulation",
        "bitwise",
        "bit operations",
        "bit operation",
    ),

    "prefix_sum": (
        "prefix sum",
        "prefix sums",
        "cumulative sum",
    ),

    "difference_array": (
        "difference array",
        "difference arrays",
    ),

    "sorting": (
        "sorting",
        "sort",
        "sorting algorithm",
        "sorting algorithms",
    ),

    "divide_and_conquer_sorting": (
        "divide and conquer sorting",
    ),

    "hashing": (
        "hashing",
        "hash table",
        "hash tables",
        "hash map",
        "hash maps",
    ),

    "linked_list": (
        "linked list",
        "linked lists",
    ),

    "tree": (
        "tree",
        "trees",
        "binary tree",
        "binary trees",
    ),

    "segment_tree": (
        "segment tree",
        "segment trees",
    ),

    "fenwick_tree": (
        "fenwick tree",
        "fenwick trees",
        "binary indexed tree",
        "binary indexed trees",
        "bit tree",
    ),
}


# ============================================================
# UNSUPPORTED ALGORITHM GUARD
# ============================================================

# These are algorithm names that are intentionally NOT
# canonical patterns in the current project taxonomy.
#
# They must not accidentally map to a broader canonical
# pattern just because one word overlaps.
#
# Examples:
#
#   "merge sort"  -> no pattern
#   "bubble sort" -> no pattern
#   "heap sort"   -> no pattern
#
# This is important because the project is playlist-driven.
# We must not invent a playlist/category that does not exist
# in the canonical taxonomy.
# ============================================================


UNSUPPORTED_ALGORITHM_PHRASES: tuple[str, ...] = (
    "merge sort",
    "bubble sort",
    "insertion sort",
    "selection sort",
    "quick sort",
    "radix sort",
    "heap sort",
    "counting sort",
)


def is_unsupported_algorithm_query(
    query: str,
) -> bool:
    """
    Return True when the query explicitly targets an
    algorithm that is not part of the current canonical
    DSA taxonomy.
    """

    normalized = normalize_query(query)

    return any(
        _phrase_matches(
            phrase,
            normalized,
        )
        for phrase in UNSUPPORTED_ALGORITHM_PHRASES
    )


# ============================================================
# PATTERN ALIAS VALIDATION
# ============================================================


def get_valid_aliases(
    pattern: str,
) -> tuple[str, ...]:
    """
    Return aliases for a pattern only if that pattern
    actually exists in the canonical taxonomy.

    This prevents aliases from introducing patterns that
    are not part of the project's canonical taxonomy.
    """

    if pattern not in DSA_PATTERN_TAXONOMY:

        return ()

    return PATTERN_ALIASES.get(
        pattern,
        (),
    )


# ============================================================
# PATTERN DETECTION
# ============================================================


def detect_pattern(
    query: str,
) -> tuple[str | None, float]:
    """
    Detect the most likely canonical DSA pattern.

    Matching sources:

        1. Canonical pattern slug.
        2. Human-readable label.
        3. Natural-language aliases.
        4. Canonical sub-pattern names.

    Only patterns present in dsa_taxonomy.py are returned.

    Unsupported algorithm queries are deliberately excluded
    to prevent false classifications.
    """

    normalized = normalize_query(query)

    # --------------------------------------------------------
    # Do not invent patterns for unsupported algorithms.
    # --------------------------------------------------------

    if is_unsupported_algorithm_query(
        normalized
    ):

        return (
            None,
            0.0,
        )

    candidates: list[tuple[str, int]] = []

    for pattern in VALID_PATTERNS:

        pattern_data = DSA_PATTERN_TAXONOMY[
            pattern
        ]

        score = 0

        # ----------------------------------------------------
        # Canonical pattern slug
        # ----------------------------------------------------

        readable_pattern = pattern.replace(
            "_",
            " ",
        )

        if _phrase_matches(
            readable_pattern,
            normalized,
        ):

            score += 5

        # ----------------------------------------------------
        # Human-readable label
        # ----------------------------------------------------

        label = str(
            pattern_data.get(
                "label",
                "",
            )
        ).lower()

        if (
            label
            and _phrase_matches(
                label,
                normalized,
            )
        ):

            score += 6

        # ----------------------------------------------------
        # Natural-language aliases
        # ----------------------------------------------------

        for alias in get_valid_aliases(
            pattern
        ):

            if _phrase_matches(
                alias,
                normalized,
            ):

                score += 10

        # ----------------------------------------------------
        # Sub-pattern matching
        # ----------------------------------------------------

        sub_patterns = pattern_data.get(
            "sub_patterns",
            (),
        )

        for sub_pattern in sub_patterns:

            readable_sub_pattern = (
                sub_pattern.replace(
                    "_",
                    " ",
                )
            )

            if _phrase_matches(
                readable_sub_pattern,
                normalized,
            ):

                score += 7

        if score > 0:

            candidates.append(
                (
                    pattern,
                    score,
                )
            )

    if not candidates:

        return (
            None,
            0.0,
        )

    candidates.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    best_pattern, best_score = candidates[0]

    confidence = min(
        0.99,
        0.50 + (
            best_score * 0.05
        ),
    )

    return (
        best_pattern,
        round(
            confidence,
            2,
        ),
    )


# ============================================================
# SUB-PATTERN DETECTION
# ============================================================


def detect_sub_pattern(
    query: str,
    pattern: str | None,
) -> str | None:
    """
    Detect a sub-pattern belonging to the already detected
    canonical parent pattern.

    If no valid parent pattern is detected, None is returned.
    """

    if pattern is None:

        return None

    normalized = normalize_query(query)

    pattern_data = (
        DSA_PATTERN_TAXONOMY.get(
            pattern
        )
    )

    if pattern_data is None:

        return None

    sub_patterns = pattern_data.get(
        "sub_patterns",
        (),
    )

    matches: list[tuple[str, int]] = []

    for sub_pattern in sub_patterns:

        readable = sub_pattern.replace(
            "_",
            " ",
        )

        score = 0

        if _phrase_matches(
            readable,
            normalized,
        ):

            score += 5

        if _phrase_matches(
            sub_pattern,
            normalized,
        ):

            score += 2

        if score > 0:

            matches.append(
                (
                    sub_pattern,
                    score,
                )
            )

    if not matches:

        return None

    matches.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return matches[0][0]


# ============================================================
# OVERALL QUERY ANALYSIS
# ============================================================


def understand_query(
    query: str,
) -> QueryAnalysis:
    """
    Run the complete query-understanding pipeline.

    Steps:

        1. Detect intent.
        2. Detect canonical pattern.
        3. Detect canonical sub-pattern.
        4. Calculate final confidence.
    """

    if not query or not query.strip():

        return QueryAnalysis(
            query=query,
            intent="general",
            pattern=None,
            sub_pattern=None,
            confidence=0.0,
        )

    intent, intent_confidence = (
        detect_intent(query)
    )

    pattern, pattern_confidence = (
        detect_pattern(query)
    )

    sub_pattern = detect_sub_pattern(
        query,
        pattern,
    )

    # --------------------------------------------------------
    # Confidence calculation
    # --------------------------------------------------------

    if pattern is None:

        confidence = intent_confidence

    else:

        confidence = max(
            intent_confidence,
            pattern_confidence,
        )

    if sub_pattern is not None:

        confidence = min(
            0.99,
            confidence + 0.03,
        )

    return QueryAnalysis(
        query=query,
        intent=intent,
        pattern=pattern,
        sub_pattern=sub_pattern,
        confidence=round(
            confidence,
            2,
        ),
    )


# ============================================================
# PUBLIC ANALYSIS ALIAS
# ============================================================


def analyze_query(
    query: str,
) -> QueryAnalysis:
    """
    Public compatibility wrapper.

    External scripts can call:

        analyze_query(query)

    while the core implementation remains:

        understand_query(query)
    """

    return understand_query(
        query
    )


# ============================================================
# SELF-CHECK
# ============================================================


SELF_CHECK_QUERIES = [
    (
        "How does two pointer work?",
        "how_it_works",
        "two_pointer",
        None,
    ),
    (
        "Explain dynamic programming memoization",
        "implementation",
        "dynamic_programming",
        "memoization",
    ),
    (
        "How do I optimize a recursive solution?",
        "optimization",
        None,
        None,
    ),
    (
        "What is binary search?",
        "explanation",
        "binary_search",
        None,
    ),
    (
        # IMPORTANT:
        # Merge sort is NOT a canonical playlist pattern
        # in the current project taxonomy.
        #
        # Therefore we only expect the intent here.
        "What is the time complexity of merge sort?",
        "complexity",
        None,
        None,
    ),
    (
        "Give me problems on sliding window",
        "practice",
        "sliding_window",
        None,
    ),
    (
        "Difference between recursion and dynamic programming",
        "comparison",
        "dynamic_programming",
        None,
    ),
]


# ============================================================
# NEGATIVE SELF-CHECKS
# ============================================================


NEGATIVE_CHECK_QUERIES = (
    "Explain merge sort",
    "Explain bubble sort",
    "Explain insertion sort",
    "Explain selection sort",
    "Explain quick sort",
    "Explain radix sort",
    "Explain heap sort",
)


def run_self_check() -> None:
    """
    Run deterministic query-understanding tests.
    """

    print("=" * 60)
    print(
        "QUERY UNDERSTANDING SELF-CHECK"
    )
    print("=" * 60)

    passed = 0
    failed = 0

    # --------------------------------------------------------
    # Positive / expected classification checks
    # --------------------------------------------------------

    for (
        query,
        expected_intent,
        expected_pattern,
        expected_sub_pattern,
    ) in SELF_CHECK_QUERIES:

        result = understand_query(
            query
        )

        print()
        print(
            f"Query       : {query}"
        )

        print(
            f"Intent      : {result.intent}"
        )

        print(
            f"Pattern     : {result.pattern}"
        )

        print(
            f"Sub-pattern : {result.sub_pattern}"
        )

        print(
            f"Confidence  : {result.confidence}"
        )

        intent_ok = (
            result.intent
            == expected_intent
        )

        pattern_ok = (
            result.pattern
            == expected_pattern
        )

        sub_pattern_ok = (
            result.sub_pattern
            == expected_sub_pattern
        )

        if (
            intent_ok
            and pattern_ok
            and sub_pattern_ok
        ):

            print(
                "✓ PASS"
            )

            passed += 1

        else:

            print(
                "✗ FAIL"
            )

            print(
                f"  Expected intent      : "
                f"{expected_intent}"
            )

            print(
                f"  Expected pattern     : "
                f"{expected_pattern}"
            )

            print(
                f"  Expected sub-pattern : "
                f"{expected_sub_pattern}"
            )

            failed += 1

    # --------------------------------------------------------
    # Negative checks
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "NEGATIVE SELF-CHECKS"
    )
    print("=" * 60)

    for query in NEGATIVE_CHECK_QUERIES:

        result = understand_query(
            query
        )

        print()
        print(
            f"Query       : {query}"
        )

        print(
            f"Pattern     : {result.pattern}"
        )

        print(
            f"Sub-pattern : {result.sub_pattern}"
        )

        if (
            result.pattern is None
            and result.sub_pattern is None
        ):

            print(
                "✓ PASS - No unsupported pattern generated"
            )

            passed += 1

        else:

            print(
                "✗ FAIL - Unexpected classification"
            )

            failed += 1

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "SELF-CHECK SUMMARY"
    )
    print("=" * 60)

    print(
        f"Passed : {passed}"
    )

    print(
        f"Failed : {failed}"
    )

    if failed == 0:

        print(
            "✓ Self-check completed successfully."
        )

    else:

        print(
            "✗ Self-check completed with failures."
        )


# ============================================================
# MODULE ENTRY POINT
# ============================================================


if __name__ == "__main__":

    run_self_check()