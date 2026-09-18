
# 🧠 DSA Revision Analyzer

> An AI-powered, pattern-first DSA learning and revision system that combines structured video learning, hybrid RAG retrieval, grounded explanations, adaptive questioning, practice problems, mastery tracking, weakness detection, strict learning progression, and adaptive revision.

---

# 📌 Project Overview

**DSA Revision Analyzer** is an AI-powered learning system designed to make DSA revision more structured, searchable, adaptive, and measurable.

Instead of treating DSA as a collection of isolated problems, the system organizes learning around **DSA patterns and concepts**.

The system is designed around a continuous learning loop:

```text
Learn
  ↓
Understand
  ↓
Search
  ↓
Revise
  ↓
Question
  ↓
Validate
  ↓
Practice
  ↓
Measure Mastery
  ↓
Identify Weakness
  ↓
Revise Again
  ↓
Improve
````

The long-term goal is to create a system where a learner can search for any DSA concept and immediately reach:

```text
Exact Pattern
      ↓
Exact Video
      ↓
Exact Timestamp / Context
      ↓
Video Learning
      ↓
Bengali AI Revision
      ↓
Concept Validation
      ↓
Targeted Practice
      ↓
Mastery Tracking
      ↓
Weakness Detection
      ↓
Adaptive Revision
```

---

# 🎯 Core Goals

The system aims to provide:

* Pattern-based DSA learning
* Searchable DSA video knowledge
* Exact video-level retrieval
* Timestamp-aware retrieval
* Hybrid semantic + lexical search
* Reranking
* Grounded RAG answers
* AI-generated revision questions
* Bengali-language post-video questioning
* One-by-one conceptual AI conversations
* Answer validation
* Concept-level weakness detection
* Mastery estimation
* Concept-based practice problems
* LeetCode resources
* GeeksforGeeks resources
* Difficulty-aware practice
* Strict video progression
* Problem completion tracking
* Learning streak tracking
* Adaptive revision
* Responsive web UI
* Dark / Light theme
* Mobile optimization

---

# 🧩 Learning Architecture

The intended learning experience is:

```text
DSA Pattern
    │
    ├── Video 1
    ├── Video 2
    ├── Video 3
    ├── ...
    └── Video N
          │
          ▼
       Watch Lesson
          │
          ▼
     Video Completion
          │
          ▼
    AI Revision Session
          │
          ├── 6–7 Deep Questions
          │
          ├── One-by-One Answers
          │
          ├── AI Answer Validation
          │
          ├── Weak Concept Detection
          │
          └── Mastery Estimation
                    │
                    ▼
            Targeted Practice
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
        Easy     Medium      Hard
          │         │         │
          └─────────┼─────────┘
                    │
                    ▼
          LeetCode / GFG / Other
                    │
                    ▼
          Solve All Required Problems
                    │
                    ▼
            Problem Completion
                    │
                    ▼
            Streak Qualification
                    │
                    ▼
            Next Video Unlock
                    │
                    ▼
          Adaptive Revision
```

---

# 🔒 Strict Learning Progression

Watching a video alone does **not** mark the lesson as fully completed.

The system follows a strict progression model:

```text
Watch Video
     ↓
Video Watched
     ↓
Complete AI Revision
     ↓
Answer 6–7 Deep Questions
     ↓
AI Evaluates Answers
     ↓
Weakness / Mastery Updated
     ↓
Receive Targeted Problems
     ↓
Solve ALL Required Problems
     ↓
Video Fully Completed
     ↓
Next Video Unlocked
```

A learner cannot simply watch a video and skip directly to the next lesson.

---

## Video Completion Rule

A video is considered fully completed only when:

```text
VIDEO_COMPLETED =
    VIDEO_WATCHED
    AND
    REVISION_COMPLETED
    AND
    ALL_REQUIRED_PROBLEMS_COMPLETED
```

Therefore:

```text
Video Watched        ✅
AI Revision          ❌
Problems             ❌
────────────────────────
Video Complete       ❌
Next Video           🔒
```

And:

```text
Video Watched        ✅
AI Revision          ✅
Problems             5 / 5
────────────────────────
Video Complete       ✅
Next Video           🔓
```

---

# 🔥 Learning Streak Rule

The learning streak is tied to **actual learning completion**, not simply opening or watching a video.

A streak-qualified lesson requires:

```text
Video Watched
      +
AI Revision Completed
      +
All Required Problems Solved
      ↓
Streak Qualified
```

Example:

```text
Video                 ✅
AI Revision           ✅
Problems              4 / 5 ❌

Streak:
NOT QUALIFIED
```

Only when all required problems are completed:

```text
Video                 ✅
AI Revision           ✅
Problems              5 / 5 ✅

🔥 STREAK QUALIFIED
```

---

# 📚 DSA Pattern Structure

The application is designed around approximately **20–25 major DSA patterns**.

The current learning dataset contains **128+ videos** and is expected to grow as more videos are added.

> **Important:** The current target is **128+ videos**, not 180+.

Each pattern is intended to have:

* Pattern overview
* Pattern-specific playlist
* Ordered videos
* Video metadata
* Transcript
* Chunked transcript
* Embeddings
* Searchable knowledge
* Revision questions
* Practice problems
* External learning resources
* Progress state
* Mastery state
* Weakness information

---

# 🏗️ System Architecture

```text
                     ┌──────────────────────┐
                     │      React UI        │
                     │                      │
                     │ Overview             │
                     │ Patterns             │
                     │ Playlist             │
                     │ AI Search            │
                     │ Revision             │
                     │ Practice             │
                     │ Progress             │
                     │ Mastery              │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │     FastAPI API      │
                     │                      │
                     │ Search               │
                     │ Retrieval            │
                     │ RAG                  │
                     │ Metadata             │
                     │ Revision             │
                     │ Evaluation           │
                     │ Practice             │
                     │ Progress             │
                     │ Mastery              │
                     └──────────┬───────────┘
                                │
                   ┌────────────┼────────────┐
                   │            │            │
                   ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │ Qdrant   │ │ SQLite   │ │   RAG    │
             │ Vector   │ │ Metadata │ │ Pipeline │
             │ Search   │ │          │ │          │
             └──────────┘ └──────────┘ └──────────┘
                   │
                   ▼
             Transcript Chunks
                   │
                   ▼
               Embeddings
```

---

# 🛠️ Technology Stack

## Frontend

* React
* JavaScript
* React Router
* CSS
* Responsive UI
* Dark / Light theme

## Backend

* Python
* FastAPI

## AI / RAG

* Transcript processing
* Chunking
* Embeddings
* Vector search
* Hybrid retrieval
* Reranking
* Context assembly
* Grounded generation
* AI revision
* Answer evaluation
* Weakness detection
* Mastery estimation
* Practice generation

## Vector Database

* Qdrant

## Metadata / Persistence

* SQLite
* JSON-based intermediate data

## Data Sources

* YouTube transcripts
* LeetCode
* GeeksforGeeks
* Other concept-specific learning resources

---

# 📁 Current Project Structure

```text
dsa_revision_analyzer/
│
├── backend/
│   │
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── data/
│   │   ├── transcripts/
│   │   ├── translated/
│   │   ├── chunks/
│   │   └── embeddings/
│   │
│   ├── scripts/
│   │   ├── youtube_transcribe.py
│   │   ├── translate_transcript.py
│   │   ├── chunk_transcript.py
│   │   └── ingest_embeddings.py
│   │
│   └── tests/
│
├── frontend/
│   │
│   ├── src/
│   │   ├── api/
│   │   │
│   │   ├── components/
│   │   │   ├── ai/
│   │   │   ├── layout/
│   │   │   ├── patterns/
│   │   │   ├── playlist/
│   │   │   ├── revision/
│   │   │   ├── search/
│   │   │   └── video/
│   │   │
│   │   ├── data/
│   │   ├── hooks/
│   │   ├── lib/
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Patterns.jsx
│   │   │   ├── Pattern.jsx
│   │   │   ├── Search.jsx
│   │   │   └── Revision.jsx
│   │   │
│   │   ├── styles/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   └── package.json
│
└── README.md
```

---

# 🚦 Development Phases

The project is divided into **28 major phases**.

The first 14 phases establish the RAG and retrieval foundation.

Phases 15–17 connect and refine the backend, frontend, AI Search, pattern playlists, and exact lesson navigation.

Phases 18–26 build the complete adaptive learning engine.

Phases 27–28 focus on testing, production readiness, and deployment.

---

# ✅ Phase 1 — Project Foundation

**Status: COMPLETE**

Implemented:

* Backend project structure
* Frontend foundation
* Environment configuration
* Initial data directories
* Development workflow

---

# ✅ Phase 2 — YouTube Transcript Acquisition

**Status: COMPLETE**

Implemented:

* YouTube video transcript extraction
* Transcript JSON storage
* Video ID based processing
* Transcript validation

---

# ✅ Phase 3 — Transcript Translation

**Status: COMPLETE**

Implemented:

* Transcript translation pipeline
* Structured translated transcript storage
* Preservation of transcript metadata

---

# ✅ Phase 4 — Transcript Chunking

**Status: COMPLETE**

Implemented:

* Transcript chunking
* Chunk metadata
* Timestamp preservation
* Search-friendly chunk structure

---

# ✅ Phase 5 — Embedding Generation

**Status: COMPLETE**

Implemented:

* Embedding generation pipeline
* Chunk-level embeddings
* Embedding storage

---

# ✅ Phase 6 — Qdrant Integration

**Status: COMPLETE**

Implemented:

* Qdrant connection
* Vector collection
* Embedding ingestion
* Vector retrieval

---

# ✅ Phase 7 — Basic Semantic Retrieval

**Status: COMPLETE**

Implemented:

* Semantic query embedding
* Vector similarity search
* Relevant transcript chunk retrieval

---

# ✅ Phase 8 — Metadata & Data Modeling

**Status: COMPLETE**

Implemented:

* Video metadata
* Pattern metadata
* Chunk metadata
* Structured dataset organization

---

# ✅ Phase 9 — Retrieval Infrastructure

**Status: COMPLETE**

Implemented:

* Retrieval service architecture
* Search abstractions
* Metadata-aware retrieval foundation

---

# ✅ Phase 10 — Retrieval Evaluation & Refinement

**Status: COMPLETE**

Implemented:

* Retrieval debugging
* Result inspection
* Retrieval quality refinement
* Dataset validation

---

# ✅ Phase 11 — Hybrid Search + Reranking

**Status: COMPLETE**

Implemented:

* Semantic retrieval
* Lexical retrieval
* Hybrid scoring
* Result fusion
* Reranking

Architecture:

```text
Query
 │
 ├── Semantic Search
 │
 └── Lexical Search
        │
        ▼
    Candidate Pool
        │
        ▼
      Reranker
        │
        ▼
  Final Ranked Results
```

---

# ✅ Phase 12 — Context Assembly

**Status: COMPLETE**

Implemented:

* Retrieval result grouping
* Context selection
* Relevant chunk assembly
* Metadata-aware context construction
* Timestamp preservation
* Video title preservation
* English transcript (`text_en`) preference for summary generation
* Grounded context formatting

---

# ✅ Phase 13 — Grounded RAG Generation

**Status: COMPLETE**

Implemented:

* Retrieval → context → generation pipeline
* Grounded responses
* Source-aware answers
* Context-based answer generation
* Structured LLM response
* Per-video English summaries
* Video provenance validation
* Hallucination reduction through retrieval grounding

---

# ✅ Phase 14 — Timestamp-Aware Retrieval

**Status: COMPLETE**

Implemented:

* Timestamp-aware chunks
* Video timestamp metadata
* Retrieval results containing video position
* Foundation for exact video navigation
* YouTube jump-link generation
* Exact timestamp preservation

---

# 🟡 Phase 15 — FastAPI Backend

**Status: IN PROGRESS**

The FastAPI backend provides the bridge between the RAG pipeline and the React frontend.

## Completed

* FastAPI application foundation
* Retrieval API
* RAG API
* Metadata endpoints
* API-level testing foundation
* RAG response contract for video titles
* RAG response contract for per-video summaries
* Search API integration with the frontend

## Remaining

* Revision API
* Practice problem API
* Resource API
* Progress API
* Evaluation API
* Frontend-ready contracts for upcoming adaptive learning features
* Complete end-to-end API validation

---

# 🟡 Phase 16 — React Frontend

**Status: IN PROGRESS**

> **Latest milestone:** AI Search integration and exact lesson navigation are working end-to-end.

The goal of Phase 16 is to build the complete user-facing learning experience and connect it to the backend learning engine.

---

## Completed

### Application Shell

* React application structure
* Global application layout
* Global navigation
* Page routing foundation

### Navigation

Implemented routes:

```text
/
├── Overview
│
├── /patterns
│   └── Pattern listing
│
├── /pattern/:patternId
│   └── Individual pattern
│
├── /search
│   └── AI Search
│
└── /revision/:videoId
    └── AI Revision
```

### Navbar

Implemented:

* DSA Revision Analyzer branding
* Overview navigation
* AI Search navigation
* Patterns navigation
* Active route highlighting
* Theme toggle

### Theme System

Implemented foundation for:

* Dark mode
* Light mode
* CSS variables
* Theme persistence
* Global theme switching

### Visual Design

Implemented foundation for:

* Dark futuristic UI
* Grid background
* Gradient glow
* Glass-like surfaces
* Cards
* Accent-based UI
* Responsive layout foundation

### Pattern UI

Implemented foundation for:

* Pattern listing
* Pattern cards
* Pattern navigation
* Playlist structure
* Ordered pattern lesson display
* Playlist progress visibility

---

# 🔎 AI Search Integration

**Status: IMPLEMENTED — FINAL MULTI-LESSON VALIDATION IN PROGRESS**

The AI Search experience is integrated with the production RAG pipeline.

Implemented:

* Search query submission from React
* FastAPI RAG API integration
* Grounded AI answer rendering
* Video-level result grouping
* Duplicate transcript-chunk suppression
* Video title propagation from Qdrant metadata
* English AI-generated summary for retrieved videos
* Episode-aware result ordering
* Timestamp-aware result display
* Exact lesson navigation
* Exact video selection using retrieved `video_id`
* Exact timestamp navigation using `timestamp_start`
* Raw YouTube video IDs hidden from user-facing result cards
* Pattern-aware retrieval
* Video-level deduplication
* Pattern playlist ordering
* Complete pattern lesson discovery for pattern searches
* Per-video best matching transcript context for lessons not present in the initial candidate pool

Current search flow:

```text
User Query
    ↓
Query Understanding
    ↓
Pattern Detection
    ↓
Pattern Playlist Discovery
    ↓
Hybrid Retrieval
    ↓
Reranking
    ↓
Video-Level Deduplication
    ↓
Pattern Playlist Ordering
    ↓
Context Assembly
    ↓
Grounded LLM Generation
    ↓
Video-wise Result Grouping
    ↓
English Video Summaries
    ↓
Exact Lesson Navigation
    ↓
Correct Video + Timestamp
```

---

## Pattern Search Behavior

For a query such as:

```text
two-pointer
```

the system should identify the **Two Pointer** pattern and retrieve the complete set of lessons belonging to that pattern.

Example playlist:

```text
Two Pointer
│
├── Episode 3
├── Episode 4
├── Episode 5
├── Triplet Sum — Core Two Pointer
├── Dutch National Flag — Core Two Pointer
└── Core Two Pointer — Lesson 06
```

The AI Search system is designed so that highly ranked early results do not prevent remaining lessons from appearing.

Instead:

```text
Pattern
   ↓
Complete Pattern Playlist
   ↓
Best Transcript Match Per Video
   ↓
Video-Level Results
   ↓
Playlist Order
```

This prevents a search from returning only the first few highly similar videos while hiding other lessons belonging to the same pattern.

---

## Result Structure

Each result can contain:

```text
Episode / Lesson
Video Title
Pattern
Exact Timestamp
English Summary
Open Exact Lesson →
```

The system should produce **one result card per lesson/video**, rather than exposing multiple raw transcript chunks from the same video.

---

## Example

```text
Search:
"two pointer"

Expected Pattern:
Two Pointer

Results:

01. Episode 3
    English Summary
    Exact timestamp
    Open Exact Lesson →

02. Episode 4
    English Summary
    Exact timestamp
    Open Exact Lesson →

03. Episode 5
    English Summary
    Exact timestamp
    Open Exact Lesson →

04. Triplet Sum — Core Two Pointer
    English Summary
    Exact timestamp
    Open Exact Lesson →

05. Dutch National Flag — Core Two Pointer
    English Summary
    Exact timestamp
    Open Exact Lesson →

06. Core Two Pointer — Lesson 06
    English Summary
    Exact timestamp
    Open Exact Lesson →
```

The summaries for the remaining lessons must be grounded in the transcript of the corresponding video.

For example:

```text
Triplet Sum
     ↓
Triplet Sum transcript
     ↓
Best matching chunk
     ↓
Timestamp + transcript context
     ↓
English summary
```

The system should **not reuse Episode 3's transcript or summary** for the other lessons.

---

## Exact Lesson Navigation

The exact lesson action uses:

```text
video_id
    +
timestamp_start
```

to navigate the learner directly to the relevant point in the correct YouTube video.

Raw `video_id` values remain internal.

The learner sees:

```text
Open Exact Lesson →
```

rather than the raw YouTube identifier.

---

## Validation Completed

The following behavior has already been browser-tested:

* `two pointer` search returns a grounded AI answer
* Retrieved videos are grouped into one card per video
* Episode ordering is preserved
* English summaries are displayed
* Raw `video_id` values are not exposed
* Exact lesson navigation works
* Exact timestamp navigation works
* Episode 3 exact navigation verified
* Episode 4 exact navigation verified
* Episode 5 exact navigation verified

The complete six-lesson pattern retrieval implementation has been added and requires final browser validation.

---

# 🟡 Phase 17 — Pattern / Playlist Navigation

**Status: IN PROGRESS**

Phase 17 focuses on connecting pattern playlists with AI Search so that the system understands the complete lesson structure of each DSA pattern.

---

## Completed

* Pattern-specific playlist retrieval
* Ordered playlist metadata
* Pattern video catalog discovery
* Video-level deduplication
* Original episode metadata preservation
* Pattern-specific video ordering
* Playlist progress visibility
* Complete Two Pointer playlist visible in the Pattern page
* Six Two Pointer lessons present in the playlist
* AI Search pattern detection
* Pattern-aware retrieval
* Missing lesson discovery during pattern search
* Per-video transcript matching
* Exact timestamp preservation
* Exact lesson navigation integration

---

## Current Two Pointer Playlist

The current Two Pointer pattern contains:

```text
01. Episode 3
02. Episode 4
03. Episode 5
04. Triplet Sum — Core Two Pointer
05. Dutch National Flag — Core Two Pointer
06. Core Two Pointer — Lesson 06
```

The Pattern page currently exposes all six lessons.

The AI Search implementation is being aligned with this same playlist so that a pattern search does not stop after only the first highly ranked lessons.

---

## Remaining

* Final browser validation of all six lessons through AI Search
* Validation of correct summary generation for each remaining lesson
* Validation of timestamp correctness for each remaining lesson
* Validation that unrelated videos such as Dynamic Programming Episode 16 do not appear in Two Pointer results
* Validation across additional DSA patterns
* Complete pattern playlist/search consistency testing

---

# ⏳ Phase 18 — Video Progress & Completion

**Status: NOT STARTED**

Focus:

* Video playback tracking
* Current playback position
* Resume from previous position
* Progress percentage
* Watch completion detection
* Video state persistence
* Pattern-level progress

Example:

```text
Episode 3

Progress:
████████████████░░░░ 80%

Status:
In Progress
```

Completion state:

```text
Video Watched
      ↓
Trigger AI Revision
```

---

# ⏳ Phase 19 — Strict Video Unlock / Progression Gate

**Status: NOT STARTED**

Focus:

* Locked next videos
* Completion-based unlocking
* Backend validation
* Frontend lock states
* Preventing progression bypass
* Current-video completion validation

Rules:

```text
Current Video
     │
     ├── Watched?       ❌ → Locked
     │
     ├── Revision?      ❌ → Locked
     │
     └── Problems?      ❌ → Locked
```

Only:

```text
Watched
   +
Revision Completed
   +
All Problems Completed
   ↓
Next Video Unlocked
```

The gate must not rely only on frontend UI state.

---

# ⏳ Phase 20 — Bengali AI Revision Session

**Status: NOT STARTED**

When a learner completes a video:

```text
Video Completed
       ↓
AI Revision Session
       ↓
Bengali Conversation
```

The AI revision session should be grounded in:

* Current video
* Current pattern
* Transcript
* Concepts explained in the video
* Retrieved context when necessary

The objective is to create an interactive revision conversation rather than a static quiz.

---

# ⏳ Phase 21 — Deep Conceptual Question Engine

**Status: NOT STARTED**

The AI should ask approximately:

```text
6–7 questions
```

Questions should be presented **one at a time**.

The learner must answer before receiving the next question.

Question categories may include:

* Core concept
* Intuition
* Why the approach works
* Pattern recognition
* Pointer / state movement
* Edge cases
* Complexity
* Implementation reasoning
* Invariants
* What-if scenarios
* Interview-style reasoning

Example:

```text
কেন এই সমস্যাটিতে দুইটা pointer ব্যবহার করলে
O(n²) থেকে O(n) এ যাওয়া সম্ভব হচ্ছে?

যদি array sorted না হয় তাহলে কী ভেঙে যাবে?

এই approach-এর কোন invariant আমরা maintain করছি?
```

The objective is **conceptual depth, not memorization**.

---

# ⏳ Phase 22 — AI Answer Evaluation

**Status: NOT STARTED**

Each learner answer should be evaluated before moving to the next question.

Evaluation dimensions:

* Correctness
* Partial correctness
* Conceptual understanding
* Reasoning quality
* Explanation quality
* Complexity awareness
* Missing concepts
* Misconceptions

Example:

```text
Answer Evaluation

Understanding:
Strong

Missing:
Pointer movement justification

Needs Revision:
Sorted-array invariant
```

The AI should explain why an answer is correct, partially correct, or incorrect.

---

# ⏳ Phase 23 — Weakness Detection & Mastery

**Status: NOT STARTED**

The system should maintain concept-level learner performance.

Mastery can track:

```text
Pattern
 ├── Concept Understanding
 ├── Implementation
 ├── Complexity
 ├── Edge Cases
 ├── Pattern Recognition
 └── Problem Solving
```

Example:

```text
Two Pointer

Core Idea              92%
Pointer Movement       84%
Edge Cases             61%
Complexity Analysis    48%

Overall Mastery        71%
```

The system should identify:

* Strong concepts
* Weak concepts
* Partially understood concepts
* Topics requiring revision

Performance should persist as learning history.

---

# ⏳ Phase 24 — AI Targeted Practice Problems

**Status: NOT STARTED**

After concept validation, AI should generate approximately:

```text
4–5 targeted problems
```

Problems should be selected based on:

```text
Current Pattern
      +
Current Video
      +
Current Concepts
      +
Detected Weakness
      +
Revision Performance
```

Difficulty distribution should normally include:

```text
Easy
Medium
Hard
```

when meaningful for the lesson.

Sources may include:

* LeetCode
* GeeksforGeeks
* Other relevant platforms
* AI-generated concept problems

Problems should be:

* Pattern-specific
* Concept-specific
* Quality-focused
* Without unnecessary hints
* Relevant to detected weaknesses
* Different from simply copying a generic problem list

---

# ⏳ Phase 25 — Problem Completion & Streak Engine

**Status: NOT STARTED**

This phase connects practice completion with progression.

Required flow:

```text
Recommended Problems
        ↓
Solve Problem 1
        ↓
Solve Problem 2
        ↓
...
        ↓
Solve Final Problem
        ↓
All Required Problems Completed
        ↓
Video Fully Completed
        ↓
Streak Qualified
        ↓
Next Video Unlocked
```

A partially completed problem set does not qualify the lesson for completion.

Example:

```text
Problems:
4 / 5

Video:
NOT COMPLETE

Streak:
NOT QUALIFIED

Next Video:
LOCKED
```

After:

```text
Problems:
5 / 5

Video:
COMPLETE

Streak:
QUALIFIED

Next Video:
UNLOCKED
```

---

# ⏳ Phase 26 — Adaptive Revision Engine

**Status: NOT STARTED**

The system should decide what the learner should revise next.

Example:

```text
Weak Area Detected
       ↓
Relevant Pattern
       ↓
Relevant Video
       ↓
Relevant Timestamp
       ↓
Targeted Question
       ↓
New Evaluation
       ↓
Updated Mastery
```

The revision engine should use previous learner performance to personalize future revision.

The goal is to avoid repeatedly revising concepts the learner already understands while prioritizing weak areas.

---

# ⏳ Phase 27 — Automated Testing + Production Hardening

**Status: NOT STARTED**

This phase combines complete system testing with production-readiness work.

## Backend Testing

* Unit tests
* API tests
* Retrieval tests
* RAG tests
* Metadata tests
* Revision tests
* Evaluation tests
* Practice generation tests
* Progress tests
* Unlock-gate tests

## Frontend Testing

* Component tests
* Routing tests
* Search tests
* Theme tests
* Playlist tests
* Revision flow tests
* Progress tests
* Locked-state tests
* Practice completion tests

## Integration Testing

```text
Search
  ↓
Retrieval
  ↓
RAG
  ↓
Frontend
```

```text
Video Completion
  ↓
AI Revision
  ↓
Evaluation
  ↓
Practice Generation
  ↓
Problem Completion
  ↓
Video Unlock
```

## Production Hardening

* Error handling
* Logging
* Validation
* Security
* Rate limiting
* API reliability
* Performance
* Caching
* Environment configuration
* Production build optimization

---

# ⏳ Phase 28 — Deployment & Final Product Polish

**Status: NOT STARTED**

Final deployment target:

```text
Frontend
   ↓
Production Hosting

Backend
   ↓
Production API

Qdrant
   ↓
Production Vector Store

Database
   ↓
Production Metadata Store
```

Final polish:

* Responsive testing
* Loading states
* Empty states
* Error states
* Accessibility
* Navigation validation
* API integration validation
* UI consistency
* Mobile optimization
* Performance refinement
* Production build validation

Final objective:

```text
Publicly Accessible
       ↓
AI-Powered
       ↓
Pattern-First
       ↓
Adaptive
       ↓
DSA Learning & Revision Platform
```

---

# 🔎 AI Search Experience

The search system works beyond simple keyword matching and is integrated with the RAG backend.

Example query:

```text
"when should I shrink the window?"
```

Current pipeline:

```text
User Query
    ↓
Query Understanding
    ↓
Pattern Detection
    ↓
Pattern Playlist Discovery
    ↓
Hybrid Retrieval
    ↓
Reranking
    ↓
Video-Level Deduplication
    ↓
Context Assembly
    ↓
Grounded LLM Answer
    ↓
Video-wise Grouping
    ↓
Episode / Playlist Ordering
    ↓
English Video Summaries
    ↓
Exact Video
    ↓
Exact Timestamp
```

The UI presents one result card per retrieved video instead of exposing multiple raw transcript chunks from the same video.

Each result can contain:

```text
Episode
Video Title
Pattern
Exact Timestamp
English Summary
Open Exact Lesson →
```

Raw YouTube `video_id` values are kept internally for navigation and are not displayed to the learner.

---

# 🧠 Pattern-Aware Search

Pattern search is designed to behave differently from a generic semantic search.

For generic queries:

```text
User Query
    ↓
Relevant Transcript Chunks
    ↓
Reranking
    ↓
Relevant Videos
```

For pattern-oriented queries:

```text
User Query
    ↓
Pattern Detection
    ↓
Complete Pattern Playlist
    ↓
Best Match Per Lesson
    ↓
Sequential Video Results
```

This distinction is important because the learner may search for a pattern expecting the complete learning sequence rather than only the most semantically similar transcript chunks.

---

# 🤖 AI Revision Experience

When a learner completes a video:

```text
┌──────────────────────────────┐
│       Video Completed        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│     AI Revision Opens        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Bengali Concept Questions    │
│        6–7 Questions         │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       User Answers           │
│      One Question at a Time  │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       AI Validation          │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│    Weakness + Mastery        │
└──────────────┬───────────────┘
               ↓
        ┌──────┴───────┐
        ↓              ↓
External Resources   New Problems
        ↓              ↓
LeetCode / GFG      4–5 Problems
        │              │
        └──────┬───────┘
               ↓
       Solve All Problems
               ↓
       Streak Qualified
               ↓
       Next Video Unlock
```

---

# 🧠 Question Generation Philosophy

The system should not behave like a simple problem recommender.

It should test whether the learner actually understands the concept.

Questions should be generated from the **specific lesson context**.

For example, after a Two Pointer video, AI may ask:

```text
কেন এই সমস্যাটিতে দুইটা pointer ব্যবহার করলে
O(n²) থেকে O(n) এ যাওয়া সম্ভব হচ্ছে?

যদি array sorted না হয় তাহলে কী ভেঙে যাবে?

এই approach-এর কোন invariant আমরা maintain করছি?
```

The question engine should explore:

* Conceptual understanding
* Intuition
* Edge cases
* Complexity
* Pattern recognition
* Implementation reasoning
* Invariants
* Failure conditions
* Alternative approaches

The goal is **actual understanding**, not memorization.

---

# 📊 Mastery Model

The long-term mastery model can track:

```text
Pattern
 ├── Concept Understanding
 ├── Implementation
 ├── Complexity
 ├── Edge Cases
 ├── Pattern Recognition
 └── Problem Solving
```

Each dimension contributes to an overall mastery score.

Example:

```text
Pattern: Sliding Window

Concept          88%
Implementation   74%
Complexity       62%
Edge Cases       55%
Recognition      81%

Overall          72%
```

Mastery should change based on:

```text
AI Revision Answers
        +
Answer Evaluation
        +
Practice Performance
        +
Historical Performance
```

---

# 🔗 External Learning Resources

The system should connect learners with relevant external problems and explanations.

Primary sources:

* LeetCode
* GeeksforGeeks

The resources should be selected based on:

```text
Current Pattern
+
Current Video
+
Current Concept
+
Detected Weakness
+
Learner Performance
```

The system may also include relevant resources from other platforms when appropriate.

---

# 💻 Practice Problem Philosophy

The practice system should not simply display a generic list of DSA problems.

Problems should be connected to the lesson:

```text
Video
  ↓
Concepts
  ↓
Revision Performance
  ↓
Weaknesses
  ↓
Targeted Problems
```

The learner should normally receive approximately:

```text
4–5 Problems
```

with meaningful difficulty coverage:

```text
Easy
Medium
Hard
```

The exact number may vary when the lesson scope makes fewer or more problems more appropriate.

Problems should avoid unnecessary hints so that the learner is required to identify the correct pattern and approach independently.

---

# 🎨 UI / UX Direction

The intended visual identity is:

```text
Dark + Light
Modern
Minimal
Futuristic
Technical
Premium
```

Key visual elements:

* Deep dark background
* Subtle grid
* Purple/indigo accent
* Soft ambient glow
* Glass-like cards
* Clean typography
* Strong spacing
* Smooth transitions
* Responsive layout

The goal is to make the project immediately feel like a polished **AI developer tool**, rather than a generic educational dashboard.

---

# 📱 Responsive Design

The application must be optimized for:

```text
Desktop
   ↓
Laptop
   ↓
Tablet
   ↓
Mobile
```

Mobile-specific priorities:

* Collapsible navigation
* Vertical playlist
* Responsive video player
* Full-width AI chat
* Touch-friendly controls
* Responsive cards
* Readable typography
* Revision conversation usability
* Practice problem usability
* Locked-state visibility

---

# 🧪 Development Principles

The project follows these principles:

### 1. Retrieval First

AI answers should be grounded in retrieved knowledge.

### 2. Evidence Based

Responses should be connected to actual transcript/video context whenever possible.

### 3. Pattern First

Problems should be understood through reusable DSA patterns.

### 4. Concept First

The system should test understanding, not memorization.

### 5. Adaptive

The learning flow should respond to learner performance.

### 6. Explainable

The learner should understand why something is correct or incorrect.

### 7. Progression Driven

A learner should complete the required learning cycle before progressing to the next lesson.

### 8. Measurable

The system should track mastery, weaknesses, practice performance, and learning history.

### 9. Production Oriented

The project is being built as a real software system rather than only as an AI demo.

---

# 📝 Latest Development Milestone — 18 September 2026

The latest milestone focuses on making **AI Search pattern-aware and lesson-oriented**, while preserving the previously completed exact lesson navigation behavior.

## Completed / Implemented

* Video titles are propagated through the RAG context and API response
* English transcript text is preferred for video-summary generation
* Groq returns a structured grounded response
* Main AI answer is separated from per-video summaries
* Video summaries are grounded against retrieved video provenance
* Search results are grouped by unique video
* Episode / playlist ordering is preserved
* Raw YouTube video IDs are hidden from the UI
* Exact timestamps remain attached to retrieved source chunks
* `Open Exact Lesson →` navigates to the correct video
* Exact timestamp navigation has been browser-tested
* Episode 3 exact navigation verified
* Episode 4 exact navigation verified
* Episode 5 exact navigation verified
* Pattern-aware search has been implemented
* Complete pattern playlist discovery has been added for pattern-oriented search
* Missing pattern lessons can be retrieved through per-video transcript matching
* Video-level deduplication is applied
* Playlist ordering is preserved after retrieval
* Two Pointer pattern currently contains 6 playlist lessons

## Current Two Pointer Dataset

```text
Two Pointer
│
├── Episode 3
├── Episode 4
├── Episode 5
├── Triplet Sum — Core Two Pointer
├── Dutch National Flag — Core Two Pointer
└── Core Two Pointer — Lesson 06
```

The Pattern page currently displays all six lessons.

The AI Search retrieval implementation has been updated so that remaining playlist lessons are not lost simply because Episode 3, Episode 4, and Episode 5 receive higher initial retrieval scores.

## Final Validation Still Required

The following validation remains before the complete Phase 17 milestone can be marked fully complete:

```text
Search:
"two-pointer"

Expected:
6 / 6 playlist lessons

Each lesson:
    ├── Correct video
    ├── Correct transcript
    ├── Correct timestamp
    ├── Correct English summary
    └── Open Exact Lesson →
```

The search must also exclude unrelated lessons such as:

```text
Dynamic Programming — Episode 16
```

from a Two Pointer pattern search.

---

# 📈 Current Project Status

```text
Phases 01–14       ████████████████████  COMPLETE

Phase 15           ███████████████░░░░░  IN PROGRESS

Phase 16           █████████████████░░░  IN PROGRESS

Phase 17           ███████████████░░░░░  IN PROGRESS

Phases 18–28       ░░░░░░░░░░░░░░░░░░░░  PLANNED
```

---

# 🎯 Current Active Focus

> **Phase 17 — Pattern / Playlist Navigation + Complete Pattern-Aware AI Search**

Current working functionality:

```text
Pattern Page
    ↓
Pattern Playlist
    ↓
Complete Pattern Lesson List
    ↓
Video Player
    ↓
Playlist Selection
    ↓
AI Search
    ↓
Pattern Detection
    ↓
Complete Pattern Playlist Discovery
    ↓
Best Transcript Match Per Lesson
    ↓
Grounded Answer
    ↓
Video-wise Results
    ↓
English Summary
    ↓
Exact Timestamp
    ↓
Open Exact Lesson
```

---

# 🗺️ Final 28-Phase Roadmap

```text
Phase 01
Project Foundation
        ↓
Phase 02
YouTube Transcript Acquisition
        ↓
Phase 03
Transcript Translation
        ↓
Phase 04
Transcript Chunking
        ↓
Phase 05
Embedding Generation
        ↓
Phase 06
Qdrant Integration
        ↓
Phase 07
Basic Semantic Retrieval
        ↓
Phase 08
Metadata & Data Modeling
        ↓
Phase 09
Retrieval Infrastructure
        ↓
Phase 10
Retrieval Evaluation & Refinement
        ↓
Phase 11
Hybrid Search + Reranking
        ↓
Phase 12
Context Assembly
        ↓
Phase 13
Grounded RAG Generation
        ↓
Phase 14
Timestamp-Aware Retrieval
        ↓
Phase 15
FastAPI Backend
        ↓
Phase 16
React Frontend
        ↓
Phase 17
Pattern / Playlist Navigation
        ↓
Phase 18
Video Progress & Completion
        ↓
Phase 19
Strict Video Unlock / Progression Gate
        ↓
Phase 20
Bengali AI Revision Session
        ↓
Phase 21
Deep Conceptual Question Engine
        ↓
Phase 22
AI Answer Evaluation
        ↓
Phase 23
Weakness Detection & Mastery
        ↓
Phase 24
AI Targeted Practice Problems
        ↓
Phase 25
Problem Completion & Streak Engine
        ↓
Phase 26
Adaptive Revision Engine
        ↓
Phase 27
Automated Testing + Production Hardening
        ↓
Phase 28
Deployment & Final Product Polish
```

---

# 🏁 Final Vision

The final system should allow a learner to do this:

```text
"I don't understand Sliding Window."

                ↓

Search:
"when should I shrink the window?"

                ↓

AI finds:

Sliding Window
      ↓
Exact Video
      ↓
Exact Timestamp

                ↓

Learner watches

                ↓

Video completes

                ↓

AI automatically opens

                ↓

Bengali conceptual questions

                ↓

6–7 deep questions
one at a time

                ↓

Learner answers

                ↓

AI evaluates

                ↓

Weak concepts detected

                ↓

Mastery updated

                ↓

AI provides:

Relevant LeetCode
Relevant GFG
+
4–5 targeted problems

                ↓

Learner solves all required problems

                ↓

Streak qualified

                ↓

Next video unlocked

                ↓

Future performance tracked

                ↓

AI identifies weak areas

                ↓

Relevant video / timestamp

                ↓

Targeted revision

                ↓

Mastery updated again
```

---

# 🚀 End Goal

The end goal is not simply:

> **"An AI chatbot for DSA."**

The goal is:

> **An adaptive DSA learning and revision system that understands patterns, retrieves the exact learning context, tests conceptual understanding, measures mastery, identifies weaknesses, enforces meaningful learning progression, recommends targeted practice, and continuously adapts the learner's revision path.**

---

# 📌 Current Milestone

**Current Phase:** Phase 17 — Pattern / Playlist Navigation + Pattern-Aware AI Search

**Latest Completed Milestone:** AI Search + Video-wise Summaries + Exact Lesson Navigation

**Latest Implementation:** Complete pattern playlist discovery and per-video retrieval for pattern-oriented search

**Dataset Target:** 128+ DSA Videos

**Patterns:** ~20–25

**Major Development Phases:** 28

**Architecture:** React + FastAPI + Qdrant + RAG

**Search:** End-to-End Integrated

**Pattern Search:** Implemented, final 6-lesson validation pending

**Exact Navigation:** Browser Verified

**AI Revision:** Planned

**Strict Progression:** Planned

**Mastery Engine:** Planned

**Adaptive Revision:** Planned

**Overall Status:** Active Development
