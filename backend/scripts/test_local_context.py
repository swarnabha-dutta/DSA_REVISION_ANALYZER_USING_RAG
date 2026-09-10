"""
Test contextual local translation for a small group of transcript segments.

Purpose:
    Verify whether a group of consecutive Hindi transcript segments can
    be translated together while still keeping enough information to
    map the translated context back to the original segment boundaries.

This is a prototype only.
It does NOT modify the existing Groq translation pipeline or checkpoint.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from local_translation import translate_local


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_ID = "nPdxCoVHC90"

START_SEGMENT = 10
END_SEGMENT = 15

TRANSCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "transcripts"
    / f"{VIDEO_ID}.json"
)


# ============================================================
# LOAD TRANSCRIPT
# ============================================================

with TRANSCRIPT_PATH.open(
    "r",
    encoding="utf-8",
) as file:
    transcript = json.load(file)


segments = transcript["segments"][
    START_SEGMENT:END_SEGMENT
]


# ============================================================
# DISPLAY SOURCE SEGMENTS
# ============================================================

print("=" * 70)
print("LOCAL CONTEXT TRANSLATION TEST")
print("=" * 70)

print(
    f"Video ID       : {VIDEO_ID}"
)

print(
    f"Segments       : "
    f"{START_SEGMENT}-{END_SEGMENT - 1}"
)

print(
    f"Segment count  : {len(segments)}"
)

print("=" * 70)

for segment in segments:

    print(
        f"[Segment {segment['segment_id']}] "
        f"{segment['start']:.3f}s - "
        f"{segment['end']:.3f}s"
    )

    print(
        segment["text"]
    )

    print()


# ============================================================
# BUILD CONTEXT
# ============================================================

context_text = " ".join(
    segment["text"]
    for segment in segments
)


print("=" * 70)
print("COMBINED CONTEXT")
print("=" * 70)

print(context_text)


# ============================================================
# LOCAL TRANSLATION
# ============================================================

print()
print("=" * 70)
print("LOCAL TRANSLATION")
print("=" * 70)

start_time = time.perf_counter()

translated_context = translate_local(
    context_text
)

elapsed = (
    time.perf_counter()
    - start_time
)


print(translated_context)

print()
print(
    f"Translation time: "
    f"{elapsed:.3f}s"
)


# ============================================================
# SOURCE TIMESTAMP RANGE
# ============================================================

first_segment = segments[0]
last_segment = segments[-1]

print()
print("=" * 70)
print("SOURCE TIMESTAMP RANGE")
print("=" * 70)

print(
    f"Start : {first_segment['start']:.3f}s"
)

print(
    f"End   : {last_segment['end']:.3f}s"
)

print(
    f"Duration: "
    f"{last_segment['end'] - first_segment['start']:.3f}s"
)


# ============================================================
# IMPORTANT NOTE
# ============================================================

print()
print("=" * 70)
print("ALIGNMENT STATUS")
print("=" * 70)

print(
    "The English output above represents the entire context window."
)

print(
    "It has NOT been automatically split back into individual "
    "segment-level translations."
)

print(
    "This test is intentionally checking whether contextual "
    "translation is suitable before implementing alignment."
)

print("=" * 70)