from pathlib import Path
import json
import time
import sys

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

print("=" * 70)
print("IndicTrans2 ONNX - 10 Segment Benchmark")
print("=" * 70)
print(f"Video ID : {data['video_id']}")
print(f"Segments : {len(segments)}")
print()

results = []
total_start = time.perf_counter()

for i, segment in enumerate(segments):
    hindi = segment["text"]

    print(f"[{i}] Hindi:")
    print(hindi)

    start = time.perf_counter()
    english = translator.translate(hindi)
    elapsed = time.perf_counter() - start

    results.append({
        "index": i,
        "hindi": hindi,
        "english": english,
        "seconds": elapsed,
    })

    print("English:")
    print(english)
    print(f"Time: {elapsed:.3f}s")
    print("-" * 70)

total_elapsed = time.perf_counter() - total_start

print()
print("=" * 70)
print("BENCHMARK SUMMARY")
print("=" * 70)
print(f"Total segments : {len(results)}")
print(f"Total time     : {total_elapsed:.3f}s")
print(f"Avg / segment  : {total_elapsed / len(results):.3f}s")
print("=" * 70)

OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "benchmark_indictrans_10.json"
)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Saved benchmark: {OUTPUT_FILE}")
