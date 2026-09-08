
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

The ingestion pipeline currently processes YouTube lecture
transcripts in multiple stages.

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
Embeddings
      ↓
Qdrant
      ↓
Retrieval
```

The first three processing stages are currently implemented:

```text
youtube_transcribe.py
      ↓
translate_transcript.py
      ↓
chunk_transcript.py
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
└── scripts/
    ├── youtube_transcribe.py
    ├── translate_transcript.py
    └── chunk_transcript.py
```

Generated data files are kept separate from the processing
scripts so that the ingestion pipeline remains organized.

---

# 8. Planned Retrieval Metadata

The final retrieval layer is expected to associate each chunk
with metadata such as:

* Video ID
* Video title
* Playlist
* DSA pattern
* DSA sub-pattern
* Chunk ID
* Segment range
* Start timestamp
* End timestamp
* Transcript text
* English transcript text

This metadata will allow retrieval to become more precise than
pure semantic similarity.

---

# 9. Planned RAG Pipeline

The planned RAG workflow is:

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

# 10. Planned Adaptive Practice System

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

# 11. Planned Technology Stack

### Backend

* Python
* FastAPI

### Retrieval

* Qdrant
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

# 12. Current Development Status

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

## In Progress / Next

* [ ] Embedding generation
* [ ] Qdrant collection setup
* [ ] Vector ingestion
* [ ] Retrieval pipeline
* [ ] Query classification
* [ ] Pattern / sub-pattern detection
* [ ] Metadata filtering
* [ ] Reranking
* [ ] Grounded RAG generation
* [ ] Timestamp-aware UI
* [ ] Adaptive practice generation
* [ ] Weakness detection
* [ ] Targeted revision
* [ ] Retrieval evaluation
* [ ] Automated tests
* [ ] Deployment

---

# 13. Project Vision

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
----
