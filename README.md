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

    User Question
          ↓
    AI Retrieval
          ↓
    Relevant Video
          ↓
    Relevant Timestamp
          ↓
    Direct Revision

---

# 2. Main Goal

Build a DSA-specific RAG system that understands a complete
YouTube DSA course and can retrieve the most relevant lecture
section for a user's question.

The system should preserve:

- Video identity
- Playlist/pattern information
- Transcript
- English translation
- Timestamp
- DSA pattern
- DSA sub-pattern
- Relevant contextual chunks

---

# 3. Core User Experience

The intended user experience is:

    User asks:

    "Explain the two pointer pattern where
    both pointers move towards each other."

The system should:

    1. Understand the query.
    2. Identify the DSA pattern.
    3. Identify the relevant sub-pattern.
    4. Search only the relevant knowledge space.
    5. Retrieve the most relevant transcript chunks.
    6. Identify the source video.
    7. Identify the exact timestamp.
    8. Generate a concise explanation.
    9. Show the relevant video section in the UI.

---

# 4. Planned Architecture
```
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

----------------
