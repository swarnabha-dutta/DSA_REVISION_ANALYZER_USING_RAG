"""
Phase 14.1 timestamp-formatting validation.

Run from:
    backend/

Command:
    python .\scripts\test_timestamp_formatting.py

This test focuses only on timestamp-aware result formatting.
It does not change retrieval, ranking, or timestamp metadata storage.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow this script to be run directly from backend/scripts/.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.context_assembler import (  # noqa: E402
    _format_timestamp,
    _format_timestamp_range,
)


def check(name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise AssertionError(
            f"{name}: expected {expected!r}, got {actual!r}"
        )
    print(f"✓ {name}")


def main() -> None:
    print("=" * 60)
    print("PHASE 14.1 — TIMESTAMP FORMATTING TEST")
    print("=" * 60)

    checks = [
        (
            "zero seconds",
            _format_timestamp(0),
            "00:00",
        ),
        (
            "sub-minute timestamp",
            _format_timestamp(12.75),
            "00:12",
        ),
        (
            "minute timestamp",
            _format_timestamp(83.5),
            "01:23",
        ),
        (
            "hour timestamp",
            _format_timestamp(3725.2),
            "01:02:05",
        ),
        (
            "missing timestamp",
            _format_timestamp(None),
            "unknown",
        ),
        (
            "timestamp range",
            _format_timestamp_range(83.5, 127.9),
            "01:23 -> 02:07",
        ),
        (
            "missing range endpoints",
            _format_timestamp_range(None, None),
            "unknown -> unknown",
        ),
    ]

    for name, actual, expected in checks:
        check(name, actual, expected)

    print()
    print(f"Passed : {len(checks)}/{len(checks)}")
    print("✓ PHASE 14.1 TIMESTAMP FORMATTING TEST PASSED")


if __name__ == "__main__":
    main()
