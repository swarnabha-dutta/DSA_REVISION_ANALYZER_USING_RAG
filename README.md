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
