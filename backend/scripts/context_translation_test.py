from pathlib import Path
import json
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

import indictrans_onnx_test as translator


TRANSCRIPT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "transcripts"
    / "nPdxCoVHC90.json"
)

with open(TRANSCRIPT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

segments = data["segments"][:10]
hindi = " ".join(x["text"] for x in segments)

print("=" * 70)
print("IndicTrans2 ONNX - Contextual Translation Test")
print("=" * 70)

print("\nINPUT:")
print(hindi)

start = time.perf_counter()
english = translator.translate(hindi)
elapsed = time.perf_counter() - start

print("\n" + "=" * 70)
print("TRANSLATION:")
print(english)

print("\n" + "=" * 70)
print("TIME:")
print(f"{elapsed:.3f}s")

print("\n" + "=" * 70)
print("Contextual translation test completed")
print("=" * 70)
