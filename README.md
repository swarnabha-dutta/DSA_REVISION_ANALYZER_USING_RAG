# DSA Revision Analyzer

An AI-powered DSA revision system that converts educational video content into a
structured, searchable knowledge base and uses semantic retrieval to provide
pattern-aware revision support.

The system is designed around **DSA patterns**, not individual random problems.

---

## 🎯 Project Goal

The goal of DSA Revision Analyzer is to help a learner revise DSA concepts from
the educational content they have already studied.

Instead of treating a YouTube transcript as plain text, the system builds a
structured pipeline:

```text
YouTube Video
      ↓
Transcript Extraction
      ↓
English Translation
      ↓
Smart Chunking
      ↓
DSA Pattern Metadata
      ↓
Embedding Generation
      ↓
Qdrant Vector Database
      ↓
Query Understanding
      ↓
Metadata-Aware Retrieval
      ↓
Relevant Revision Content
````

The long-term system will also use completed topics to generate
**pattern-specific practice problems without hints**.

---

# 🧠 Core Architecture

The project currently follows a modular architecture:

```text
                    ┌──────────────────────┐
                    │    YouTube Video     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Transcript Extraction│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Translation       │
                    │      → English       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Smart Chunking    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  DSA Taxonomy /      │
                    │  Metadata Enrichment │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Sentence Transformer │
                    │    Embeddings        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        Qdrant        │
                    │    Vector Database   │
                    └──────────┬───────────┘
                               │
                               │
                     User Query
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Query Understanding  │
                    ├──────────────────────┤
                    │ Intent               │
                    │ Pattern              │
                    │ Sub-pattern          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Metadata-Aware        │
                    │ Retrieval             │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Relevant Chunks       │
                    └──────────────────────┘
```

---

# 📁 Project Structure

```text
dsa_revision_analyzer/
│
├── backend/
│   │
│   ├── app/
│   │   └── services/
│   │       ├── dsa_taxonomy.py
│   │       ├── metadata_storage.py
│   │       ├── query_understanding.py
│   │       ├── retrieval.py
│   │       └── video_metadata_schema.py
│   │
│   ├── data/
│   │   ├── transcripts/
│   │   ├── translated/
│   │   └── chunks/
│   │
│   ├── scripts/
│   │   ├── youtube_transcribe.py
│   │   ├── translate_transcript.py
│   │   ├── chunk_transcript.py
│   │   ├── ingest_embeddings.py
│   │   └── test_retrieval_pipeline.py
│   │
│   ├── .env
│   └── README.md
│
└── frontend/
    └── ...
```

---

# 🗂️ DSA Taxonomy

The project uses a **canonical DSA taxonomy**.

The taxonomy is the single source of truth for:

* Pattern classification
* Sub-pattern validation
* Playlist mapping
* Metadata enrichment
* Qdrant filtering
* Query understanding
* Revision organization
* Future practice generation

Current taxonomy:

```text
13 Core DSA Patterns
71 Sub-patterns
```

The taxonomy intentionally contains only patterns relevant to the target DSA
learning system.

## Current Core Patterns

```text
1. Two Pointer
2. Sliding Window
3. Hashing
4. Prefix Sum
5. Binary Search
6. Sorting + Sweep
7. Intervals
8. Fast & Slow Pointer
9. Stack
10. Heap
11. Recursion
12. Backtracking
13. Dynamic Programming
```

> The taxonomy should be extended only when a genuine DSA pattern is required.
> Individual sorting algorithms such as Bubble Sort, Insertion Sort, Selection
> Sort, Radix Sort, etc. are NOT treated as standalone DSA patterns.

---

# 🏷️ Pattern and Sub-pattern Design

Each chunk can contain canonical metadata such as:

```json
{
  "pattern": "two_pointer",
  "sub_pattern": "pair_search",
  "playlist": "DSA_Patterns_Two_Pointer"
}
```

The system distinguishes between:

```text
Pattern
    ↓
Sub-pattern
    ↓
Transcript chunks
```

For example:

```text
two_pointer
├── opposite_direction
├── same_direction
├── pair_search
├── three_sum
├── four_sum
└── partitioning
```

Another example:

```text
dynamic_programming
├── memoization
├── tabulation
├── state_definition
├── transition
└── space_optimization
```

The exact supported values are controlled by `dsa_taxonomy.py`.

---

# 📚 Playlist Mapping

Each canonical pattern maps to a logical playlist namespace.

Example:

```text
two_pointer
    ↓
DSA_Patterns_Two_Pointer

dynamic_programming
    ↓
DSA_Patterns_Dynamic_Programming

sliding_window
    ↓
DSA_Patterns_Sliding_Window
```

The playlist name is **derived from the canonical taxonomy**.

It is not manually constructed during embedding ingestion.

This prevents inconsistent metadata such as:

```text
Two Pointer
two-pointer
two pointer
2 pointer
```

from becoming separate categories.

---

# 🎥 Transcript Pipeline

## 1. YouTube Transcript Extraction

Script:

```text
backend/scripts/youtube_transcribe.py
```

Usage:

```powershell
python .\scripts\youtube_transcribe.py <VIDEO_ID>
```

Example:

```powershell
python .\scripts\youtube_transcribe.py PvyEr3CeKzE
```

Output:

```text
data/transcripts/<VIDEO_ID>.json
```

The transcript retains:

* Video ID
* Video title
* Timestamp information
* Transcript segments

---

# 🌐 Translation Pipeline

The transcript is translated into English before chunking and embedding.

Script:

```text
backend/scripts/translate_transcript.py
```

Usage:

```powershell
python .\scripts\translate_transcript.py <VIDEO_ID>
```

Example:

```powershell
python .\scripts\translate_transcript.py PvyEr3CeKzE
```

Output:

```text
data/translated/<VIDEO_ID>.json
```

The translation pipeline uses batching and retry logic.

Current configuration:

```text
Model:
openai/gpt-oss-120b

Batch size:
25 segments
```

Translation failures caused by temporary API/network issues are retried.

---

# ✂️ Smart Chunking

Script:

```text
backend/scripts/chunk_transcript.py
```

Usage:

```powershell
python .\scripts\chunk_transcript.py <VIDEO_ID>
```

Example:

```powershell
python .\scripts\chunk_transcript.py PvyEr3CeKzE
```

The chunking system creates semantically useful transcript chunks instead of
splitting the transcript at arbitrary fixed intervals.

Current configuration:

```text
Target characters : 1000
Maximum characters: 1400
Overlap segments  : 2
```

Example result:

```text
Input segments : 766
Output chunks   : 33
Average chunk size: ~1154 characters
```

Output:

```text
data/chunks/<VIDEO_ID>.json
```

---

# 🧾 Metadata Enrichment

Metadata enrichment connects video-level DSA information to individual
transcript chunks.

The metadata layer propagates:

```text
video_id
video_title
pattern
playlist
playlist_id
video_order
source_url
```

where available.

Sub-pattern behavior is intentionally conservative.

### If a chunk already has a valid sub-pattern

It is preserved.

### If the video contains exactly one sub-pattern

The chunk may inherit that sub-pattern.

### If the video contains multiple sub-patterns

The system does **not** guess.

The chunk remains without a sub-pattern unless it has explicit chunk-level
metadata.

This prevents an entire multi-topic video from being incorrectly labeled as
one sub-pattern.

---

# 🔢 Embedding Generation

Script:

```text
backend/scripts/ingest_embeddings.py
```

Embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Vector dimension:

```text
384
```

The ingestion pipeline:

```text
Chunk
  ↓
Metadata Enrichment
  ↓
English Text
  ↓
Embedding Model
  ↓
384-dimensional vector
  ↓
Qdrant
```

---

# 🗄️ Qdrant

Vector database:

```text
Qdrant
```

Collection:

```text
dsa_revision_chunks
```

Payload indexes currently include:

```text
pattern
sub_pattern
```

These indexes allow metadata-aware retrieval.

---

# 📥 Embedding Ingestion

Basic usage:

```powershell
python .\scripts\ingest_embeddings.py <VIDEO_ID> --pattern <PATTERN>
```

Example:

```powershell
python .\scripts\ingest_embeddings.py PvyEr3CeKzE --pattern two_pointer
```

With a sub-pattern:

```powershell
python .\scripts\ingest_embeddings.py dyG4JBKh6tA `
    --pattern dynamic_programming `
    --sub-pattern memoization
```

The ingestion pipeline validates the pattern against the canonical taxonomy.

A missing pattern is treated as an error rather than guessed.

---

# 🔍 Query Understanding

Script:

```text
backend/app/services/query_understanding.py
```

The query-understanding layer converts a natural-language query into structured
metadata.

Example:

```text
User:
"Explain dynamic programming memoization"

        ↓

Intent:
implementation

Pattern:
dynamic_programming

Sub-pattern:
memoization

Confidence:
0.99
```

Another example:

```text
User:
"How does two pointer work?"

        ↓

Intent:
how_it_works

Pattern:
two_pointer

Sub-pattern:
None
```

Supported query dimensions include:

```text
Intent
Pattern
Sub-pattern
Confidence
```

---

# 🎯 Query Intents

The current system recognizes intents such as:

```text
explanation
how_it_works
implementation
complexity
practice
comparison
optimization
```

The query understanding layer is intentionally separated from retrieval.

This keeps classification and search independently testable.

---

# 🔎 Metadata-Aware Retrieval

Script:

```text
backend/app/services/retrieval.py
```

Retrieval pipeline:

```text
User Query
    ↓
Query Understanding
    ↓
Pattern / Sub-pattern
    ↓
Query Embedding
    ↓
Qdrant Metadata Filter
    ↓
Vector Search
    ↓
Relevant Chunks
```

The retrieval service supports:

1. Pure semantic retrieval
2. Pattern-aware retrieval
3. Sub-pattern-aware retrieval
4. Safe semantic fallback
5. Structured retrieval results

---

# 🧩 Retrieval Result

Retrieved chunks are converted into a stable application-level result model.

A result contains:

```text
score
pattern
sub_pattern
playlist
video_id
video_title
chunk_id
start
end
duration
text
```

This prevents the rest of the application from depending directly on Qdrant's
internal response structure.

---

# 🧪 Testing

The project includes self-checks and integration tests.

## Taxonomy Self-check

Run:

```powershell
python .\app\services\dsa_taxonomy.py
```

Expected:

```text
VALIDATION : PASSED
```

The self-check validates:

* Canonical patterns
* Canonical sub-patterns
* Natural-language resolution
* Playlist mapping
* Unsupported-topic protection

---

## Query Understanding Self-check

Run:

```powershell
python -m app.services.query_understanding
```

Expected:

```text
Passed : 14
Failed : 0

✓ Self-check completed successfully.
```

The `-m` form is recommended because it executes the module from the backend
package context.

Running:

```powershell
python .\app\services\query_understanding.py
```

directly may cause:

```text
ModuleNotFoundError: No module named 'app'
```

because of Python package path resolution.

---

# 🔗 Retrieval Pipeline Integration Test

Script:

```text
backend/scripts/test_retrieval_pipeline.py
```

Run:

```powershell
python .\scripts\test_retrieval_pipeline.py
```

The integration test verifies:

```text
User Query
    ↓
Query Understanding
    ↓
Intent Validation
    ↓
Pattern Validation
    ↓
Sub-pattern Validation
    ↓
Metadata-Aware Retrieval
    ↓
Qdrant
    ↓
Retrieved Chunk Validation
```

The test validates that retrieved chunks satisfy the expected metadata
constraints.

Example:

```text
Expected pattern:
dynamic_programming

Expected sub-pattern:
memoization

Expected playlist:
DSA_Patterns_Dynamic_Programming
```

All returned chunks must satisfy these constraints.

---

# ✅ Current Validation Status

Current pipeline validation:

```text
DSA Taxonomy
    ✓ Passed

Query Understanding
    ✓ 14/14 checks passed

Retrieval Integration
    ✓ Dynamic Programming + Memoization
    ✓ Two Pointer

Retrieval Metadata Validation
    ✓ Pattern constraints
    ✓ Sub-pattern constraints
    ✓ Playlist constraints
```

Latest retrieval integration result:

```text
Total tests : 2
Passed      : 2
Failed      : 0

✓ All retrieval pipeline tests passed.
```

---

# ⚠️ Important Design Decisions

## 1. No Fake Pattern Generation

The system must not invent a pattern merely because a query contains a known
DSA term.

For example:

```text
"Explain bubble sort"
"Explain insertion sort"
"Explain selection sort"
"Explain radix sort"
"Explain heap sort"
```

must not automatically become:

```text
sorting_sweep
```

unless the taxonomy explicitly supports that concept as a valid pattern in the
relevant context.

This prevents retrieval from returning unrelated educational content.

---

## 2. Sorting Algorithms Are Not Automatically DSA Patterns

Algorithms such as:

```text
Bubble Sort
Insertion Sort
Selection Sort
Radix Sort
```

are not automatically treated as independent pattern categories.

The taxonomy represents **problem-solving patterns**, not every individual
algorithm.

---

## 3. Missing Metadata Is Safer Than Guessing

If the system cannot confidently determine a sub-pattern:

```text
sub_pattern = None
```

is preferred over assigning an incorrect label.

Incorrect metadata can permanently damage retrieval quality.

---

## 4. Playlist Names Come From the Taxonomy

The ingestion layer does not manually invent playlist names.

Instead:

```text
Canonical Pattern
      ↓
Taxonomy
      ↓
Playlist Name
```

This keeps metadata consistent across the system.

---

# 🔐 Environment Variables

Create:

```text
backend/.env
```

Example configuration:

```env
GROQ_API_KEY=your_key_here

QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key

QDRANT_COLLECTION=dsa_revision_chunks

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

SEARCH_TOP_K=5
FILTERED_SEARCH_MULTIPLIER=3
```

Never commit API keys to Git.

---

# 🚀 End-to-End Example

For a new YouTube video:

### Step 1 — Extract transcript

```powershell
python .\scripts\youtube_transcribe.py PvyEr3CeKzE
```

### Step 2 — Translate

```powershell
python .\scripts\translate_transcript.py PvyEr3CeKzE
```

### Step 3 — Chunk

```powershell
python .\scripts\chunk_transcript.py PvyEr3CeKzE
```

### Step 4 — Ingest embeddings

```powershell
python .\scripts\ingest_embeddings.py PvyEr3CeKzE --pattern two_pointer
```

### Step 5 — Run taxonomy validation

```powershell
python .\app\services\dsa_taxonomy.py
```

### Step 6 — Run query understanding validation

```powershell
python -m app.services.query_understanding
```

### Step 7 — Run retrieval integration test

```powershell
python .\scripts\test_retrieval_pipeline.py
```

---

# 🛣️ Roadmap

## Phase 1 — Foundation

* [x] YouTube transcript extraction
* [x] Transcript translation
* [x] Smart transcript chunking
* [x] Embedding generation
* [x] Qdrant ingestion

## Phase 2 — DSA Intelligence

* [x] Canonical DSA taxonomy
* [x] Pattern validation
* [x] Sub-pattern validation
* [x] Playlist mapping
* [x] Metadata enrichment
* [x] Pattern-aware retrieval
* [x] Query understanding
* [x] Intent classification

## Phase 3 — Revision Intelligence

* [ ] Evidence-grounded answer generation
* [ ] Context-aware revision explanations
* [ ] Timestamp-aware revision
* [ ] Topic completion tracking
* [ ] Pattern progress tracking

## Phase 4 — AI Practice Engine

After a learner completes a DSA pattern/topic:

```text
Completed Topic
      ↓
AI analyzes covered concepts
      ↓
Generate 4–5 problems
      ↓
No hints
      ↓
Learner solves
      ↓
AI evaluates solution
      ↓
Weakness detection
```

The goal is to test whether the learner can recognize and apply a pattern
without being explicitly told which pattern to use.

## Phase 5 — Adaptive Revision

Future versions will support:

```text
Learning History
      ↓
Weak Topic Detection
      ↓
Revision Recommendation
      ↓
Targeted Retrieval
      ↓
Practice
      ↓
Performance Tracking
      ↓
Adaptive Next Step
```

---

# 🧠 Long-Term Vision

The final system is intended to become more than a transcript search engine.

The long-term vision is:

```text
                    DSA Learning History
                            │
                            ▼
                    Pattern Knowledge
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        Revision Engine              Practice Engine
              │                           │
              ▼                           ▼
      Relevant Video Content        New Problems
              │                           │
              └─────────────┬─────────────┘
                            ▼
                     Learner Progress
                            │
                            ▼
                    Adaptive Revision
```

The system should gradually understand:

* What the learner has studied
* Which DSA patterns they know
* Which sub-patterns they have covered
* Which concepts are weak
* Which concepts need revision
* Which problems should be practiced next

---

# 🧰 Main Technologies

```text
Python
Sentence Transformers
Qdrant
Groq API
YouTube Transcript API
JSON-based intermediate storage
```

---

# 📌 Current Project Status

The current backend has a working:

```text
YouTube → Transcript → Translation → Chunking
        → Metadata → Embedding → Qdrant
        → Query Understanding → Retrieval
```

pipeline with successful taxonomy, query-understanding, and retrieval
integration validation.

The next major step is to move from **retrieval correctness** toward
**answer generation and adaptive DSA revision intelligence**.

```pattern/sub-pattern filtering architecture-ও current implementation অনুযায়ী রাখা হয়েছে। :contentReference[oaicite:2]{index=2}
```
