
# DSA Revision Analyzer

An AI-powered DSA revision system that converts educational video content into a
structured, searchable knowledge base and uses pattern-aware retrieval to provide
grounded revision support.

The system is designed around **DSA problem-solving patterns**, not individual
random problems.

---

# 🎯 Project Goal

The goal of DSA Revision Analyzer is to help a learner revise DSA concepts from
educational content they have already studied.

Instead of treating a YouTube transcript as plain text, the system builds a
structured knowledge pipeline:

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
Hybrid Search
      ↓
RRF Candidate Fusion
      ↓
Cross-Encoder Reranking
      ↓
Relevant Revision Context
      ↓
Grounded Answer Generation
````

The long-term system will also use completed topics and patterns to generate
**pattern-specific practice problems without hints**.

---

# 🧠 Core Architecture

The current system has evolved from a semantic-only retrieval system into a
hybrid retrieval and reranking architecture.

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
                         │ Translation → English│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Smart Chunking    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ DSA Taxonomy /       │
                         │ Metadata Enrichment  │
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
                         │ Confidence            │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Metadata Constraints │
                         └──────────┬───────────┘
                                    │
                      ┌─────────────┴─────────────┐
                      │                           │
                      ▼                           ▼
              ┌──────────────┐           ┌──────────────┐
              │   Semantic   │           │     BM25     │
              │    Search    │           │   Lexical    │
              │   Qdrant     │           │    Search    │
              └──────┬───────┘           └──────┬───────┘
                     │                          │
                     └────────────┬─────────────┘
                                  ▼
                         ┌──────────────────────┐
                         │ RRF Candidate Fusion │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  Candidate Pool      │
                         │  (Expanded Top-K)     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Cross-Encoder        │
                         │ Reranking            │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Final Top-K      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Context Assembly     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Grounded LLM Answer  │
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
│   │       ├── bm25_index.py
│   │       ├── hybrid_retrieval.py
│   │       ├── rrf.py
│   │       └── video_metadata_schema.py
│   │
│   ├── data/
│   │   ├── transcripts/
│   │   ├── translated/
│   │   ├── chunks/
│   │   └── bm25/
│   │
│   ├── scripts/
│   │   ├── youtube_transcribe.py
│   │   ├── translate_transcript.py
│   │   ├── chunk_transcript.py
│   │   ├── ingest_embeddings.py
│   │   ├── search_chunks.py
│   │   ├── search_bm25.py
│   │   ├── build_bm25_index.py
│   │   ├── test_retrieval_pipeline.py
│   │   ├── test_semantic_retrieval.py
│   │   ├── test_hybrid_retrieval.py
│   │   ├── test_rrf.py
│   │   │
│   │   ├── local_translation.py
│   │   ├── indictrans_onnx_test.py
│   │   ├── benchmark_indictrans.py
│   │   ├── benchmark_indictrans_50.py
│   │   ├── context_translation_test.py
│   │   └── test_local_context.py
│   │
│   ├── .env
│   ├── pyproject.toml
│   └── README.md
│
├── frontend/
│   └── ...
│
└── ...
```

The local IndicTrans2-related scripts are currently **experimental utilities**.
They are not part of the authoritative production translation pipeline.

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

The taxonomy intentionally contains only patterns relevant to the target DSA
learning system.

Individual sorting algorithms such as Bubble Sort, Insertion Sort, Selection
Sort, Radix Sort, etc. are **not treated as standalone DSA patterns**.

---

# 🏷️ Pattern and Sub-pattern Design

Each transcript chunk can contain canonical metadata such as:

```json
{
  "pattern": "two_pointer",
  "sub_pattern": "pair_search",
  "playlist": "DSA_Patterns_Two_Pointer"
}
```

The system maintains the hierarchy:

```text
Pattern
   ↓
Sub-pattern
   ↓
Transcript Chunks
```

Example:

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

Playlist names are **derived from the canonical taxonomy** rather than manually
constructed during ingestion.

This prevents inconsistent categories such as:

```text
Two Pointer
two-pointer
two pointer
2 pointer
```

from becoming separate metadata categories.

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
python .\scripts\youtube_transcribe.py Fu7LD_mIo00
```

Output:

```text
data/transcripts/<VIDEO_ID>.json
```

The transcript preserves:

* Video ID
* Video title
* Timestamp information
* Transcript segments
* Segment ordering

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
python .\scripts\translate_transcript.py Fu7LD_mIo00
```

Output:

```text
data/translated/<VIDEO_ID>.json
```

## Translation Model

Current production translation model:

```text
openai/gpt-oss-120b
```

Current batch size:

```text
25 segments
```

## Resume-Safe Translation

The translation pipeline is designed to survive temporary API failures and
rate-limit interruptions.

Successful batches are checkpointed to:

```text
data/translated/<VIDEO_ID>.partial.json
```

The checkpoint preserves:

* Video metadata
* Segment IDs
* Original transcript text
* English translation
* Start timestamp
* End timestamp
* Duration

If translation stops midway, the script can resume from the existing checkpoint
instead of retranslating completed segments.

After all segments are successfully translated:

```text
.partial.json
      ↓
final .json
```

The temporary checkpoint is then removed.

---

# 🧪 Local Translation Experiment

An offline IndicTrans2-based ONNX translation pipeline was also evaluated.

Relevant scripts include:

```text
backend/scripts/local_translation.py
backend/scripts/indictrans_onnx_test.py
backend/scripts/benchmark_indictrans.py
backend/scripts/benchmark_indictrans_50.py
backend/scripts/context_translation_test.py
backend/scripts/test_local_context.py
```

The tested model is:

```text
hari31416/indictrans2-indic-en-dist-200M-ONNX-int8
```

The model runs locally through ONNX Runtime and is suitable for CPU-based
experimentation.

However, contextual benchmark testing showed that the local model can introduce
semantic errors in conversational DSA explanations.

Therefore:

```text
Production translation
      ↓
Authoritative production translation

Local IndicTrans2
      ↓
Experimental / optional offline fallback
```

The local translation implementation is **not currently used to replace the
production translation pipeline**.

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
python .\scripts\chunk_transcript.py Fu7LD_mIo00
```

Output:

```text
data/chunks/<VIDEO_ID>.json
```

The chunking system creates semantically useful transcript chunks rather than
splitting the transcript at arbitrary fixed intervals.

Current configuration:

```text
Target characters : 1000
Maximum characters: 1400
Overlap segments  : 2
```

Timestamp information is retained so that future retrieval results can be
connected back to the original video location.

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

## Conservative Sub-pattern Assignment

### If a chunk already has a valid sub-pattern

It is preserved.

### If the video contains exactly one sub-pattern

The chunk may inherit that sub-pattern.

### If the video contains multiple sub-patterns

The system does **not guess**.

The chunk remains without a sub-pattern unless explicit chunk-level metadata
exists.

This prevents an entire multi-topic video from being incorrectly labeled as a
single sub-pattern.

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

The same embedding model must be used for both:

```text
Document Embeddings
        +
Query Embeddings
```

to keep vector retrieval consistent.

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

The Qdrant payload stores both transcript information and DSA metadata.

Important payload fields include:

```text
video_id
chunk_id
text
text_en
video_title
playlist
pattern
sub_pattern
video_sub_patterns
video_order
source_url
topic
start
end
duration
```

Payload indexes currently include:

```text
pattern
sub_pattern
```

These indexes support metadata-aware retrieval.

## Deterministic Point IDs

Qdrant point IDs are deterministically generated from:

```text
video_id + chunk_id
```

Therefore, re-running ingestion for the same chunk updates the corresponding
point rather than creating duplicate vector records.

---

# 📥 Embedding Ingestion

Basic usage:

```powershell
python .\scripts\ingest_embeddings.py <VIDEO_ID> --pattern <PATTERN>
```

Example:

```powershell
python .\scripts\ingest_embeddings.py Fu7LD_mIo00 --pattern two_pointer
```

With a sub-pattern:

```powershell
python .\scripts\ingest_embeddings.py dyG4JBKh6tA `
    --pattern dynamic_programming `
    --sub-pattern memoization
```

The ingestion pipeline validates the supplied pattern against the canonical
taxonomy.

A missing or invalid pattern is treated as an error rather than guessed.

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

The query-understanding layer is intentionally separated from retrieval so that
classification and search remain independently testable.

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

The classifier also protects the system against unsupported algorithm queries.

For example:

```text
merge sort
bubble sort
insertion sort
selection sort
quick sort
radix sort
heap sort
counting sort
```

must not automatically become a broader DSA pattern unless the canonical taxonomy
explicitly supports that classification.

---

# 🔎 Metadata-Aware Retrieval

Current stable retrieval implementation:

```text
backend/app/services/retrieval.py
```

The semantic retrieval pipeline is:

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

Supported behavior includes:

1. Pure semantic retrieval
2. Pattern-aware retrieval
3. Sub-pattern-aware retrieval
4. Safe semantic fallback
5. Structured retrieval results

Metadata constraints remain authoritative.

---

# 🔀 Phase 11 — Hybrid Search + Reranking

The retrieval architecture has now been extended beyond semantic-only retrieval.

Current Phase 11 pipeline:

```text
User Query
     ↓
Query Understanding
     ↓
Metadata Constraints
     ↓
 ┌──────────────────────────────┐
 │                              │
 ▼                              ▼
Semantic Search                BM25
(Qdrant)                     (Lexical)
 │                              │
 └──────────────┬───────────────┘
                ↓
        Candidate Retrieval
                ↓
        Reciprocal Rank Fusion
                ↓
          Expanded Candidate Pool
                ↓
        Cross-Encoder Reranking
                ↓
             Final Top-K
```

## 1. BM25 Lexical Search

BM25 provides lexical matching for important exact terms.

For example:

```text
sorted array
two pointer
left
right
merge
memoization
```

can receive strong lexical relevance.

The BM25 index is stored locally and can be reused instead of rebuilding the
lexical index for every query.

---

## 2. Semantic Candidate Retrieval

Semantic retrieval continues to use Qdrant and the existing embedding model.

For hybrid retrieval, the system retrieves an expanded candidate pool rather
than immediately returning the final Top-K.

Example:

```text
Final Top-K = 5
Candidate multiplier = 3

5 × 3 = 15 candidates
```

This gives later ranking stages more candidates to evaluate.

---

## 3. Reciprocal Rank Fusion

Semantic and BM25 rankings are combined using **Reciprocal Rank Fusion
(RRF)**.

RRF combines rankings rather than directly adding raw scores from different
retrieval systems.

Conceptually:

```text
Semantic Ranking
      +
BM25 Ranking
      ↓
RRF
      ↓
Unified Candidate Ranking
```

The implementation uses a configurable RRF constant:

```text
RRF K = 60
```

The RRF layer preserves stable document/point IDs so that candidates from
different retrievers can be matched correctly.

---

## 4. Current Hybrid Retrieval Validation

The hybrid retrieval integration test currently validates:

```text
✓ Query validation
✓ Metadata filter validation
✓ Semantic candidate retrieval
✓ BM25 candidate retrieval
✓ Candidate ID compatibility
✓ Cross-retriever overlap
✓ RRF fusion
✓ Stable point ID preservation
✓ Final Top-K constraint
✓ Metadata restoration
```

A representative test produced:

```text
Semantic candidates : 15
BM25 candidates     : 3
Overlapping points  : 3
Final fused results : 5
```

The complete hybrid retrieval test passed successfully.

Example command:

```powershell
python scripts/test_hybrid_retrieval.py
```

---

## 5. Cross-Encoder Reranking

**Current Phase 11 remaining major component:**

```text
Cross-Encoder Reranking
```

The cross-encoder evaluates the query and candidate chunk together:

```text
(query, candidate_chunk)
          ↓
    Cross-Encoder
          ↓
  relevance score
```

Unlike independent embedding similarity, the cross-encoder can evaluate the
relationship between the query and candidate text directly.

The intended final pipeline is:

```text
Semantic Search
      +
BM25
      ↓
RRF
      ↓
Candidate Pool
      ↓
Cross-Encoder
      ↓
Reranked Candidates
      ↓
Final Top-K
```

Cross-encoder reranking is **not yet marked complete** until its implementation,
integration, and validation are finished.

---

# 🧩 Retrieval Result

Retrieved chunks are converted into a stable application-level result model.

A result currently contains:

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

This abstraction prevents the rest of the application from depending directly on
Qdrant's internal response structures.

During hybrid retrieval, internal candidate objects may additionally track:

```text
semantic_score
bm25_score
rrf_score
reranker_score
final_score
```

These internal scores do not need to become part of the public retrieval
contract.

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

# Query Understanding Self-check

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

The integration test validates:

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

The test verifies that retrieved chunks satisfy the expected metadata
constraints.

---

# 🔀 Hybrid Retrieval Integration Test

Script:

```text
backend/scripts/test_hybrid_retrieval.py
```

Run:

```powershell
python .\scripts\test_hybrid_retrieval.py
```

The current integration test validates:

```text
User Query
      ↓
Query Understanding
      ↓
Metadata Constraints
      ↓
 ┌──────────────┐
 │              │
 ▼              ▼
Semantic       BM25
 │              │
 └──────┬───────┘
        ↓
       RRF
        ↓
   Final Top-K
```

Current validation result:

```text
✓ Semantic retrieval validated
✓ BM25 retrieval validated
✓ RRF fusion validated
✓ Stable point_id preservation validated
✓ Final Top-K constraint passed
✓ Metadata restoration passed

✓ COMPLETE HYBRID RETRIEVAL TEST PASSED
```

Cross-encoder-specific validation will be added after the reranker is integrated.

---

# 📊 Current Validation Status

Current backend foundation:

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

Hybrid Retrieval
    ✓ Semantic candidate retrieval
    ✓ BM25 candidate retrieval
    ✓ RRF fusion
    ✓ Candidate compatibility
    ✓ Final Top-K
    ✓ Metadata restoration

Cross-Encoder
    ⏳ Pending
```

The semantic retrieval foundation is working and validated.

The hybrid retrieval foundation is also working and validated.

The project is now completing the final component of Phase 11:

```text
Retrieval Correctness
        ↓
Hybrid Search
        ↓
RRF Fusion
        ↓
Cross-Encoder Reranking  ← CURRENT TASK
        ↓
Retrieval Quality
        ↓
Context Assembly
        ↓
Grounded Generation
```

---

# ⚠️ Important Design Decisions

## 1. No Fake Pattern Generation

The system must not invent a pattern merely because a query contains a known DSA
term.

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

unless the taxonomy explicitly supports that concept in the relevant context.

---

## 2. DSA Patterns Are Not Individual Algorithms

The taxonomy represents **problem-solving patterns**, not every individual
algorithm.

Therefore, algorithms such as:

```text
Bubble Sort
Insertion Sort
Selection Sort
Radix Sort
```

are not automatically independent pattern categories.

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

## 5. Metadata Filtering Remains Authoritative

Hybrid retrieval must respect pattern and sub-pattern constraints.

The intended order is:

```text
Query Understanding
      ↓
Metadata Constraints
      ↓
Semantic Search + BM25
      ↓
RRF
      ↓
Cross-Encoder Reranking
      ↓
Final Top-K
```

Metadata filtering should not be treated as an optional ranking signal when the
query explicitly specifies a supported pattern or sub-pattern.

---

## 6. Translation Quality Matters

Translation is part of the retrieval foundation.

The pipeline is:

```text
Translation
      ↓
Chunking
      ↓
Embedding
      ↓
Retrieval
      ↓
RAG
```

Therefore, translation errors can propagate into chunking, embeddings, retrieval,
and ultimately generated answers.

For this reason, the higher-quality production translation pipeline remains the
authoritative path.

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

EMBEDDING_BATCH_SIZE=32

SEARCH_TOP_K=5
FILTERED_SEARCH_MULTIPLIER=3

RRF_K=60
```

Never commit API keys or other secrets to Git.

---

# 🚀 End-to-End Example

For a new YouTube video:

## Step 1 — Extract transcript

```powershell
python .\scripts\youtube_transcribe.py <VIDEO_ID>
```

## Step 2 — Translate

```powershell
python .\scripts\translate_transcript.py <VIDEO_ID>
```

## Step 3 — Chunk

```powershell
python .\scripts\chunk_transcript.py <VIDEO_ID>
```

## Step 4 — Build / update BM25 index

```powershell
python .\scripts\build_bm25_index.py
```

## Step 5 — Ingest embeddings

```powershell
python .\scripts\ingest_embeddings.py <VIDEO_ID> --pattern <PATTERN>
```

## Step 6 — Run taxonomy validation

```powershell
python .\app\services\dsa_taxonomy.py
```

## Step 7 — Run query understanding validation

```powershell
python -m app.services.query_understanding
```

## Step 8 — Run semantic retrieval integration test

```powershell
python .\scripts\test_retrieval_pipeline.py
```

## Step 9 — Run hybrid retrieval integration test

```powershell
python .\scripts\test_hybrid_retrieval.py
```

---

# 🛣️ Roadmap

## Phase 1 — Foundation

* [x] Project structure
* [x] Environment configuration
* [x] Core backend foundation

## Phase 2 — YouTube Transcript Ingestion

* [x] YouTube transcript extraction
* [x] Transcript storage
* [x] Timestamp preservation

## Phase 3 — Transcript Translation

* [x] Translation pipeline
* [x] Batched translation
* [x] Retry handling
* [x] Resume-safe checkpoints
* [ ] Complete translation of the remaining representative dataset

## Phase 4 — Intelligent Transcript Chunking

* [x] Character-aware chunking
* [x] Chunk overlap
* [x] Timestamp preservation
* [x] Chunk JSON generation

## Phase 5 — Embedding Generation

* [x] Sentence Transformer integration
* [x] 384-dimensional embeddings
* [x] Local embedding generation

## Phase 6 — Qdrant Vector Database

* [x] Qdrant collection
* [x] Vector ingestion
* [x] Payload metadata
* [x] Payload indexes
* [x] Deterministic point IDs

## Phase 7 — Semantic Retrieval

* [x] Query embedding
* [x] Vector search
* [x] Top-K retrieval
* [x] Structured retrieval results

## Phase 8 — DSA Knowledge & Metadata Layer

* [x] Canonical DSA taxonomy
* [x] Sub-pattern taxonomy
* [x] Playlist mapping
* [x] Metadata validation
* [x] Chunk metadata enrichment

## Phase 9 — Query Understanding

* [x] Intent classification
* [x] Pattern detection
* [x] Sub-pattern detection
* [x] Confidence scoring
* [x] Unsupported algorithm protection

## Phase 10 — Metadata-Aware Retrieval

* [x] Pattern filtering
* [x] Sub-pattern filtering
* [x] Metadata validation
* [x] Safe fallback behavior
* [x] Retrieval integration testing

## Phase 11 — Hybrid Search + Reranking

* [x] BM25 lexical search
* [x] Reusable BM25 index
* [x] Semantic + lexical candidate retrieval
* [x] Reciprocal Rank Fusion
* [x] RRF integration
* [x] Candidate pool generation
* [x] Final Top-K after RRF
* [ ] Cross-encoder reranking
* [ ] Reranker integration with hybrid retrieval
* [ ] Reranked Top-K validation
* [ ] Phase 11 end-to-end retrieval quality validation

### Current Phase 11 Status

```text
BM25
   ↓
Semantic + BM25 Candidate Retrieval
   ↓
RRF Fusion
   ↓
Final Candidate Pool
   ↓
Cross-Encoder Reranking  ← NEXT
   ↓
Final Top-K
```

Phase 11 is **not yet complete** until the cross-encoder stage and its
integration tests pass.

---

## Phase 12 — Context Assembly

* [ ] Context selection
* [ ] Context deduplication
* [ ] Relevance ordering
* [ ] Token-aware context construction

## Phase 13 — Grounded RAG Generation

* [ ] LLM answer generation
* [ ] Source-grounded responses
* [ ] Retrieval-context prompting
* [ ] Hallucination-aware answer structure

## Phase 14 — Timestamp-Aware Retrieval

* [ ] Timestamp-aware result formatting
* [ ] Video jump links
* [ ] Relevant time-range extraction
* [ ] Timestamp-grounded explanations

## Phase 15 — FastAPI Backend

* [ ] Retrieval API
* [ ] Query API
* [ ] RAG API
* [ ] Metadata endpoints
* [ ] Request validation

## Phase 16 — React Frontend

* [ ] Search interface
* [ ] Revision interface
* [ ] Retrieved source display
* [ ] Video/timestamp navigation

## Phase 17 — Pattern / Playlist Navigation

* [ ] Pattern browser
* [ ] Playlist navigation
* [ ] Video ordering
* [ ] Topic progression

## Phase 18 — Adaptive Practice System

After completing a topic or pattern:

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
```

The goal is to test whether the learner can recognize and apply a DSA pattern
without being explicitly told which pattern to use.

## Phase 19 — Performance & Weakness Detection

* [ ] Track practice performance
* [ ] Detect weak sub-patterns
* [ ] Detect recurring mistakes
* [ ] Identify knowledge gaps

## Phase 20 — Adaptive Revision Engine

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

## Phase 21 — Evaluation System

* [ ] Retrieval evaluation dataset
* [ ] Recall@K
* [ ] Precision@K
* [ ] MRR
* [ ] Reranking evaluation
* [ ] RAG answer evaluation

## Phase 22 — Automated Testing

* [ ] Unit tests
* [ ] Integration tests
* [ ] Retrieval regression tests
* [ ] API tests
* [ ] End-to-end tests

## Phase 23 — Production Hardening

* [ ] Logging
* [ ] Error handling
* [ ] Performance optimization
* [ ] Model caching
* [ ] Security hardening
* [ ] Configuration cleanup

## Phase 24 — Deployment

* [ ] Backend deployment
* [ ] Frontend deployment
* [ ] Production Qdrant
* [ ] Monitoring
* [ ] Production documentation

---

# 🧠 Long-Term Vision

The final system is intended to become more than a transcript search engine.

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
BM25
Reciprocal Rank Fusion (RRF)
Cross-Encoder
ONNX Runtime
JSON-based intermediate storage
```

---

# 📌 Current Project Status

The DSA Revision Analyzer currently has a working and validated retrieval
foundation:

```text
YouTube
   ↓
Transcript
   ↓
Translation
   ↓
Chunking
   ↓
Metadata
   ↓
Embedding
   ↓
Qdrant
   ↓
Query Understanding
   ↓
Metadata-Aware Semantic Retrieval
   ↓
BM25
   ↓
RRF Fusion
   ↓
Candidate Pool
```

The project has completed the core retrieval foundation through **Phase 10**.

**Phase 11 is currently in progress.**

Completed:

```text
Semantic Retrieval
      ✓

BM25
      ✓

Hybrid Candidate Retrieval
      ✓

RRF Fusion
      ✓

Final Top-K after RRF
      ✓

Hybrid Integration Tests
      ✓
```

Remaining:

```text
Cross-Encoder Reranking
      ↓
Reranker Integration
      ↓
Reranked Top-K Validation
      ↓
Phase 11 Completion
```

After retrieval quality is fully improved, development will move toward:

```text
Context Assembly
      ↓
Grounded RAG Generation
      ↓
Timestamp-Aware Revision
      ↓
Adaptive Practice
      ↓
Weakness Detection
      ↓
Adaptive Revision
```

The long-term objective is to transform the project from a
**transcript retrieval system** into an **adaptive AI-powered DSA revision and
practice engine**.

