# DSA Revision Analyzer

An AI-powered DSA revision system that converts educational video content into a
structured, searchable knowledge base and uses pattern-aware hybrid retrieval,
reranking, and grounded context construction to provide revision support.

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
Context Assembly
      ↓
Grounded Answer Generation
````

The long-term system will also use completed topics and patterns to generate
**pattern-specific practice problems without hints**.

---

# 🧠 Core Architecture

The current system uses a hybrid retrieval architecture with lexical search,
semantic search, Reciprocal Rank Fusion, Cross-Encoder reranking, and structured
context assembly.

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
                       ┌────────────┴────────────┐
                       │                         │
                       ▼                         ▼
               ┌──────────────┐          ┌──────────────┐
               │   Semantic   │          │     BM25     │
               │    Search    │          │   Lexical    │
               │   Qdrant     │          │    Search    │
               └──────┬───────┘          └──────┬───────┘
                      │                         │
                      └────────────┬────────────┘
                                   ▼
                          ┌──────────────────┐
                          │   RRF Fusion     │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Candidate Pool   │
                          │   Expanded K     │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Cross-Encoder    │
                          │    Reranking     │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │    Final Top-K   │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Context Assembly │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Grounded LLM     │
                          │     Answer       │
                          └──────────────────┘
```

---

# 🔀 Hybrid Retrieval + Reranking

The retrieval system combines multiple retrieval and ranking stages:

```text
User Query
    ↓
Query Understanding
    ↓
Metadata Constraints
    ↓
┌───────────────────────┐
│                       │
▼                       ▼
Semantic Search         BM25
(Qdrant)                (Lexical)
│                       │
└───────────┬───────────┘
            ↓
     Candidate Retrieval
            ↓
       RRF Fusion
            ↓
   Expanded Candidate Pool
            ↓
   Cross-Encoder Reranking
            ↓
       Final Top-K
            ↓
     Context Assembly
```

## Candidate Expansion

The system retrieves more candidates before final reranking.

Current configuration:

```text
Final Top-K         : 5
Candidate multiplier: 3
Candidate K         : 15
RRF K               : 60
```

Therefore:

```text
5 final results × 3 candidate multiplier
= 15 reranking candidates
```

This allows the Cross-Encoder to evaluate a larger candidate pool before
selecting the final context.

---

# 🔬 Cross-Encoder Reranking

The Cross-Encoder evaluates the query and candidate chunk together:

```text
(query, candidate_chunk)
          ↓
    Cross-Encoder
          ↓
   relevance score
```

This differs from embedding retrieval, where query and documents are encoded
independently.

The current retrieval flow is:

```text
Semantic Search
      +
BM25 Search
      ↓
RRF Fusion
      ↓
Candidate Pool
      ↓
Cross-Encoder
      ↓
Reranked Candidates
      ↓
Final Top-K
```

Implementation:

```text
backend/app/services/reranker.py
```

Hybrid retrieval integration:

```text
backend/app/services/hybrid_retrieval.py
```

Benchmark:

```text
backend/scripts/benchmark_reranking.py
```

The reranking benchmark currently records:

```text
RRF-only latency
Full-pipeline latency
Cross-Encoder stage latency
RRF ranking
Cross-Encoder scores
Top-K ranking movement
```

The benchmark does **not** claim retrieval relevance improvement because
human-validated ground-truth relevance labels are not available yet.

Future evaluation can introduce:

```text
Recall@K
Precision@K
MRR
nDCG@K
Reranking quality
```

---

# 🧩 Context Assembly

## Phase 12 — Context Assembly

The context assembly layer converts final reranked retrieval results into a
structured context suitable for downstream LLM generation.

Implementation:

```text
backend/app/services/context_assembler.py
```

The context assembly layer is responsible for:

```text
Final reranked results
        ↓
Top-K enforcement
        ↓
Duplicate removal
        ↓
Metadata preservation
        ↓
Score preservation
        ↓
Stable ranking
        ↓
LLM-ready context
```

Each context item preserves:

```text
rank
point_id
text
video_id
pattern
sub_pattern
timestamp_start
timestamp_end
rrf_score
reranker_score
```

The assembled context also provides deterministic text generation for
downstream LLM prompting.

Example structure:

```text
[Context 1]
Point ID: ...
Video ID: ...
Pattern: dynamic_programming
Sub-pattern: memoization
Timestamp: ...
 
<retrieved chunk text>
```

The context object can also be serialized into a JSON-compatible dictionary.

---

# 🧪 Context Assembly Validation

Unit-level context assembly validation:

```text
backend/scripts/test_context_assembly.py
```

Current validation:

```text
✓ Top-K limit
✓ Reranked order preservation
✓ Chunk text preservation
✓ Metadata preservation
✓ Score preservation
✓ Duplicate handling
✓ Empty result handling
✓ Context text generation
✓ Dictionary serialization
```

Result:

```text
Passed : 9/9

✓ CONTEXT ASSEMBLY TEST PASSED
```

---

# 🔗 Context Integration

Integration validation:

```text
backend/scripts/test_context_integration.py
```

The integration pipeline validates:

```text
Hybrid Retrieval
      ↓
RRF Fusion
      ↓
Cross-Encoder Reranking
      ↓
Final Top-K
      ↓
Context Assembly
      ↓
Metadata Preservation
      ↓
Score Preservation
      ↓
LLM-Ready Context
      ↓
Serialization
```

Current integration checks include:

```text
✓ Hybrid retrieval completed
✓ RRF fusion completed
✓ Cross-Encoder reranking completed
✓ Final Top-K validated
✓ Context Assembly completed
✓ Context metadata preserved
✓ Stable point IDs preserved
✓ Chunk text preserved
✓ RRF scores preserved
✓ Cross-Encoder scores preserved
✓ LLM-ready context generated
✓ Dictionary serialization validated
```

Current integration result:

```text
✓ PHASE 12 CONTEXT INTEGRATION PASSED
```

---

# 📊 Current Validation Status

```text
DSA Taxonomy
    ✓ Passed

Query Understanding
    ✓ Passed

Semantic Retrieval
    ✓ Passed

Metadata-Aware Retrieval
    ✓ Passed

BM25 Retrieval
    ✓ Passed

Hybrid Candidate Retrieval
    ✓ Passed

RRF Fusion
    ✓ Passed

Cross-Encoder Reranking
    ✓ Passed

Hybrid + Reranking Integration
    ✓ Passed

Context Assembly
    ✓ 9/9 checks passed

Context Integration
    ✓ Passed
```

The current validated retrieval-to-context pipeline is:

```text
Query
  ↓
Query Understanding
  ↓
Metadata Constraints
  ↓
Semantic Search + BM25
  ↓
RRF Fusion
  ↓
Candidate Pool
  ↓
Cross-Encoder Reranking
  ↓
Final Top-K
  ↓
Context Assembly
  ↓
LLM-Ready Context
```

---

# 🧪 Testing

## Hybrid Retrieval Test

Run:

```powershell
python .\scripts\test_hybrid_retrieval.py
```

## Cross-Encoder Benchmark

Run:

```powershell
python .\scripts\benchmark_reranking.py
```

## Context Assembly Test

Run:

```powershell
python .\scripts\test_context_assembly.py
```

## Context Integration Test

Run:

```powershell
python .\scripts\test_context_integration.py
```

The context integration test validates the complete retrieval-to-context path.

---

# 🗂️ Project Structure

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
│   │       ├── reranker.py
│   │       ├── context_assembler.py
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
│   │   ├── benchmark_reranking.py
│   │   ├── test_context_assembly.py
│   │   ├── test_context_integration.py
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

`__pycache__` and generated `.pyc` files are development artifacts and should
not be committed to the repository.

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
* [x] Cross-Encoder reranking
* [x] Reranker integration with hybrid retrieval
* [x] Reranked Top-K validation
* [x] Phase 11 integration validation
* [x] Reranking benchmark

### Phase 11 Final Pipeline

```text
BM25
   ↓
Semantic + BM25 Candidate Retrieval
   ↓
RRF Fusion
   ↓
Expanded Candidate Pool
   ↓
Cross-Encoder Reranking
   ↓
Final Top-K
```

**Phase 11: COMPLETE**

---

## Phase 12 — Context Assembly

* [x] Context selection
* [x] Context deduplication
* [x] Relevance ordering
* [x] Top-K enforcement
* [x] Metadata preservation
* [x] Score preservation
* [x] Stable point ID preservation
* [x] LLM-ready context construction
* [x] Context serialization
* [x] Context assembly validation
* [x] End-to-end context integration validation

### Phase 12 Final Pipeline

```text
Final Reranked Top-K
        ↓
Context Assembly
        ↓
Deduplication
        ↓
Metadata + Score Preservation
        ↓
LLM-Ready Context
```

**Phase 12: COMPLETE**

---

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
* [ ] nDCG@K
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

# 📌 Current Project Status

The project has now completed the retrieval and context-construction
foundation through **Phase 12**.

Current validated pipeline:

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
Metadata-Aware Retrieval
   ↓
BM25
   ↓
RRF Fusion
   ↓
Candidate Pool
   ↓
Cross-Encoder Reranking
   ↓
Final Top-K
   ↓
Context Assembly
   ↓
LLM-Ready Context
```

Completed:

```text
Phase 1   ✓
Phase 2   ✓
Phase 3   ✓* 
Phase 4   ✓
Phase 5   ✓
Phase 6   ✓
Phase 7   ✓
Phase 8   ✓
Phase 9   ✓
Phase 10  ✓
Phase 11  ✓
Phase 12  ✓
```

`*` Phase 3 still contains the remaining representative-dataset translation
work.

The next major development stage is:

```text
Phase 13 — Grounded RAG Generation
```

which will consume the structured context produced by Phase 12.

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
      ↓
Context Assembly
```

Metadata filtering should not be treated as an optional ranking signal when the
query explicitly specifies a supported pattern or sub-pattern.

---

## 6. Translation Quality Matters

Translation is part of the retrieval foundation.

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

