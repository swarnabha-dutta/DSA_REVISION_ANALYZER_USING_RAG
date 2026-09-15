"""
Language detection for the DSA Revision Analyzer.

Rules:
    English query -> English answer
    Bengali-script query -> Bengali answer
    Banglish query -> Bengali answer
    Mixed Bengali + English query -> Bengali answer
"""

from __future__ import annotations

import re
from enum import StrEnum


class QueryLanguage(StrEnum):
    """
    Supported query language categories.
    """

    ENGLISH = "english"
    BENGALI = "bengali"
    BANGLISH = "banglish"
    MIXED = "mixed"


# ============================================================
# BANGLISH MARKERS
# ============================================================

BANGLISH_MARKERS: tuple[str, ...] = (
    "ami",
    "amar",
    "amake",
    "apni",
    "tumi",
    "tomar",
    "tor",
    "eta",
    "ei",
    "oi",
    "aeta",
    "aer",
    "er",
    "ta",
    "te",
    "kibhabe",
    "kivabe",
    "ki",
    "keno",
    "kobe",
    "kothay",
    "korbo",
    "korbe",
    "kori",
    "korche",
    "hobe",
    "hoy",
    "hoye",
    "ache",
    "nei",
    "nai",
    "chai",
    "chaile",
    "dorkar",
    "bujhi",
    "bujhte",
    "bujbo",
    "bol",
    "bolo",
    "bolbe",
    "de",
    "dao",
    "diye",
    "theke",
    "jonno",
    "jodi",
    "tahole",
    "sudhu",
    "sob",
    "shob",
    "age",
    "ekta",
    "akta",
    "kono",
    "kon",
    "jinis",
    "mane",
    "like",
    "emon",
    "jeiroom",
    "karon",
    "kaj",
    "kaj kore",
    "korte",
    "kor",
    "hoyna",
    "hoyechhe",
)


# ============================================================
# REGEX
# ============================================================

_BANGLA_RE = re.compile(
    r"[\u0980-\u09FF]"
)

_LATIN_RE = re.compile(
    r"[A-Za-z]"
)

_WORD_RE = re.compile(
    r"[A-Za-z]+"
)


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _bangla_char_count(query: str) -> int:
    """
    Count Bengali-script characters.
    """

    return len(
        _BANGLA_RE.findall(query)
    )


def _latin_char_count(query: str) -> int:
    """
    Count Latin alphabet characters.
    """

    return len(
        _LATIN_RE.findall(query)
    )


def _banglish_marker_count(query: str) -> int:
    """
    Count common Banglish markers.
    """

    words = {
        word.lower()
        for word in _WORD_RE.findall(query)
    }

    return sum(
        1
        for marker in BANGLISH_MARKERS
        if marker in words
    )


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_query_language(
    query: str,
) -> QueryLanguage:
    """
    Detect the language/style of a user query.

    Examples
    --------
    English:
        "How does two pointer work?"

    Bengali:
        "টু পয়েন্টার কিভাবে কাজ করে?"

    Banglish:
        "two pointer ta kibhabe kaj kore?"

    Mixed:
        "Two Pointer এ left pointer কখন move করবো?"
    """

    if not isinstance(query, str):
        raise TypeError(
            "query must be a string."
        )

    query = query.strip()

    if not query:
        raise ValueError(
            "query cannot be empty."
        )

    bangla_chars = _bangla_char_count(
        query
    )

    latin_chars = _latin_char_count(
        query
    )

    # --------------------------------------------------------
    # Bengali + English
    # --------------------------------------------------------

    if bangla_chars and latin_chars:
        return QueryLanguage.MIXED

    # --------------------------------------------------------
    # Bengali script
    # --------------------------------------------------------

    if bangla_chars:
        return QueryLanguage.BENGALI

    # --------------------------------------------------------
    # Banglish
    # --------------------------------------------------------

    marker_count = _banglish_marker_count(
        query
    )

    if marker_count >= 1:
        return QueryLanguage.BANGLISH

    # --------------------------------------------------------
    # Default -> English
    # --------------------------------------------------------

    return QueryLanguage.ENGLISH


# ============================================================
# RESPONSE LANGUAGE
# ============================================================

def response_language_for(
    query: str,
) -> str:
    """
    Determine the language the AI should use for its answer.

    English
        -> English

    Bengali
        -> Bengali

    Banglish
        -> Bengali

    Mixed
        -> Bengali
    """

    detected = detect_query_language(
        query
    )

    if detected is QueryLanguage.ENGLISH:
        return "English"

    return "Bengali"


# ============================================================
# LANGUAGE METADATA
# ============================================================

def language_metadata(
    query: str,
) -> dict[str, str]:
    """
    Return both detected query language
    and expected response language.
    """

    detected = detect_query_language(
        query
    )

    return {
        "query_language": detected.value,
        "response_language": response_language_for(
            query
        ),
    }


# ============================================================
# SELF CHECK
# ============================================================

def self_check() -> None:
    """
    Run a lightweight language detector self-check.
    """

    test_cases = [
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
            "Two Pointer এ left pointer কখন move করবো?",
            "mixed",
            "Bengali",
        ),
    ]

    print("=" * 60)
    print("LANGUAGE DETECTION SELF-CHECK")
    print("=" * 60)

    for (
        query,
        expected_query_language,
        expected_response_language,
    ) in test_cases:

        detected = detect_query_language(
            query
        ).value

        response_language = response_language_for(
            query
        )

        assert (
            detected ==
            expected_query_language
        ), (
            f"Expected "
            f"{expected_query_language}, "
            f"got {detected} "
            f"for query: {query}"
        )

        assert (
            response_language ==
            expected_response_language
        ), (
            f"Expected "
            f"{expected_response_language}, "
            f"got {response_language} "
            f"for query: {query}"
        )

        print(
            f"✓ {detected:8} → "
            f"{response_language:7} | "
            f"{query}"
        )

    print()
    print("✓ Language detection self-check passed.")


if __name__ == "__main__":
    self_check()