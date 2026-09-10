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

segments = data["segments"][:50]
group_size = 10

results = []

print("=" * 70)
print("IndicTrans2 ONNX - 50 Segment Context Benchmark")
print("=" * 70)
print(f"Video ID       : {data['video_id']}")
print(f"Total segments : {len(segments)}")
print(f"Group size     : {group_size}")
print(f"Groups         : {len(segments) // group_size}")
print()

total_start = time.perf_counter()

for group_index in range(0, len(segments), group_size):
    group = segments[group_index:group_index + group_size]

    hindi = " ".join(x["text"] for x in group)

    print("=" * 70)
    print(
        f"GROUP {group_index // group_size + 1} "
        f"(segments {group_index}-{group_index + len(group) - 1})"
    )
    print("=" * 70)

    print("\nHindi:")
    print(hindi)

    start = time.perf_counter()
    english = translator.translate(hindi)
    elapsed = time.perf_counter() - start

    results.append({
        "group": group_index // group_size + 1,
        "start_segment": group_index,
        "end_segment": group_index + len(group) - 1,
        "hindi": hindi,
        "english": english,
        "seconds": elapsed,
    })

    print("\nEnglish:")
    print(english)

    print(f"\nGroup time: {elapsed:.3f}s")

total_elapsed = time.perf_counter() - total_start

print("\n")
print("=" * 70)
print("BENCHMARK SUMMARY")
print("=" * 70)
print(f"Segments tested : {len(segments)}")
print(f"Groups          : {len(results)}")
print(f"Total time      : {total_elapsed:.3f}s")
print(f"Avg/group       : {total_elapsed / len(results):.3f}s")
print(f"Avg/segment     : {total_elapsed / len(segments):.3f}s")

estimated_full = total_elapsed * (1243 / 50)

print(
    f"Estimated 1243-segment time: "
    f"{estimated_full / 60:.2f} minutes"
)

print("=" * 70)

OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "benchmark_indictrans_50.json"
)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved benchmark: {OUTPUT_FILE}")
