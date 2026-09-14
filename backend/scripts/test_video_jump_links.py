"""
Phase 14.2 — Video Jump Link Test

Run from:
    backend/

Command:
    python .\scripts\test_video_jump_links.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.context_assembler import _build_youtube_jump_link


def check(name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise AssertionError(
            f"{name}: expected {expected!r}, got {actual!r}"
        )
    print(f"✓ {name}")


def main() -> None:
    print("=" * 60)
    print("PHASE 14.2 — VIDEO JUMP LINK TEST")
    print("=" * 60)

    checks = [
        ("valid jump link", _build_youtube_jump_link("dyG4JBKh6tA", 83.5),
         "https://www.youtube.com/watch?v=dyG4JBKh6tA&t=83s"),
        ("zero-second jump link", _build_youtube_jump_link("abc123_-X", 0),
         "https://www.youtube.com/watch?v=abc123_-X&t=0s"),
        ("missing video id", _build_youtube_jump_link(None, 83), None),
        ("empty video id", _build_youtube_jump_link("   ", 83), None),
        ("missing timestamp", _build_youtube_jump_link("dyG4JBKh6tA", None), None),
        ("negative timestamp is clamped", _build_youtube_jump_link("dyG4JBKh6tA", -10),
         "https://www.youtube.com/watch?v=dyG4JBKh6tA&t=0s"),
    ]

    for name, actual, expected in checks:
        check(name, actual, expected)

    print()
    print(f"Passed : {len(checks)}/{len(checks)}")
    print("✓ PHASE 14.2 VIDEO JUMP LINK TEST PASSED")


if __name__ == "__main__":
    main()
