"""
Tests for DSA Revision Analyzer language detection.
"""

from __future__ import annotations

import sys
from pathlib import Path


BACKEND_ROOT = Path(
    __file__
).resolve().parents[1]


if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


from app.services.language_detection import (
    detect_query_language,
    response_language_for,
)


CASES = [

    (
        "How does two pointer work?",
        "english",
        "English",
    ),

    (
        "টু পয়েন্টার কিভাবে কাজ করে?",
        "bengali",
        "Bengali",
    ),

    (
        "two pointer ta kibhabe kaj kore?",
        "banglish",
        "Bengali",
    ),

    (
        "Two pointer এ left pointer কখন move করবো?",
        "mixed",
        "Bengali",
    ),

    (
        "When should I move the left pointer?",
        "english",
        "English",
    ),

    (
        "left pointer কখন move করব?",
        "mixed",
        "Bengali",
    ),
]


def main() -> None:

    passed = 0

    print("=" * 60)
    print("LANGUAGE DETECTION TEST")
    print("=" * 60)

    for (
        query,
        expected_query_language,
        expected_response_language,
    ) in CASES:

        detected = (
            detect_query_language(query)
            .value
        )

        response_language = (
            response_language_for(query)
        )

        assert (
            detected ==
            expected_query_language
        ), (
            f"Unexpected query language "
            f"for {query!r}: {detected}"
        )

        assert (
            response_language ==
            expected_response_language
        ), (
            f"Unexpected response language "
            f"for {query!r}: "
            f"{response_language}"
        )

        print(
            f"✓ {detected:8} → "
            f"{response_language:7} | "
            f"{query}"
        )

        passed += 1

    print()

    print(
        f"RESULT: "
        f"{passed}/{len(CASES)} TESTS PASSED"
    )


if __name__ == "__main__":
    main()