"""
DSA Retrieval Pipeline Integration Test
=======================================

Validates the complete retrieval flow:

    User Query
        ↓
    Query Understanding
        ↓
    Intent
    Pattern
    Sub-pattern
        ↓
    Metadata-aware Retrieval
        ↓
    Qdrant
        ↓
    Relevant Chunks

IMPORTANT
---------

This integration test only uses patterns for which transcript
chunks are expected to exist in the current Qdrant collection.

It does NOT test generic algorithms that are not canonical
patterns in the project taxonomy.

Therefore there is intentionally NO:

    merge sort
    bubble sort
    insertion sort
    selection sort
    radix sort
    sorting_sweep

test here.
"""

from __future__ import annotations

import sys

from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR),
    )


# ============================================================
# SERVICE IMPORTS
# ============================================================


from app.services.query_understanding import (  # noqa: E402
    analyze_query,
)

from app.services.retrieval import (  # noqa: E402
    retrieve_chunks,
)

from app.services.dsa_taxonomy import (  # noqa: E402
    get_playlist_name,
)


# ============================================================
# TEST QUERIES
# ============================================================
#
# These tests correspond to data that has already been ingested
# in the current development environment.
#
# Dynamic Programming:
#     dyG4JBKh6tA
#
# Two Pointer:
#     PvyEr3CeKzE
#
# ============================================================


TEST_QUERIES = [

    {
        "name": (
            "Dynamic Programming + Memoization"
        ),

        "query": (
            "Explain dynamic programming memoization"
        ),

        "expected_intent": (
            "implementation"
        ),

        "expected_pattern": (
            "dynamic_programming"
        ),

        "expected_sub_pattern": (
            "memoization"
        ),

        "expected_playlist": (
            "DSA_Patterns_Dynamic_Programming"
        ),
    },

    {
        "name": "Two Pointer",

        "query": (
            "How does two pointer work?"
        ),

        "expected_intent": (
            "how_it_works"
        ),

        "expected_pattern": (
            "two_pointer"
        ),

        "expected_sub_pattern": None,

        "expected_playlist": (
            "DSA_Patterns_Two_Pointer"
        ),
    },
]


# ============================================================
# DISPLAY HELPERS
# ============================================================


def print_separator() -> None:
    """
    Print visual separator.
    """

    print(
        "=" * 60
    )


def print_result_header(
    name: str,
) -> None:
    """
    Print individual test header.
    """

    print()

    print_separator()

    print(
        f"TEST: {name}"
    )

    print_separator()


# ============================================================
# QUERY UNDERSTANDING VALIDATION
# ============================================================


def validate_query_understanding(
    query: str,
    expected_intent: str,
    expected_pattern: str | None,
    expected_sub_pattern: str | None,
) -> tuple[object, bool]:
    """
    Run query understanding and validate metadata.
    """

    print()
    print(
        "Query Understanding"
    )

    print(
        "-" * 60
    )

    analysis = analyze_query(
        query
    )

    print(
        f"Query       : {query}"
    )

    print(
        f"Intent      : {analysis.intent}"
    )

    print(
        f"Pattern     : {analysis.pattern}"
    )

    print(
        f"Sub-pattern : {analysis.sub_pattern}"
    )

    print(
        f"Confidence  : {analysis.confidence}"
    )

    passed = True

    # --------------------------------------------------------
    # INTENT
    # --------------------------------------------------------

    if (
        analysis.intent
        != expected_intent
    ):

        print(
            "✗ Intent mismatch"
        )

        print(
            f"  Expected: {expected_intent}"
        )

        print(
            f"  Received: {analysis.intent}"
        )

        passed = False

    else:

        print(
            "✓ Intent correct"
        )

    # --------------------------------------------------------
    # PATTERN
    # --------------------------------------------------------

    if (
        analysis.pattern
        != expected_pattern
    ):

        print(
            "✗ Pattern mismatch"
        )

        print(
            f"  Expected: {expected_pattern}"
        )

        print(
            f"  Received: {analysis.pattern}"
        )

        passed = False

    else:

        print(
            "✓ Pattern correct"
        )

    # --------------------------------------------------------
    # SUB-PATTERN
    # --------------------------------------------------------

    if (
        analysis.sub_pattern
        != expected_sub_pattern
    ):

        print(
            "✗ Sub-pattern mismatch"
        )

        print(
            f"  Expected: {expected_sub_pattern}"
        )

        print(
            f"  Received: {analysis.sub_pattern}"
        )

        passed = False

    else:

        print(
            "✓ Sub-pattern correct"
        )

    return (
        analysis,
        passed,
    )


# ============================================================
# RETRIEVAL VALIDATION
# ============================================================


def validate_retrieval(
    query: str,
    analysis: object,
    expected_pattern: str,
    expected_sub_pattern: str | None,
    expected_playlist: str,
) -> bool:
    """
    Run metadata-aware retrieval and validate returned metadata.
    """

    print()
    print(
        "Retrieval"
    )

    print(
        "-" * 60
    )

    try:

        results = retrieve_chunks(
            query=query,
            pattern=analysis.pattern,
            sub_pattern=analysis.sub_pattern,
            top_k=5,
        )

    except Exception as exc:

        print(
            "✗ Retrieval failed"
        )

        print(
            f"  Error: {exc}"
        )

        return False

    if not results:

        print(
            "✗ No chunks retrieved"
        )

        return False

    print(
        f"✓ Retrieved chunks: {len(results)}"
    )

    if len(results) <= 5:

        print(
            "✓ Result count within top_k=5"
        )

    else:

        print(
            "✗ Result count exceeded top_k=5"
        )

        return False

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    for index, result in enumerate(
        results,
        start=1,
    ):

        print()

        print(
            f"Result #{index}"
        )

        print(
            f"  Score       : "
            f"{result.score:.4f}"
        )

        print(
            f"  Pattern     : "
            f"{result.pattern}"
        )

        print(
            f"  Sub-pattern : "
            f"{result.sub_pattern}"
        )

        print(
            f"  Playlist    : "
            f"{result.playlist}"
        )

        print(
            f"  Video ID    : "
            f"{result.video_id}"
        )

        print(
            f"  Video title : "
            f"{result.video_title}"
        )

        print(
            f"  Chunk ID    : "
            f"{result.chunk_id}"
        )

        print(
            f"  Start       : "
            f"{result.start:.2f}s"
        )

        print(
            f"  End         : "
            f"{result.end:.2f}s"
        )

        text_preview = (
            result.text
            .replace(
                "\n",
                " ",
            )
            .strip()
        )

        if len(text_preview) > 180:

            text_preview = (
                text_preview[:180]
                + "..."
            )

        print(
            f"  Text        : "
            f"{text_preview}"
        )

    # ========================================================
    # METADATA VALIDATION
    # ========================================================

    print()
    print(
        "Retrieval Metadata Validation"
    )

    print(
        "-" * 60
    )

    print(
        f"Expected pattern: "
        f"{expected_pattern}"
    )

    pattern_passed = True

    for index, result in enumerate(
        results,
        start=1,
    ):

        if (
            result.pattern
            != expected_pattern
        ):

            print(
                f"✗ Result #{index} "
                f"pattern mismatch"
            )

            print(
                f"  Expected: "
                f"{expected_pattern}"
            )

            print(
                f"  Received: "
                f"{result.pattern}"
            )

            pattern_passed = False

        else:

            print(
                f"✓ Result #{index} "
                f"pattern: "
                f"{result.pattern}"
            )

    if not pattern_passed:
        return False

    # --------------------------------------------------------
    # SUB-PATTERN
    # --------------------------------------------------------

    if expected_sub_pattern is not None:

        print()

        print(
            f"Expected sub-pattern: "
            f"{expected_sub_pattern}"
        )

        sub_pattern_passed = True

        for index, result in enumerate(
            results,
            start=1,
        ):

            if (
                result.sub_pattern
                != expected_sub_pattern
            ):

                print(
                    f"✗ Result #{index} "
                    f"sub-pattern mismatch"
                )

                print(
                    f"  Expected: "
                    f"{expected_sub_pattern}"
                )

                print(
                    f"  Received: "
                    f"{result.sub_pattern}"
                )

                sub_pattern_passed = False

            else:

                print(
                    f"✓ Result #{index} "
                    f"sub-pattern: "
                    f"{result.sub_pattern}"
                )

        if not sub_pattern_passed:
            return False

    # --------------------------------------------------------
    # PLAYLIST
    # --------------------------------------------------------

    print()

    print(
        f"Expected playlist: "
        f"{expected_playlist}"
    )

    playlist_passed = True

    for index, result in enumerate(
        results,
        start=1,
    ):

        if (
            result.playlist
            != expected_playlist
        ):

            print(
                f"✗ Result #{index} "
                f"playlist mismatch"
            )

            print(
                f"  Expected: "
                f"{expected_playlist}"
            )

            print(
                f"  Received: "
                f"{result.playlist}"
            )

            playlist_passed = False

        else:

            print(
                f"✓ Result #{index} "
                f"playlist: "
                f"{result.playlist}"
            )

    if not playlist_passed:
        return False

    print()

    print(
        "✓ All retrieved chunks satisfy "
        "pattern/sub-pattern/playlist constraints."
    )

    return True


# ============================================================
# SINGLE TEST RUNNER
# ============================================================


def run_test(
    test_case: dict,
) -> bool:
    """
    Execute one complete integration test.
    """

    print_result_header(
        test_case["name"]
    )

    # ========================================================
    # QUERY UNDERSTANDING
    # ========================================================

    (
        analysis,
        understanding_passed,
    ) = validate_query_understanding(
        query=test_case[
            "query"
        ],

        expected_intent=test_case[
            "expected_intent"
        ],

        expected_pattern=test_case[
            "expected_pattern"
        ],

        expected_sub_pattern=test_case[
            "expected_sub_pattern"
        ],
    )

    # ========================================================
    # STOP ON UNDERSTANDING FAILURE
    # ========================================================

    if not understanding_passed:

        print()

        print(
            "Skipping retrieval because "
            "query understanding failed."
        )

        return False

    # ========================================================
    # RETRIEVAL
    # ========================================================

    retrieval_passed = (
        validate_retrieval(
            query=test_case[
                "query"
            ],

            analysis=analysis,

            expected_pattern=test_case[
                "expected_pattern"
            ],

            expected_sub_pattern=test_case[
                "expected_sub_pattern"
            ],

            expected_playlist=test_case[
                "expected_playlist"
            ],
        )
    )

    return (
        understanding_passed
        and retrieval_passed
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    """
    Run all retrieval integration tests.
    """

    print()

    print_separator()

    print(
        "DSA RETRIEVAL PIPELINE INTEGRATION TEST"
    )

    print_separator()

    print(
        f"Base directory: {BASE_DIR}"
    )

    print(
        f"Tests         : "
        f"{len(TEST_QUERIES)}"
    )

    print(
        "Top-K         : 5"
    )

    passed_count = 0

    # ========================================================
    # EXECUTE TESTS
    # ========================================================

    for test_case in TEST_QUERIES:

        passed = run_test(
            test_case
        )

        if passed:

            passed_count += 1

            print()

            print(
                "✓ TEST PASSED"
            )

        else:

            print()

            print(
                "✗ TEST FAILED"
            )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    failed_count = (
        len(TEST_QUERIES)
        - passed_count
    )

    print()
    print_separator()

    print(
        "INTEGRATION TEST SUMMARY"
    )

    print_separator()

    print(
        f"Total tests : "
        f"{len(TEST_QUERIES)}"
    )

    print(
        f"Passed      : "
        f"{passed_count}"
    )

    print(
        f"Failed      : "
        f"{failed_count}"
    )

    print(
        f"Top-K       : 5"
    )

    if failed_count == 0:

        print()

        print(
            "✓ All retrieval pipeline tests passed."
        )

    else:

        print()

        print(
            "✗ Some retrieval pipeline tests failed."
        )

        print(
            "Review the failing metadata validation "
            "checks above."
        )

    print_separator()


# ============================================================
# ENTRY POINT
# ============================================================


if __name__ == "__main__":
    main()