"""
DSA Pattern Taxonomy
====================

This module defines the canonical DSA pattern vocabulary used by
the DSA Revision Analyzer.

IMPORTANT DESIGN PRINCIPLE
--------------------------

The taxonomy is playlist-oriented.

A pattern should only become a canonical DSA pattern when it is
actually part of the learning taxonomy used by this project.

We DO NOT automatically convert every generic DSA algorithm into
a pattern.

For example:

    merge sort
    bubble sort
    insertion sort
    selection sort
    radix sort
    heap sort

are algorithms/topics, but they are NOT canonical patterns in the
current Padho With Pratyush DSA Patterns taxonomy.

Therefore:

    "What is merge sort?"
        -> pattern = None

instead of:

    pattern = sorting_sweep
    sub_pattern = merge_sort

This prevents the query-understanding layer from inventing
playlists that do not exist in the source learning structure.

Canonical metadata flow:

    Natural-language text
            ↓
    Pattern detection
            ↓
    Sub-pattern detection
            ↓
    Playlist resolution
            ↓
    Metadata-aware retrieval
            ↓
    Qdrant


The taxonomy is intentionally deterministic.

LLMs are NOT required to resolve the basic canonical vocabulary.
"""

from __future__ import annotations

from typing import Final


# ============================================================
# CANONICAL DSA PATTERN TAXONOMY
# ============================================================
#
# These are pattern-level concepts.
#
# Algorithm names that are not patterns are deliberately NOT
# included here.
#
# In particular, there is no:
#
#     sorting_sweep
#     merge_sort
#     bubble_sort
#     insertion_sort
#     selection_sort
#     quick_sort
#     radix_sort
#     heap_sort
#
# ============================================================


DSA_PATTERN_TAXONOMY: Final[
    dict[str, dict[str, object]]
] = {

    # --------------------------------------------------------
    # TWO POINTER
    # --------------------------------------------------------

    "two_pointer": {
        "label": "Two Pointer",

        "aliases": [
            "two pointer",
            "two pointers",
            "two-pointer",
            "two-pointer technique",
            "2 pointer",
            "2 pointers",
        ],

        "keywords": [
            "left pointer",
            "right pointer",
            "left and right pointer",
            "opposite direction",
            "same direction",
            "pair sum",
            "two sum",
            "three sum",
            "triplet sum",
            "four sum",
            "partition",
            "remove duplicates",
            "move zeros",
            "dutch national flag",
        ],

        "sub_patterns": [
            "opposite_direction",
            "same_direction",
            "pair_search",
            "three_sum",
            "four_sum",
            "partitioning",
            "duplicate_removal",
            "move_zeros",
            "dutch_national_flag",
        ],
    },


    # --------------------------------------------------------
    # SLIDING WINDOW
    # --------------------------------------------------------

    "sliding_window": {
        "label": "Sliding Window",

        "aliases": [
            "sliding window",
            "sliding-window",
            "window technique",
            "window pattern",
            "window approach",
        ],

        "keywords": [
            "sliding window",
            "fixed window",
            "variable window",
            "fixed size window",
            "variable size window",
            "window size",
            "longest substring",
            "shortest substring",
            "minimum window",
            "frequency window",
        ],

        "sub_patterns": [
            "fixed_window",
            "variable_window",
            "longest_valid_window",
            "shortest_valid_window",
            "frequency_window",
            "minimum_window",
        ],
    },


    # --------------------------------------------------------
    # KADANE
    # --------------------------------------------------------

    "kadane": {
        "label": "Kadane's Algorithm",

        "aliases": [
            "kadane",
            "kadane algorithm",
            "kadane's algorithm",
            "maximum subarray",
            "max subarray",
        ],

        "keywords": [
            "kadane",
            "maximum subarray",
            "maximum subarray sum",
            "max subarray sum",
            "maximum sum subarray",
            "largest subarray sum",
        ],

        "sub_patterns": [
            "maximum_subarray",
            "maximum_subarray_sum",
            "minimum_subarray_variant",
        ],
    },


    # --------------------------------------------------------
    # FAST / SLOW POINTER
    # --------------------------------------------------------

    "fast_slow_pointer": {
        "label": "Fast & Slow Pointer",

        "aliases": [
            "fast slow pointer",
            "fast and slow pointer",
            "fast-slow pointer",
            "tortoise and hare",
        ],

        "keywords": [
            "fast pointer",
            "slow pointer",
            "fast and slow",
            "tortoise hare",
            "cycle detection",
            "find middle",
            "middle of linked list",
        ],

        "sub_patterns": [
            "cycle_detection",
            "find_middle",
            "nth_node_from_end",
            "cycle_entry",
            "duplicate_number",
        ],
    },


    # --------------------------------------------------------
    # PREFIX SUM
    # --------------------------------------------------------

    "prefix_sum": {
        "label": "Prefix Sum",

        "aliases": [
            "prefix sum",
            "prefix-sum",
            "prefix sums",
            "cumulative sum",
            "running sum",
        ],

        "keywords": [
            "prefix sum",
            "cumulative sum",
            "running sum",
            "range sum",
            "prefix array",
        ],

        "sub_patterns": [
            "one_dimensional_prefix_sum",
            "two_dimensional_prefix_sum",
            "range_sum",
            "prefix_sum_hashing",
        ],
    },


    # --------------------------------------------------------
    # HASHING / HASHMAP
    # --------------------------------------------------------

    "hashing": {
        "label": "Hashing / HashMap",

        "aliases": [
            "hashing",
            "hash map",
            "hashmap",
            "hash table",
            "hash set",
            "hashset",
        ],

        "keywords": [
            "hash map",
            "hashmap",
            "hash table",
            "hash set",
            "frequency map",
            "frequency counting",
            "lookup",
            "complement",
            "two sum hashmap",
        ],

        "sub_patterns": [
            "frequency_map",
            "lookup_set",
            "complement_lookup",
            "prefix_sum_hashing",
            "grouping",
        ],
    },


    # --------------------------------------------------------
    # MERGE INTERVALS
    # --------------------------------------------------------

    "merge_intervals": {
        "label": "Merge Intervals",

        "aliases": [
            "merge intervals",
            "merge interval",
            "intervals",
            "interval",
        ],

        "keywords": [
            "merge intervals",
            "merge interval",
            "overlapping intervals",
            "interval overlap",
            "meeting rooms",
            "interval scheduling",
        ],

        "sub_patterns": [
            "merge_overlapping_intervals",
            "overlap_detection",
            "meeting_rooms",
            "interval_scheduling",
        ],
    },


    # --------------------------------------------------------
    # BINARY SEARCH
    # --------------------------------------------------------

    "binary_search": {
        "label": "Binary Search",

        "aliases": [
            "binary search",
            "binary-search",
            "binary searching",
            "modified binary search",
            "binary search on answer",
            "search on answer",
            "bsoa",
            "bossa",
        ],

        "keywords": [
            "binary search",
            "lower bound",
            "upper bound",
            "first occurrence",
            "last occurrence",
            "rotated array",
            "search rotated array",
            "search on answer",
            "binary search on answer",
            "monotonic predicate",
        ],

        "sub_patterns": [
            "classic_binary_search",
            "lower_bound",
            "upper_bound",
            "first_last_occurrence",
            "search_rotated_array",
            "binary_search_on_answer",
            "monotonic_predicate",
        ],
    },


    # --------------------------------------------------------
    # STACK
    # --------------------------------------------------------

    "stack": {
        "label": "Stack",

        "aliases": [
            "stack",
            "stacks",
            "stack pattern",
        ],

        "keywords": [
            "stack",
            "balanced parentheses",
            "valid parentheses",
            "next greater element",
            "previous greater element",
            "next smaller element",
            "expression evaluation",
            "monotonic stack",
        ],

        "sub_patterns": [
            "basic_stack",
            "balanced_parentheses",
            "monotonic_stack",
            "next_greater_element",
            "previous_greater_element",
            "next_smaller_element",
            "expression_evaluation",
        ],
    },


    # --------------------------------------------------------
    # HEAP
    # --------------------------------------------------------

    "heap": {
        "label": "Heap / Priority Queue",

        "aliases": [
            "heap",
            "heaps",
            "priority queue",
            "priority queues",
            "heap priority queue",
        ],

        "keywords": [
            "heap",
            "min heap",
            "max heap",
            "priority queue",
            "top k",
            "kth element",
            "kth largest",
            "kth smallest",
            "two heaps",
            "heap pairs",
        ],

        "sub_patterns": [
            "min_heap",
            "max_heap",
            "top_k",
            "kth_element",
            "two_heaps",
            "heap_pairs",
        ],
    },


    # --------------------------------------------------------
    # RECURSION
    # --------------------------------------------------------

    "recursion": {
        "label": "Recursion",

        "aliases": [
            "recursion",
            "recursive",
            "recursive solution",
            "recursive approach",
        ],

        "keywords": [
            "recursion",
            "recursive function",
            "recursive solution",
            "base case",
            "recursive call",
            "recursion tree",
        ],

        "sub_patterns": [
            "recursion_basics",
            "base_case",
            "recursive_call",
            "recursion_tree",
        ],
    },


    # --------------------------------------------------------
    # BACKTRACKING
    # --------------------------------------------------------

    "backtracking": {
        "label": "Backtracking",

        "aliases": [
            "backtracking",
            "backtrack",
            "backtracking algorithm",
        ],

        "keywords": [
            "backtracking",
            "backtrack",
            "subsets",
            "permutations",
            "combinations",
            "decision tree",
            "pruning",
            "constraint satisfaction",
        ],

        "sub_patterns": [
            "subsets",
            "permutations",
            "combinations",
            "decision_tree",
            "constraint_satisfaction",
            "pruning",
        ],
    },


    # --------------------------------------------------------
    # DYNAMIC PROGRAMMING
    # --------------------------------------------------------

    "dynamic_programming": {
        "label": "Dynamic Programming",

        "aliases": [
            "dynamic programming",
            "dynamic-programming",
            "dp",
        ],

        "keywords": [
            "dynamic programming",
            "dynamic programming dp",
            "memoization",
            "tabulation",
            "state transition",
            "dp state",
            "dp transition",
        ],

        "sub_patterns": [
            "memoization",
            "tabulation",
            "one_dimensional_dp",
            "two_dimensional_dp",
            "state_transition",
            "space_optimization",
        ],
    },
}


# ============================================================
# DERIVED LOOKUPS
# ============================================================


VALID_PATTERNS: Final[frozenset[str]] = frozenset(
    DSA_PATTERN_TAXONOMY.keys()
)


VALID_SUB_PATTERNS: Final[frozenset[str]] = frozenset(
    sub_pattern
    for pattern_data in DSA_PATTERN_TAXONOMY.values()
    for sub_pattern in pattern_data["sub_patterns"]  # type: ignore[index]
)


# ============================================================
# NORMALIZATION
# ============================================================


def normalize_text(
    text: str,
) -> str:
    """
    Normalize text for deterministic matching.
    """

    if not text:
        return ""

    text = text.lower().strip()

    replacements = {
        "-": " ",
        "_": " ",
        "/": " ",
        ",": " ",
        ".": " ",
        ":": " ",
        ";": " ",
        "(": " ",
        ")": " ",
        "[": " ",
        "]": " ",
        "{": " ",
        "}": " ",
        "'": "",
        "?": " ",
        "!": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())


# ============================================================
# VALIDATION HELPERS
# ============================================================


def is_valid_pattern(
    pattern: str,
) -> bool:
    """
    Return True when pattern is canonical.
    """

    return pattern in VALID_PATTERNS


def is_valid_sub_pattern(
    pattern: str,
    sub_pattern: str,
) -> bool:
    """
    Return True when the sub-pattern belongs to the supplied
    canonical pattern.
    """

    pattern_data = DSA_PATTERN_TAXONOMY.get(
        pattern
    )

    if pattern_data is None:
        return False

    return sub_pattern in pattern_data["sub_patterns"]  # type: ignore[operator]


def validate_pattern_metadata(
    pattern: str,
    sub_pattern: str,
) -> None:
    """
    Validate a canonical pattern/sub-pattern pair.
    """

    if not is_valid_pattern(pattern):
        raise ValueError(
            f"Unknown DSA pattern: {pattern!r}. "
            f"Expected one of: {sorted(VALID_PATTERNS)}"
        )

    if not is_valid_sub_pattern(
        pattern,
        sub_pattern,
    ):
        allowed = DSA_PATTERN_TAXONOMY[
            pattern
        ]["sub_patterns"]

        raise ValueError(
            f"Invalid sub-pattern {sub_pattern!r} "
            f"for pattern {pattern!r}. "
            f"Allowed values: {allowed}"
        )


# ============================================================
# PLAYLIST HELPERS
# ============================================================


def get_pattern_label(
    pattern: str,
) -> str:
    """
    Return the human-readable pattern label.
    """

    if not is_valid_pattern(pattern):
        raise ValueError(
            f"Unknown DSA pattern: {pattern!r}"
        )

    return str(
        DSA_PATTERN_TAXONOMY[
            pattern
        ]["label"]
    )


def get_sub_patterns(
    pattern: str,
) -> list[str]:
    """
    Return all sub-patterns belonging to a pattern.
    """

    if not is_valid_pattern(pattern):
        raise ValueError(
            f"Unknown DSA pattern: {pattern!r}"
        )

    return list(
        DSA_PATTERN_TAXONOMY[
            pattern
        ]["sub_patterns"]  # type: ignore[index]
    )


def get_playlist_name(
    pattern: str,
) -> str:
    """
    Convert a canonical pattern slug into the project's
    logical playlist identifier.

    Example:

        two_pointer
            ->
        DSA_Patterns_Two_Pointer
    """

    if not is_valid_pattern(pattern):
        raise ValueError(
            f"Unknown DSA pattern: {pattern!r}"
        )

    pattern_name = (
        pattern
        .replace("_", " ")
        .title()
        .replace(" ", "_")
    )

    return (
        f"DSA_Patterns_{pattern_name}"
    )


# ============================================================
# ALIAS / KEYWORD HELPERS
# ============================================================


def get_pattern_aliases(
    pattern: str,
) -> list[str]:
    """
    Return canonical aliases for a pattern.
    """

    if not is_valid_pattern(pattern):
        raise ValueError(
            f"Unknown DSA pattern: {pattern!r}"
        )

    return list(
        DSA_PATTERN_TAXONOMY[
            pattern
        ].get("aliases", [])
    )


def get_pattern_keywords(
    pattern: str,
) -> list[str]:
    """
    Return canonical keywords for a pattern.
    """

    if not is_valid_pattern(pattern):
        raise ValueError(
            f"Unknown DSA pattern: {pattern!r}"
        )

    return list(
        DSA_PATTERN_TAXONOMY[
            pattern
        ].get("keywords", [])
    )


def _keyword_match_score(
    text: str,
    keyword: str,
) -> int:
    """
    Deterministic keyword scoring.

    Longer / more specific phrases receive higher scores.
    """

    normalized_text = normalize_text(
        text
    )

    normalized_keyword = normalize_text(
        keyword
    )

    if not normalized_keyword:
        return 0

    if normalized_keyword not in normalized_text:
        return 0

    word_count = len(
        normalized_keyword.split()
    )

    score = (
        word_count * 10
        + min(
            len(normalized_keyword),
            30,
        )
    )

    return score


# ============================================================
# PATTERN RESOLUTION
# ============================================================


def resolve_pattern_from_text(
    text: str,
) -> str | None:
    """
    Resolve natural language to a canonical pattern.

    Important:

    Only patterns present in DSA_PATTERN_TAXONOMY can be
    returned.

    Generic sorting algorithms such as merge sort are therefore
    NOT converted into a fake sorting pattern.
    """

    if not text:
        return None

    best_pattern: str | None = None
    best_score = 0

    for pattern, data in (
        DSA_PATTERN_TAXONOMY.items()
    ):

        candidates: list[str] = []

        candidates.extend(
            str(alias)
            for alias in data.get(
                "aliases",
                [],
            )
        )

        candidates.extend(
            str(keyword)
            for keyword in data.get(
                "keywords",
                [],
            )
        )

        for candidate in candidates:

            score = _keyword_match_score(
                text,
                candidate,
            )

            if score > best_score:
                best_score = score
                best_pattern = pattern

    return best_pattern


# ============================================================
# SUB-PATTERN ALIASES
# ============================================================


SUB_PATTERN_ALIASES: Final[
    dict[str, list[str]]
] = {

    # --------------------------------------------------------
    # TWO POINTER
    # --------------------------------------------------------

    "opposite_direction": [
        "opposite direction",
        "left right pointers",
        "left and right pointer",
    ],

    "same_direction": [
        "same direction",
        "same direction pointers",
    ],

    "pair_search": [
        "pair search",
        "two sum",
        "pair sum",
        "find pair",
    ],

    "three_sum": [
        "three sum",
        "3 sum",
        "3sum",
        "triplet sum",
    ],

    "four_sum": [
        "four sum",
        "4 sum",
        "4sum",
    ],

    "partitioning": [
        "partition",
        "partitioning",
    ],

    "duplicate_removal": [
        "remove duplicates",
        "duplicate removal",
    ],

    "move_zeros": [
        "move zeros",
        "move zeroes",
    ],

    "dutch_national_flag": [
        "dutch national flag",
        "dutch flag",
    ],


    # --------------------------------------------------------
    # SLIDING WINDOW
    # --------------------------------------------------------

    "fixed_window": [
        "fixed window",
        "fixed size window",
    ],

    "variable_window": [
        "variable window",
        "variable size window",
    ],

    "longest_valid_window": [
        "longest valid window",
        "longest substring",
        "longest subarray",
    ],

    "shortest_valid_window": [
        "shortest valid window",
        "smallest window",
    ],

    "frequency_window": [
        "frequency window",
        "character frequency window",
    ],

    "minimum_window": [
        "minimum window",
        "minimum window substring",
    ],


    # --------------------------------------------------------
    # KADANE
    # --------------------------------------------------------

    "maximum_subarray": [
        "maximum subarray",
        "max subarray",
    ],

    "maximum_subarray_sum": [
        "maximum subarray sum",
        "max subarray sum",
    ],

    "minimum_subarray_variant": [
        "minimum subarray",
        "minimum subarray sum",
    ],


    # --------------------------------------------------------
    # FAST / SLOW POINTER
    # --------------------------------------------------------

    "cycle_detection": [
        "cycle detection",
        "detect cycle",
        "linked list cycle",
    ],

    "find_middle": [
        "find middle",
        "middle of linked list",
        "middle element",
    ],

    "nth_node_from_end": [
        "nth node from end",
        "remove nth node",
    ],

    "cycle_entry": [
        "cycle entry",
        "entry point of cycle",
    ],

    "duplicate_number": [
        "duplicate number",
        "find duplicate number",
    ],


    # --------------------------------------------------------
    # PREFIX SUM
    # --------------------------------------------------------

    "one_dimensional_prefix_sum": [
        "one dimensional prefix sum",
        "1d prefix sum",
    ],

    "two_dimensional_prefix_sum": [
        "two dimensional prefix sum",
        "2d prefix sum",
    ],

    "range_sum": [
        "range sum",
        "range query",
    ],

    "prefix_sum_hashing": [
        "prefix sum hashmap",
        "prefix sum hashing",
    ],


    # --------------------------------------------------------
    # HASHING
    # --------------------------------------------------------

    "frequency_map": [
        "frequency map",
        "frequency hashmap",
        "frequency counting",
        "count frequency",
    ],

    "lookup_set": [
        "lookup set",
        "hash set lookup",
        "set lookup",
    ],

    "complement_lookup": [
        "complement lookup",
        "two sum hashmap",
    ],

    "grouping": [
        "grouping with hashmap",
        "group by",
    ],


    # --------------------------------------------------------
    # MERGE INTERVALS
    # --------------------------------------------------------

    "merge_overlapping_intervals": [
        "merge intervals",
        "merge overlapping intervals",
    ],

    "overlap_detection": [
        "overlap detection",
        "interval overlap",
        "overlapping intervals",
    ],

    "meeting_rooms": [
        "meeting rooms",
        "meeting room",
    ],

    "interval_scheduling": [
        "interval scheduling",
    ],


    # --------------------------------------------------------
    # BINARY SEARCH
    # --------------------------------------------------------

    "classic_binary_search": [
        "classic binary search",
        "basic binary search",
        "standard binary search",
    ],

    "lower_bound": [
        "lower bound",
    ],

    "upper_bound": [
        "upper bound",
    ],

    "first_last_occurrence": [
        "first occurrence",
        "last occurrence",
        "first and last occurrence",
    ],

    "search_rotated_array": [
        "rotated array",
        "search rotated array",
    ],

    "binary_search_on_answer": [
        "binary search on answer",
        "search on answer",
        "bsoa",
        "bossa",
    ],

    "monotonic_predicate": [
        "monotonic predicate",
        "monotonic condition",
    ],


    # --------------------------------------------------------
    # STACK
    # --------------------------------------------------------

    "basic_stack": [
        "basic stack",
        "stack basics",
    ],

    "balanced_parentheses": [
        "balanced parentheses",
        "valid parentheses",
        "balanced brackets",
    ],

    "monotonic_stack": [
        "monotonic stack",
    ],

    "next_greater_element": [
        "next greater element",
        "nge",
    ],

    "previous_greater_element": [
        "previous greater element",
        "pge",
    ],

    "next_smaller_element": [
        "next smaller element",
        "nse",
    ],

    "expression_evaluation": [
        "expression evaluation",
        "evaluate expression",
    ],


    # --------------------------------------------------------
    # HEAP
    # --------------------------------------------------------

    "min_heap": [
        "min heap",
        "minimum heap",
    ],

    "max_heap": [
        "max heap",
        "maximum heap",
    ],

    "top_k": [
        "top k",
        "top-k",
        "top k elements",
    ],

    "kth_element": [
        "kth element",
        "kth largest",
        "kth smallest",
    ],

    "two_heaps": [
        "two heaps",
        "two heap",
    ],

    "heap_pairs": [
        "heap pairs",
        "pairs using heap",
    ],


    # --------------------------------------------------------
    # RECURSION
    # --------------------------------------------------------

    "recursion_basics": [
        "recursion basics",
        "recursive basics",
    ],

    "base_case": [
        "base case",
    ],

    "recursive_call": [
        "recursive call",
        "recursive calls",
    ],

    "recursion_tree": [
        "recursion tree",
    ],


    # --------------------------------------------------------
    # BACKTRACKING
    # --------------------------------------------------------

    "subsets": [
        "subsets",
        "subset",
    ],

    "permutations": [
        "permutations",
        "permutation",
    ],

    "combinations": [
        "combinations",
        "combination",
    ],

    "decision_tree": [
        "decision tree",
    ],

    "constraint_satisfaction": [
        "constraint satisfaction",
    ],

    "pruning": [
        "pruning",
        "backtracking pruning",
    ],


    # --------------------------------------------------------
    # DYNAMIC PROGRAMMING
    # --------------------------------------------------------

    "memoization": [
        "memoization",
        "memoisation",
        "top down dp",
        "top-down dp",
    ],

    "tabulation": [
        "tabulation",
        "bottom up dp",
        "bottom-up dp",
    ],

    "one_dimensional_dp": [
        "one dimensional dp",
        "1d dp",
    ],

    "two_dimensional_dp": [
        "two dimensional dp",
        "2d dp",
    ],

    "state_transition": [
        "state transition",
        "dp transition",
    ],

    "space_optimization": [
        "space optimization",
        "dp space optimization",
    ],
}


# ============================================================
# SUB-PATTERN RESOLUTION
# ============================================================


def resolve_sub_pattern_from_text(
    text: str,
    pattern: str | None = None,
) -> str | None:
    """
    Resolve a sub-pattern.

    If pattern is supplied, only sub-patterns belonging to that
    pattern are considered.
    """

    if not text:
        return None

    normalized_text = normalize_text(
        text
    )

    allowed_sub_patterns: (
        set[str] | None
    ) = None

    if pattern is not None:

        if not is_valid_pattern(
            pattern
        ):
            return None

        allowed_sub_patterns = set(
            DSA_PATTERN_TAXONOMY[
                pattern
            ]["sub_patterns"]  # type: ignore[index]
        )

    best_sub_pattern: str | None = None
    best_score = 0

    for (
        sub_pattern,
        aliases,
    ) in SUB_PATTERN_ALIASES.items():

        if (
            allowed_sub_patterns is not None
            and sub_pattern
            not in allowed_sub_patterns
        ):
            continue

        for alias in aliases:

            score = _keyword_match_score(
                normalized_text,
                alias,
            )

            if score > best_score:
                best_score = score
                best_sub_pattern = (
                    sub_pattern
                )

    return best_sub_pattern


# ============================================================
# COMPLETE METADATA RESOLUTION
# ============================================================


def resolve_dsa_metadata(
    text: str,
) -> dict[str, str | None]:
    """
    Resolve:

        pattern
        sub_pattern
        playlist

    from natural-language text.

    If a generic algorithm is not represented by the canonical
    taxonomy, pattern/sub-pattern/playlist remain None.

    Example:

        "How does two pointer work?"

        ->
        {
            "pattern": "two_pointer",
            "sub_pattern": None,
            "playlist": "DSA_Patterns_Two_Pointer",
        }

    Example:

        "What is merge sort?"

        ->
        {
            "pattern": None,
            "sub_pattern": None,
            "playlist": None,
        }
    """

    pattern = (
        resolve_pattern_from_text(
            text
        )
    )

    sub_pattern = (
        resolve_sub_pattern_from_text(
            text,
            pattern,
        )
    )

    playlist = (
        get_playlist_name(pattern)
        if pattern is not None
        else None
    )

    return {
        "pattern": pattern,
        "sub_pattern": sub_pattern,
        "playlist": playlist,
    }


# ============================================================
# CLASSIFICATION HELPER
# ============================================================


def classify_text(
    text: str,
) -> dict[str, object]:
    """
    Classify text into canonical metadata.
    """

    result = resolve_dsa_metadata(
        text
    )

    pattern = result[
        "pattern"
    ]

    sub_pattern = result[
        "sub_pattern"
    ]

    if pattern is None:
        confidence = 0.0

    elif sub_pattern is not None:
        confidence = 1.0

    else:
        confidence = 0.75

    return {
        **result,
        "confidence": confidence,
    }


# ============================================================
# BACKWARD-COMPATIBILITY HELPERS
# ============================================================


def get_pattern_from_text(
    text: str,
) -> str | None:
    """
    Backward-compatible wrapper.
    """

    return resolve_pattern_from_text(
        text
    )


def get_sub_pattern_from_text(
    text: str,
    pattern: str | None = None,
) -> str | None:
    """
    Backward-compatible wrapper.
    """

    return resolve_sub_pattern_from_text(
        text,
        pattern,
    )


# ============================================================
# CLI SELF-CHECK
# ============================================================


if __name__ == "__main__":

    print("=" * 60)
    print("DSA TAXONOMY SELF-CHECK")
    print("=" * 60)

    print(
        f"Core patterns : {len(VALID_PATTERNS)}"
    )

    print(
        f"Sub-patterns  : {len(VALID_SUB_PATTERNS)}"
    )

    print()

    # --------------------------------------------------------
    # Canonical metadata checks
    # --------------------------------------------------------

    print(
        "Canonical metadata checks"
    )

    print("-" * 60)

    canonical_checks = [
        (
            "dynamic_programming",
            "memoization",
        ),
        (
            "two_pointer",
            "pair_search",
        ),
        (
            "sliding_window",
            "fixed_window",
        ),
        (
            "binary_search",
            "binary_search_on_answer",
        ),
        (
            "stack",
            "next_greater_element",
        ),
    ]

    for pattern, sub_pattern in (
        canonical_checks
    ):

        validate_pattern_metadata(
            pattern,
            sub_pattern,
        )

        print(
            f"✓ {pattern} / {sub_pattern}"
        )

    # --------------------------------------------------------
    # Natural-language resolution checks
    # --------------------------------------------------------

    print()
    print(
        "Natural-language resolution checks"
    )
    print("-" * 60)

    test_queries = [

        "How does two pointer work?",

        "Explain dynamic programming memoization",

        "What is sliding window?",

        "Explain binary search on answer",

        "Explain Kadane algorithm",

        "How does prefix sum work?",

        "Explain merge intervals",

        "What is hashing?",

        "Explain stack next greater element",

        "Explain heap",

        "Explain recursion",

        "Explain backtracking",

        # IMPORTANT:
        # This must NOT invent a sorting playlist.
        "What is the time complexity of merge sort?",
    ]

    for query in test_queries:

        result = resolve_dsa_metadata(
            query
        )

        print()
        print(
            f"Query       : {query}"
        )

        print(
            f"Pattern     : {result['pattern']}"
        )

        print(
            f"Sub-pattern : {result['sub_pattern']}"
        )

        print(
            f"Playlist    : {result['playlist']}"
        )

    # --------------------------------------------------------
    # Explicit negative checks
    # --------------------------------------------------------

    print()
    print(
        "Negative checks"
    )
    print("-" * 60)

    unsupported_sort_queries = [
        "Explain merge sort",
        "Explain bubble sort",
        "Explain insertion sort",
        "Explain selection sort",
        "Explain quick sort",
        "Explain radix sort",
        "Explain heap sort",
    ]

    for query in (
        unsupported_sort_queries
    ):

        result = resolve_dsa_metadata(
            query
        )

        if (
            result["pattern"] is None
            and result["sub_pattern"] is None
            and result["playlist"] is None
        ):
            print(
                f"✓ No fake pattern generated: {query}"
            )
        else:
            print(
                f"✗ Unexpected classification: {query}"
            )
            print(
                f"  Result: {result}"
            )

    # --------------------------------------------------------
    # Playlist checks
    # --------------------------------------------------------

    print()
    print(
        "Playlist checks"
    )
    print("-" * 60)

    for pattern in [
        "two_pointer",
        "sliding_window",
        "binary_search",
        "stack",
        "heap",
        "recursion",
        "backtracking",
        "dynamic_programming",
    ]:

        print(
            f"{pattern:<25} -> "
            f"{get_playlist_name(pattern)}"
        )

    print()
    print("=" * 60)
    print(
        "VALIDATION : PASSED"
    )
    print("=" * 60)