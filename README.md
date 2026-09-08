# DSA Revision Analyzer

An AI-powered, timestamp-aware RAG system for learning and
revising DSA concepts directly from YouTube lectures.

The system is designed around a simple idea:

> Ask a DSA question → find the most relevant lecture section
> → identify the exact video → identify the exact timestamp
> → open that part directly in the UI.

---

# 1. Problem Statement

When revising DSA, the actual problem is often not understanding
the concept itself.

The problem is finding where the concept was explained.

For example:

Suppose the user remembers that a Two Pointer concept was
explained somewhere inside a playlist containing 6-7 videos.

Without an intelligent retrieval system, the user may need to:

1. Open every video.
2. Search through the lecture.
3. Remember approximately where the concept was discussed.
4. Watch multiple unrelated sections.
5. Finally find the required explanation.

This project aims to automate that process.

Instead of searching manually:

```text
User Question
      ↓
AI Retrieval
      ↓
Relevant Video
      ↓
Relevant Timestamp
      ↓
Direct Revision
````

---

# 2. Main Goal

Build a DSA-specific RAG system that understands a complete
YouTube DSA course and can retrieve the most relevant lecture
section for a user's question.

The system should preserve:

* Video identity
* Playlist/pattern information
* Transcript
* English translation
* Timestamp
* DSA pattern
* DSA sub-pattern
* Relevant contextual chunks

---

# 3. Core User Experience

The intended user experience is:

```text
User asks:

"Explain the two pointer pattern where
both pointers move towards each other."
```

The system should:

```text
1. Understand the query.
2. Identify the DSA pattern.
3. Identify the relevant sub-pattern.
4. Search only the relevant knowledge space.
5. Retrieve the most relevant transcript chunks.
6. Identify the source video.
7. Identify the exact timestamp.
8. Generate a concise explanation.
9. Show the relevant video section in the UI.
```

---

# 4. Planned Architecture

```text
                ┌─────────────────────┐
                │      Frontend       │
                │      React UI       │
                └──────────┬──────────┘
                           │
                           │ REST API
                           ▼
                ┌─────────────────────┐
                │       FastAPI       │
                │      Backend        │
                └──────────┬──────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    Query Analysis      Retrieval        Generation
          │                │                │
          │                ▼                │
          │             Qdrant              │
          │          Vector Database        │
          │                                 │
          └───────────────┬─────────────────┘
                          │
                          ▼
                        Groq
                          │
                          ▼
                   Final Answer
```

---

# 5. Current Data Pipeline

The ingestion and retrieval pipeline currently processes
YouTube lecture transcripts through multiple stages.

```text
YouTube Video
      ↓
Transcript Extraction
      ↓
Timestamped Transcript
      ↓
English Translation
      ↓
Smart Chunking
      ↓
Chunked Transcript
      ↓
Embedding Generation
      ↓
Qdrant Vector Ingestion
      ↓
Semantic Retrieval
```

The complete ingestion pipeline currently consists of:

```text
youtube_transcribe.py
      ↓
translate_transcript.py
      ↓
chunk_transcript.py
      ↓
ingest_embeddings.py
```

The retrieval pipeline currently uses:

```text
search_chunks.py
      ↓
Query Embedding
      ↓
Qdrant Similarity Search
      ↓
Top-K Relevant Chunks
```

---

# 6. Implemented Components

## 6.1 YouTube Transcript Extraction

File:

```text
backend/scripts/youtube_transcribe.py
```

Purpose:

* Extract transcript segments from a YouTube video.
* Preserve the original transcript text.
* Preserve segment-level timestamps.
* Store video metadata.
* Save the transcript as JSON.

Output location:

```text
backend/data/transcripts/<video_id>.json
```

Each transcript segment preserves information such as:

* `segment_id`
* `start`
* `end`
* `duration`
* `text`

This timestamp information is important for the final
timestamp-aware retrieval experience.

---

## 6.2 Transcript Translation

File:

```text
backend/scripts/translate_transcript.py
```

Purpose:

* Read the timestamped transcript.
* Translate transcript text into English.
* Process segments in batches.
* Validate that translated output maps correctly to the
  original segment indexes.
* Retry failed batches.
* Preserve the original timestamps and transcript structure.

Output location:

```text
backend/data/translated/<video_id>.json
```

The translated transcript adds:

```text
text_en
```

while keeping the original:

```text
text
```

This allows the system to retain both the original transcript
and the English representation used by downstream retrieval.

---

## 6.3 Smart Transcript Chunking

File:

```text
backend/scripts/chunk_transcript.py
```

Purpose:

* Convert many small transcript segments into meaningful
  retrieval chunks.
* Keep individual transcript segments intact.
* Prefer natural sentence boundaries.
* Keep chunks around a configurable target size.
* Apply a maximum chunk size.
* Preserve timestamp information.
* Add a small overlap between neighboring chunks.
* Prevent duplicate tail chunks when the final chunk already
  reaches the end of the transcript.

Current default configuration:

```text
Target characters : 1000
Maximum characters: 1400
Overlap segments  : 2
```

Output location:

```text
backend/data/chunks/<video_id>.json
```

Each chunk contains:

* `video_id`
* `chunk_id`
* `segment_start`
* `segment_end`
* `start`
* `end`
* `duration`
* `text`
* `text_en`
* `segment_count`

Example flow:

```text
566 transcript segments
          ↓
   Smart Chunking
          ↓
   Meaningful chunks
          ↓
   Timestamp-aware JSON
```

The chunking stage is deterministic and currently does not
require an additional NLP dependency.

---

## 6.4 Embedding Generation and Qdrant Ingestion

File:

```text
backend/scripts/ingest_embeddings.py
```

Purpose:

* Read processed transcript chunks.
* Prepare searchable English text.
* Generate dense vector embeddings.
* Create the Qdrant collection when required.
* Store embeddings together with chunk metadata.
* Upload the vectors to Qdrant.

Current embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Current vector dimension:

```text
384
```

Current Qdrant collection:

```text
dsa_revision_chunks
```

The ingestion pipeline preserves important chunk metadata,
including:

* Video ID
* Chunk ID
* Segment range
* Start timestamp
* End timestamp
* Transcript text
* English transcript text
* Segment count

Example flow:

```text
Chunked Transcript
        ↓
Embedding Model
        ↓
384-dimensional vectors
        ↓
Qdrant
        ↓
dsa_revision_chunks
```

---

## 6.5 Semantic Chunk Retrieval

File:

```text
backend/scripts/search_chunks.py
```

Purpose:

* Accept a natural-language search query.
* Generate an embedding for the query.
* Search the Qdrant vector collection.
* Retrieve the most semantically similar transcript chunks.
* Display retrieval scores and timestamp information.

Example:

```bash
python .\scripts\search_chunks.py "dynamic programming recursion"
```

A custom Top-K value can also be provided:

```bash
python .\scripts\search_chunks.py "dynamic programming recursion" 10
```

The current retrieval output includes:

* Similarity score
* Video ID
* Chunk ID
* Segment range
* Start timestamp
* End timestamp
* English transcript
* Original transcript

Example:

```text
Query:
dynamic programming recursion

        ↓

Query Embedding
        ↓

Qdrant Semantic Search
        ↓

Top-K Results
        ↓

Relevant Chunks
        ↓

Timestamp Information
```

The current retrieval implementation is based on semantic
similarity. Query classification, DSA pattern detection,
metadata filtering, and reranking are planned for later stages.

---

# 7. Data Directory Structure

```text
backend/
│
├── data/
│   ├── transcripts/
│   │   └── <video_id>.json
│   │
│   ├── translated/
│   │   └── <video_id>.json
│   │
│   └── chunks/
│       └── <video_id>.json
│
├── scripts/
│   ├── youtube_transcribe.py
│   ├── translate_transcript.py
│   ├── chunk_transcript.py
│   ├── ingest_embeddings.py
│   └── search_chunks.py
│
└── app/
    └── services/
        └── vector_store.py
```

Generated data files are kept separate from the processing
scripts so that the ingestion pipeline remains organized.

---

# 8. Current Retrieval Metadata

The current vector ingestion layer stores chunk-level metadata
required for timestamp-aware retrieval.

Current metadata includes:

* Video ID
* Chunk ID
* Segment range
* Start timestamp
* End timestamp
* Duration
* Transcript text
* English transcript text
* Segment count

The final retrieval layer is expected to extend this metadata
with:

* Video title
* Playlist
* DSA pattern
* DSA sub-pattern

This metadata will allow retrieval to become more precise than
pure semantic similarity.

---

# 9. Current Retrieval Pipeline

The currently implemented retrieval workflow is:

```text
User Query
      ↓
Query Embedding
      ↓
Qdrant Vector Search
      ↓
Top-K Semantic Results
      ↓
Relevant Transcript Chunks
      ↓
Timestamp Information
```

For example:

```text
"d​​ynamic programming recursion"
```

can retrieve lecture chunks containing discussions around:

* Recursion
* Dynamic Programming
* Overlapping subproblems
* Memoization
* Tabulation
* Space optimization

The retrieved chunks retain their original lecture timestamps,
which will later allow the frontend to navigate directly to the
relevant section of the YouTube video.

---

# 10. Planned RAG Pipeline

The planned complete RAG workflow is:

```text
User Question
      ↓
Query Understanding
      ↓
Pattern Detection
      ↓
Sub-pattern Detection
      ↓
Metadata Filtering
      ↓
Vector Retrieval
      ↓
Reranking
      ↓
Relevant Lecture Chunks
      ↓
Timestamp Resolution
      ↓
Grounded LLM Generation
      ↓
Final Answer + Video Timestamp
```

The LLM should generate answers from retrieved lecture evidence
rather than relying only on its general knowledge.

---

# 11. Planned Query Intelligence

The current system performs semantic retrieval directly from the
user's query.

The next retrieval intelligence layer will analyze the query
before searching.

Example:

```text
User Query:

"Explain the two pointer pattern where
both pointers move towards each other."
```

Planned analysis:

```text
Pattern:
Two Pointer

Sub-pattern:
Opposite Direction

Intent:
Concept Explanation
```

The analyzed query can then be used for:

```text
Query
  ↓
Pattern Detection
  ↓
Sub-pattern Detection
  ↓
Metadata Filtering
  ↓
Semantic Retrieval
  ↓
Reranking
```

This should reduce irrelevant retrieval results and improve
DSA-specific search precision.

---

# 12. Planned Adaptive Practice System

After completing a DSA pattern or playlist, the system is
planned to generate practice problems based on the concepts
covered in the lectures.

Example:

```text
Two Pointer Pattern
      ↓
Lecture Completion
      ↓
Concept / Sub-pattern Analysis
      ↓
4-5 Practice Problems
      ↓
No Hint
      ↓
User Attempts
      ↓
Performance Tracking
      ↓
Weakness Detection
      ↓
Targeted Revision
```

The goal is to make the system adaptive rather than simply
providing static questions.

---

# 13. Planned Technology Stack

### Backend

* Python
* FastAPI

### Retrieval

* Qdrant
* Sentence Transformers
* Vector embeddings
* Hybrid / metadata-aware retrieval
* Reranking

### LLM

* Groq

### Frontend

* React

### Data Sources

* YouTube lecture transcripts

---

# 14. Current Development Status

## Completed

* [x] YouTube transcript extraction
* [x] Timestamp preservation
* [x] Transcript JSON storage
* [x] English transcript translation
* [x] Batch translation
* [x] Translation validation and retry handling
* [x] Smart transcript chunking
* [x] Timestamp-aware chunk metadata
* [x] Chunk overlap
* [x] Duplicate final-tail prevention
* [x] Embedding generation
* [x] Sentence Transformer integration
* [x] 384-dimensional vector generation
* [x] Qdrant collection setup
* [x] Vector ingestion
* [x] Chunk metadata storage in Qdrant
* [x] Semantic query embedding
* [x] Top-K semantic retrieval
* [x] Retrieval score output
* [x] Timestamp-aware search results
* [x] Original and English transcript retrieval

## In Progress / Next

* [ ] Reusable vector retrieval service
* [ ] Multi-video ingestion
* [ ] Query classification
* [ ] DSA pattern detection
* [ ] DSA sub-pattern detection
* [ ] Metadata filtering
* [ ] Hybrid retrieval
* [ ] Reranking
* [ ] Grounded RAG generation
* [ ] FastAPI retrieval endpoint
* [ ] Timestamp-aware UI
* [ ] Adaptive practice generation
* [ ] Weakness detection
* [ ] Targeted revision
* [ ] Retrieval evaluation
* [ ] Automated tests
* [ ] Deployment

---

# 15. Development Progress

The current system has successfully progressed from raw YouTube
lecture data to a working semantic retrieval system.

```text
YouTube Lecture
      ↓
Transcript Extraction          ✅
      ↓
Timestamp Preservation         ✅
      ↓
English Translation            ✅
      ↓
Smart Chunking                 ✅
      ↓
Embedding Generation           ✅
      ↓
Qdrant Vector Ingestion        ✅
      ↓
Semantic Retrieval             ✅
      ↓
Query Intelligence             ⏳
      ↓
Reranking                      ⏳
      ↓
Grounded RAG                   ⏳
      ↓
Timestamp-aware UI             ⏳
      ↓
Adaptive Practice              ⏳
```

The current backend can already retrieve relevant timestamped
lecture chunks from Qdrant using natural-language queries.

---

# 16. Project Vision

The long-term goal is to turn the system from a simple
question-answering tool into an adaptive DSA learning system.

Instead of:

```text
"Here is an answer."
```

the system should eventually provide:

```text
"Here is the exact part of the lecture where this was taught,
 here is a concise explanation grounded in that lecture,
 and here are problems that test whether you actually learned it."
```

The final system should connect:

```text
Lecture Knowledge
      +
Retrieval
      +
Timestamp Navigation
      +
Pattern Intelligence
      +
Practice
      +
Performance Analysis
      +
Adaptive Revision
```

into one learning workflow.
