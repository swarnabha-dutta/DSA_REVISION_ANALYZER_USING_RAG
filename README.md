# 🧠 DSA Revision Analyzer

> An AI-powered, pattern-first DSA learning and revision system that combines structured video learning, hybrid RAG retrieval, grounded explanations, adaptive questioning, practice problems, and weakness detection.

---

## 📌 Project Overview

**DSA Revision Analyzer** is an AI-powered learning system designed to make DSA revision more structured, searchable, and adaptive.

Instead of treating DSA as a collection of isolated problems, the system organizes learning around **DSA patterns and concepts**.

The system is designed around a simple learning loop:

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
````

The long-term goal is to create a system where a learner can search for any DSA concept and immediately reach the **exact pattern → exact video → exact timestamp/context**, followed by an AI-powered revision session.

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
* Concept-based practice problems
* LeetCode and GeeksforGeeks resources
* Mastery estimation
* Weakness detection
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
      Video Ends
          │
          ▼
    AI Revision Session
          │
          ├── Concept Questions
          │
          ├── Answer Validation
          │
          ├── Mastery Score
          │
          ├── LeetCode Links
          │
          ├── GFG Links
          │
          └── Newly Generated
              Concept Problems
                    │
                    ▼
             Weakness Detection
                    │
                    ▼
             Adaptive Revision
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
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐     ┌──────────┐     ┌──────────┐
        │ Qdrant   │     │ SQLite   │     │   RAG    │
        │ Vector   │     │ Metadata │     │ Pipeline │
        │ Search   │     │          │     │          │
        └──────────┘     └──────────┘     └──────────┘
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

## Vector Database

* Qdrant

## Metadata / Persistence

* SQLite
* JSON-based intermediate data

## Data Sources

* YouTube transcripts
* LeetCode
* GeeksforGeeks

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
│   │   │
│   │   ├── hooks/
│   │   │
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
│   │   │
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

The project is divided into **24 major phases**.

---

## ✅ Phase 1 — Project Foundation

**Status: COMPLETE**

Implemented:

* Backend project structure
* Frontend foundation
* Environment configuration
* Initial data directories
* Development workflow

---

## ✅ Phase 2 — YouTube Transcript Acquisition

**Status: COMPLETE**

Implemented:

* YouTube video transcript extraction
* Transcript JSON storage
* Video ID based processing
* Transcript validation

---

## ✅ Phase 3 — Transcript Translation

**Status: COMPLETE**

Implemented:

* Transcript translation pipeline
* Structured translated transcript storage
* Preservation of transcript metadata

---

## ✅ Phase 4 — Transcript Chunking

**Status: COMPLETE**

Implemented:

* Transcript chunking
* Chunk metadata
* Timestamp preservation
* Search-friendly chunk structure

---

## ✅ Phase 5 — Embedding Generation

**Status: COMPLETE**

Implemented:

* Embedding generation pipeline
* Chunk-level embeddings
* Embedding storage

---

## ✅ Phase 6 — Qdrant Integration

**Status: COMPLETE**

Implemented:

* Qdrant connection
* Vector collection
* Embedding ingestion
* Vector retrieval

---

## ✅ Phase 7 — Basic Semantic Retrieval

**Status: COMPLETE**

Implemented:

* Semantic query embedding
* Vector similarity search
* Relevant transcript chunk retrieval

---

## ✅ Phase 8 — Metadata & Data Modeling

**Status: COMPLETE**

Implemented:

* Video metadata
* Pattern metadata
* Chunk metadata
* Structured dataset organization

---

## ✅ Phase 9 — Retrieval Infrastructure

**Status: COMPLETE**

Implemented:

* Retrieval service architecture
* Search abstractions
* Metadata-aware retrieval foundation

---

## ✅ Phase 10 — Retrieval Evaluation & Refinement

**Status: COMPLETE**

Implemented:

* Retrieval debugging
* Result inspection
* Retrieval quality refinement
* Dataset validation

---

## ✅ Phase 11 — Hybrid Search + Reranking

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

## ✅ Phase 12 — Context Assembly

**Status: COMPLETE**

Implemented:

* Retrieval result grouping
* Context selection
* Relevant chunk assembly
* Metadata-aware context construction
* Timestamp preservation

---

## ✅ Phase 13 — Grounded RAG Generation

**Status: COMPLETE**

Implemented:

* Retrieval → context → generation pipeline
* Grounded responses
* Source-aware answers
* Context-based answer generation
* Hallucination reduction through retrieval grounding

---

## ✅ Phase 14 — Timestamp-Aware Retrieval

**Status: COMPLETE**

Implemented:

* Timestamp-aware chunks
* Video timestamp metadata
* Retrieval results containing video position
* Foundation for exact video navigation

---

# 🟡 Phase 15 — FastAPI Backend

**Status: IN PROGRESS**

The FastAPI backend provides the bridge between the RAG pipeline and the React frontend.

### Completed

* FastAPI application foundation
* Retrieval API
* RAG API
* Metadata endpoints
* API-level testing foundation

### Remaining

* Query API finalization
* Revision API
* Practice problem API
* Resource API
* Frontend-ready response contracts
* End-to-end API validation

---

# 🟡 Phase 16 — React Frontend

**Status: IN PROGRESS**

This is the **current active phase**.

The goal of Phase 16 is to build the complete user-facing learning experience.

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

---

## Remaining Phase 16 Work

### 1. Complete Theme Polish

* Final dark mode polish
* Final light mode polish
* Component-level theme consistency
* Theme transition refinement

### 2. Pattern Playlist Integration

The UI must support the full **128+ video dataset**.

Expected behaviour:

```text
Pattern
   ↓
Playlist
   ↓
Video 1
Video 2
Video 3
...
Video N
```

### 3. Video Player Integration

Implement:

* Video playback
* Active video state
* Playlist selection
* Progress tracking
* Completion detection
* Timestamp-aware navigation

### 4. AI Search → Exact Video Navigation

The intended behaviour:

```text
User Search
     ↓
RAG Retrieval
     ↓
Pattern Detection
     ↓
Exact Video Detection
     ↓
Exact Timestamp
     ↓
Open Correct Pattern
     ↓
Select Correct Video
     ↓
Start From Relevant Context
```

This is one of the core differentiating features of the application.

### 5. Post-Video AI Revision

When a video finishes:

```text
Video Completed
       ↓
AI Revision Opens
       ↓
Concept Questions
       ↓
User Answers
       ↓
AI Validation
       ↓
Mastery Estimation
```

### 6. Bengali AI Questions

The post-video AI questions should be generated in **Bengali**.

Questions should be based specifically on:

* Current video
* Current pattern
* Transcript
* Concepts explained in the video

### 7. High-Quality Concept Questions

The system should not depend only on LeetCode/GFG questions.

AI should be able to generate original questions such as:

* Conceptual questions
* Edge-case questions
* Complexity questions
* Pattern recognition questions
* Implementation reasoning questions
* "Why does this work?" questions
* "What breaks if..." questions

The objective is to test **actual understanding**, not memorization.

### 8. External Practice Resources

After the revision session, the system should provide:

* LeetCode problems
* GeeksforGeeks problems
* Concept-specific resources

These should be aligned with the current:

```text
Pattern
+
Video
+
Concept
```

### 9. Practice Problem Generation

After concept validation, AI should generate approximately:

```text
4–5 problems
```

Problems should be:

* Pattern-specific
* Concept-specific
* Quality-focused
* Without unnecessary hints
* Different from simply copying existing LeetCode/GFG questions

### 10. Mastery Score

The system should estimate the learner's understanding.

Example:

```text
Two Pointer Mastery

████████████████░░░░ 78%
```

The score should help identify:

* Strong concepts
* Weak concepts
* Partially understood concepts
* Topics requiring revision

### 11. Mobile Optimization

The complete frontend must work across:

* Desktop
* Laptop
* Tablet
* Mobile

Important areas:

* Navbar
* Pattern cards
* Playlist
* Video player
* AI chat
* Revision questions
* Practice problems

### 12. Final Phase 16 Polish

Before moving to Phase 17:

* Responsive testing
* Loading states
* Empty states
* Error states
* Accessibility
* Navigation validation
* API integration validation
* UI consistency
* Performance refinement

---

# ⏳ Phase 17 — Pattern / Playlist Navigation

**Status: NOT STARTED**

Focus:

* Complete pattern browsing
* Playlist navigation
* Video ordering
* Progress tracking
* Pattern completion
* Video completion state

---

# ⏳ Phase 18 — Adaptive Practice

**Status: NOT STARTED**

Focus:

* Concept-based question generation
* 4–5 practice problems
* Difficulty adaptation
* Pattern-specific practice
* Avoiding duplicate problems

---

# ⏳ Phase 19 — Performance & Weakness Detection

**Status: NOT STARTED**

Focus:

* Answer evaluation
* Concept-level performance
* Weakness identification
* Mastery calculation
* Performance history

Example:

```text
Two Pointer

Core Idea              92%
Window Expansion       84%
Edge Cases             61%
Complexity Analysis    48%

Overall Mastery        71%
```

---

# ⏳ Phase 20 — Adaptive Revision Engine

**Status: NOT STARTED**

The system should decide what the learner should revise next.

Example:

```text
Weak Area Detected
       ↓
Relevant Video
       ↓
Relevant Timestamp
       ↓
Targeted Question
       ↓
New Evaluation
```

The system should become increasingly personalized based on previous performance.

---

# ⏳ Phase 21 — Evaluation System

**Status: NOT STARTED**

Focus:

* Answer correctness
* Partial correctness
* Explanation quality
* Conceptual understanding
* Reasoning quality
* Complexity awareness
* Confidence / mastery estimation

---

# ⏳ Phase 22 — Automated Testing

**Status: NOT STARTED**

Testing areas:

### Backend

* Unit tests
* API tests
* Retrieval tests
* RAG tests
* Metadata tests

### Frontend

* Component tests
* Routing tests
* Search tests
* Theme tests
* Playlist tests
* Revision flow tests

### Integration

* Search → retrieval → frontend
* Video completion → revision
* Revision → evaluation
* Evaluation → practice generation

---

# ⏳ Phase 23 — Production Hardening

**Status: NOT STARTED**

Focus:

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

# ⏳ Phase 24 — Deployment

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

Final objective:

```text
Publicly accessible
AI-powered
Pattern-first
DSA learning platform
```

---

# 🔎 AI Search Experience

The search system is intended to work beyond simple keyword matching.

Example query:

```text
"when should I shrink the window?"
```

Expected pipeline:

```text
User Query
    ↓
Query Understanding
    ↓
Hybrid Retrieval
    ↓
Reranking
    ↓
Relevant Pattern
    ↓
Relevant Video
    ↓
Relevant Timestamp
    ↓
Grounded Answer
```

The UI should then automatically select:

```text
Pattern Playlist
       ↓
Exact Video
       ↓
Exact Relevant Position
```

---

# 🤖 AI Revision Experience

When a learner finishes a video:

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
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       User Answers           │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       AI Validation          │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│       Mastery Score          │
└──────────────┬───────────────┘
               ↓
       ┌───────┴────────┐
       ↓                ↓
 External Resources   New Problems
       ↓                ↓
 LeetCode / GFG      4–5 Problems
```

---

# 🧠 Question Generation Philosophy

The system should not behave like a simple problem recommender.

It should test whether the learner actually understands the concept.

For example, after a Two Pointer video, AI may ask:

```text
কেন এই সমস্যাটিতে দুইটা pointer ব্যবহার করলে
O(n²) থেকে O(n) এ যাওয়া সম্ভব হচ্ছে?

যদি array sorted না হয় তাহলে কী ভেঙে যাবে?

এই approach-এর কোন invariant আমরা maintain করছি?
```

The goal is **conceptual depth**, not merely solving known problems.

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
```

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

### 7. Production Oriented

The project is being built as a real software system rather than only as an AI demo.

---

# 📈 Current Project Status

```text
Phases 1–14       ████████████████████  COMPLETE

Phase 15          ███████████████░░░░░  IN PROGRESS

Phase 16          ████████░░░░░░░░░░░░  IN PROGRESS

Phases 17–24      ░░░░░░░░░░░░░░░░░░░░  PLANNED
```

### Current active focus

> **Phase 16 — React Frontend**

Current work is focused on:

* Theme system
* Navigation
* Routing
* Pattern UI
* Playlist UI
* Video experience
* Search integration
* AI revision flow
* Responsive/mobile UI

---

# 🗺️ Remaining Roadmap

```text
Phase 16
   ↓
Complete React Frontend
   ↓
Phase 17
   ↓
Pattern / Playlist Navigation
   ↓
Phase 18
   ↓
Adaptive Practice
   ↓
Phase 19
   ↓
Weakness Detection
   ↓
Phase 20
   ↓
Adaptive Revision Engine
   ↓
Phase 21
   ↓
Evaluation System
   ↓
Phase 22
   ↓
Automated Testing
   ↓
Phase 23
   ↓
Production Hardening
   ↓
Phase 24
   ↓
Deployment
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

Learner answers

                ↓

AI validates

                ↓

Mastery:
67%

                ↓

Weak area detected:
"Window invariant"

                ↓

AI provides:

Relevant LeetCode
Relevant GFG
+
4–5 new concept problems

                ↓

Learner practices

                ↓

Mastery updated

                ↓

AI recommends next revision
```

---

# 🚀 End Goal

The end goal is not simply:

> **"An AI chatbot for DSA."**

The goal is:

> **An adaptive DSA learning and revision system that understands patterns, retrieves the exact learning context, tests conceptual understanding, measures mastery, identifies weaknesses, and continuously adapts the learner's revision path.**

---

## Current Milestone

**Current Phase: Phase 16 — React Frontend**

**Dataset Target: 128+ DSA Videos**

**Patterns: ~20–25**

**Architecture: React + FastAPI + Qdrant + RAG**

**Status: Active Development**

