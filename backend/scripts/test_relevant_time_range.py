"""
Phase 14.3 — Relevant Time-Range Test

Tests the extraction and validation of the relevant timestamp range
from retrieved video metadata.

Run from:
    backend/

Command:
    python .\scripts\test_relevant_time_range.py
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PATH SETUP
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# IMPORT
# ============================================================

from app.services.context_assembler import (
    _extract_relevant_time_range,
)


# ============================================================
# ASSERTION HELPER
# ============================================================

def check(
    name: str,
    actual: object,
    expected: object,
) -> None:
    """
    Validate a single test case.
    """

    if actual != expected:
        raise AssertionError(
            f"{name}: expected {expected!r}, got {actual!r}"
        )

    print(f"✓ {name}")


# ============================================================
# MAIN TEST
# ============================================================

def main() -> None:

    print("=" * 60)
    print("PHASE 14.3 — RELEVANT TIME-RANGE TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Valid range
    # --------------------------------------------------------

    check(
        "valid timestamp range",
        _extract_relevant_time_range(
            83.5,
            127.9,
        ),
        {
            "start": 83.5,
            "end": 127.9,
            "duration": 44.4,
        },
    )

    # --------------------------------------------------------
    # Exact integer range
    # --------------------------------------------------------

    check(
        "integer timestamp range",
        _extract_relevant_time_range(
            60,
            120,
        ),
        {
            "start": 60.0,
            "end": 120.0,
            "duration": 60.0,
        },
    )

    # --------------------------------------------------------
    # Same start and end
    # --------------------------------------------------------

    check(
        "zero-duration range",
        _extract_relevant_time_range(
            100,
            100,
        ),
        {
            "start": 100.0,
            "end": 100.0,
            "duration": 0.0,
        },
    )

    # --------------------------------------------------------
    # Missing start
    # --------------------------------------------------------

    check(
        "missing start timestamp",
        _extract_relevant_time_range(
            None,
            127.9,
        ),
        None,
    )

    # --------------------------------------------------------
    # Missing end
    # --------------------------------------------------------

    check(
        "missing end timestamp",
        _extract_relevant_time_range(
            83.5,
            None,
        ),
        None,
    )

    # --------------------------------------------------------
    # Both missing
    # --------------------------------------------------------

    check(
        "missing timestamp range",
        _extract_relevant_time_range(
            None,
            None,
        ),
        None,
    )

    # --------------------------------------------------------
    # Invalid reversed range
    # --------------------------------------------------------

    check(
        "reversed timestamp range",
        _extract_relevant_time_range(
            127.9,
            83.5,
        ),
        None,
    )

    # --------------------------------------------------------
    # Negative start
    # --------------------------------------------------------

    check(
        "negative start rejected",
        _extract_relevant_time_range(
            -10,
            50,
        ),
        None,
    )

    # --------------------------------------------------------
    # Negative end
    # --------------------------------------------------------

    check(
        "negative end rejected",
        _extract_relevant_time_range(
            10,
            -5,
        ),
        None,
    )

    # --------------------------------------------------------
    # String numeric values
    # --------------------------------------------------------

    check(
        "numeric strings converted",
        _extract_relevant_time_range(
            "83.5",
            "127.9",
        ),
        {
            "start": 83.5,
            "end": 127.9,
            "duration": 44.4,
        },
    )

    # --------------------------------------------------------
    # Non-numeric values
    # --------------------------------------------------------

    check(
        "invalid start rejected",
        _extract_relevant_time_range(
            "invalid",
            100,
        ),
        None,
    )

    check(
        "invalid end rejected",
        _extract_relevant_time_range(
            50,
            "invalid",
        ),
        None,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_checks = 13

    print()
    print("=" * 60)
    print("PHASE 14.3 SUMMARY")
    print("=" * 60)
    print(f"Passed : {total_checks}/{total_checks}")

    print()
    print("✓ RELEVANT TIME-RANGE TEST PASSED")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()