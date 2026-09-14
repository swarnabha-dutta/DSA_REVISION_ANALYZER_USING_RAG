# DSA Revision Analyzer

An AI-powered DSA revision system that converts educational video content into a
structured, searchable knowledge base and uses pattern-aware hybrid retrieval,
reranking, grounded context construction, timestamp-aware retrieval, and LLM
generation to provide evidence-grounded revision support.

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
Timestamp-Aware Context
      ↓
Grounded Prompt Construction
      ↓
Groq LLM Generation
      ↓
Grounding Guard
      ↓
Grounded Answer
````

The long-term system will also use completed topics and patterns to generate
**pattern-specific practice problems without hints**.

---

# 🧠 Core Architecture

The current system uses a hybrid retrieval architecture with lexical search,
semantic search, Reciprocal Rank Fusion, Cross-Encoder reranking, structured
context assembly, timestamp-aware source provenance, grounded prompting, and
LLM generation.

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
                          │ Timestamp +      │
                          │ Provenance Layer │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Grounded Prompt  │
                          │     Builder      │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │    Groq LLM      │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Grounding Guard  │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │ Grounded Answer  │
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

# 🤖 Phase 13 — Grounded RAG Generation

Phase 13 connects the structured context pipeline to an LLM generation layer.

The objective is to generate answers from retrieved course material while
preserving source metadata and explicitly preventing unsupported claims.

---

## Grounded Prompt Builder

Implementation:

```text
backend/app/services/prompt_builder.py
```

The prompt builder converts the structured `AssembledContext` into a grounded
LLM prompt.

The prompt contains:

```text
System Instruction
      ↓
Grounding Rules
      ↓
Original User Query
      ↓
Retrieved Course Context
      ↓
Retrieval Metadata
```

The grounding instructions explicitly require the model to:

```text
* Answer only from the supplied retrieved context
* Do not use outside knowledge
* Do not invent unsupported information
* Do not guess when the retrieved context is insufficient
```

Empty retrieval is represented explicitly:

```text
[NO RETRIEVED COURSE CONTEXT AVAILABLE]
```

This prevents an empty retrieval result from being silently interpreted as valid
evidence.

---

## LLM Generator

Implementation:

```text
backend/app/services/llm_generator.py
```

The LLM generation flow is:

```text
AssembledContext
      ↓
Grounded Prompt
      ↓
Groq Chat Completion
      ↓
Structured LLMGenerationResult
```

Current configuration:

```text
Provider     : Groq
Model        : openai/gpt-oss-20b
Temperature  : 0.0
Max Tokens   : 1024
```

The generated result preserves:

```text
* Original query
* Generated answer
* Model name
* Retrieved context
* Source metadata
```

The generation result is also JSON/API serializable.

---

# 🛡️ Grounding & Hallucination Guard

Implementation:

```text
backend/scripts/test_grounding_guard.py
```

The grounding validation layer verifies:

```text
Explicit grounding restrictions
        ↓
Retrieved evidence visibility
        ↓
Metadata preservation
        ↓
Insufficient-context behavior
        ↓
Adversarial unsupported-query behavior
```

The system is intentionally tested with queries whose answers are not present
in the supplied course context.

Example:

```text
Retrieved context:

Two pointers use two indices. One pointer can start
from the left and another can start from the right.

Query:

What is the exact historical origin of the two pointer
technique, including who invented it and the year it
was first introduced?
```

The model correctly returned:

```text
The retrieved course material does not contain enough
information to answer that question.
```

This demonstrates that the model can refuse an unsupported question instead of
automatically using outside knowledge.

> Note: this validation does not mathematically guarantee zero hallucinations.
> It validates the implemented grounding instructions and adversarial
> insufficient-context behavior.

---

# 🧪 Phase 13 Validation

## Prompt Builder Integration Test

Implementation:

```text
backend/scripts/test_prompt_builder.py
```

Validation:

```text
✓ User query preserved.
✓ Retrieved context preserved.
✓ Retrieval metadata preserved.
✓ Grounding instructions present.
✓ Insufficient-context guard present.
✓ Chat message structure valid.
✓ Empty retrieval context handled safely.
```

Result:

```text
RESULT: 7/7 TESTS PASSED
```

---

## LLM Generator Integration Test

Implementation:

```text
backend/scripts/test_llm_generator.py
```

Validation:

```text
✓ LLM generation returned a structured result.
✓ Generated answer is non-empty.
✓ Original query preserved.
✓ Model recorded.
✓ Retrieved source metadata preserved.
✓ Generation result is API-serializable.
```

Result:

```text
RESULT: 6/6 TESTS PASSED
```

---

## End-to-End Grounded RAG Test

Implementation:

```text
backend/scripts/test_e2e_rag.py
```

The test validates the real retrieval-to-generation pipeline:

```text
Query
  ↓
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
Grounded Prompt Construction
  ↓
Groq LLM Generation
  ↓
Source Preservation
```

Example validated run:

```text
Semantic candidates       : 15
BM25 candidates           : 15
RRF candidates            : 23
Final reranked results    : 5
Context items             : 5
```

The real pipeline successfully generated a grounded answer and preserved the
retrieved source metadata.

Result:

```text
✓ Retrieval
✓ RRF fusion
✓ Cross-Encoder reranking
✓ Context assembly
✓ Grounded prompt construction
✓ Groq LLM generation
✓ Source preservation

✓ END-TO-END RAG TEST PASSED
```

---

## Grounding Quality Test

Implementation:

```text
backend/scripts/test_grounding_guard.py
```

Validation:

```text
✓ Explicit grounding restrictions present.
✓ Empty-context safety guard present.
✓ Retrieved evidence is visible to the LLM.
✓ Source metadata is available to the grounding layer.
✓ Retrieved context is explicitly structured.
✓ Query and evidence are jointly available.
✓ Empty retrieval is explicitly represented.
✓ Unsupported query triggered a grounded refusal.
```

Result:

```text
RESULT: 8/8 TESTS PASSED
```

---

# ⏱️ Phase 14 — Timestamp-Aware Retrieval

Phase 14 extends the grounded RAG pipeline with timestamp-aware source
provenance and direct navigation back to the relevant portion of the source
video.

The objective is to ensure that retrieved explanations remain connected to
their original video location.

```text
Retrieved Chunk
      ↓
Timestamp Metadata
      ↓
Relevant Time Range
      ↓
YouTube Jump Link
      ↓
Provenance-Aware Context
      ↓
Timestamp-Grounded Prompt
      ↓
Grounded Explanation
```

---

## Timestamp-Aware Result Formatting

The context layer formats source timestamps into human-readable values.

Examples:

```text
0 seconds       → 00:00
83.5 seconds    → 01:23
127.9 seconds   → 02:07
```

Timestamp ranges are represented as:

```text
Timestamp: 01:23 -> 02:07
```

Missing timestamps are handled safely without inventing source locations.

Implementation:

```text
backend/app/services/context_assembler.py
```

Validation:

```text
backend/scripts/test_timestamp_formatting.py
```

Result:

```text
Passed : 7/7

✓ PHASE 14.1 TIMESTAMP FORMATTING TEST PASSED
```

---

## Video Jump Links

Retrieved context can expose a direct YouTube link to the relevant timestamp.

Example:

```text
https://www.youtube.com/watch?v=dyG4JBKh6tA&t=83s
```

The timestamp is converted to a non-negative integer second before constructing
the jump link.

Missing video IDs are handled safely.

Implementation:

```text
backend/app/services/context_assembler.py
```

Validation:

```text
backend/scripts/test_video_jump_links.py
```

Result:

```text
Passed : 6/6

✓ PHASE 14.2 VIDEO JUMP LINK TEST PASSED
```

Timestamp and jump-link integration:

```text
backend/scripts/test_timestamp_jump_integration.py
```

Result:

```text
Passed : 8/8

✓ TIMESTAMP + VIDEO JUMP LINK INTEGRATION TEST PASSED
```

---

## Relevant Time-Range Extraction

The system preserves the original relevant timestamp range associated with a
retrieved chunk.

Example:

```text
Start    : 83.5
End      : 127.9
Duration : 44.4 seconds
```

The extraction layer validates:

```text
✓ Valid timestamp ranges
✓ Integer timestamps
✓ Zero-duration ranges
✓ Missing start timestamps
✓ Missing end timestamps
✓ Missing timestamp ranges
✓ Reversed ranges
✓ Negative timestamps
✓ Numeric string conversion
✓ Invalid timestamp values
```

Implementation:

```text
backend/app/services/context_assembler.py
```

Validation:

```text
backend/scripts/test_relevant_time_range.py
```

Result:

```text
Passed : 13/13

✓ RELEVANT TIME-RANGE TEST PASSED
```

Integration validation:

```text
backend/scripts/test_relevant_time_range_integration.py
```

Result:

```text
Passed : 9/9

✓ RELEVANT TIME-RANGE INTEGRATION TEST PASSED
```

---

## Timestamp-Grounded Explanations

The grounded prompt now explicitly handles timestamp and video provenance.

The system instructs the LLM to:

```text
* Ground explanations in supplied timestamped evidence.
* Use supplied video provenance when referring to source material.
* Preserve supplied timestamps and video references.
* Never invent timestamps, timestamp ranges, video IDs, or video links.
* Avoid fabricating temporal references when they are absent.
```

Implementation:

```text
backend/app/services/prompt_builder.py
```

Validation:

```text
backend/scripts/test_timestamp_grounded_explanation.py
```

Result:

```text
Passed : 14/14

✓ TIMESTAMP-GROUNDED EXPLANATION TEST PASSED
```

---

## Context Provenance

Phase 14 also preserves retrieval provenance throughout context assembly.

Each context item can preserve:

```text
point_id
video_id
pattern
sub_pattern
timestamp_start
timestamp_end
rrf_score
reranker_score
original chunk text
```

This allows downstream components to retain evidence about where each retrieved
piece of information originated.

Implementation:

```text
backend/app/services/context_assembler.py
```

Validation:

```text
backend/scripts/test_context_provenance.py
```

Result:

```text
Passed : 15/15

✓ CONTEXT PROVENANCE TEST PASSED
```

Integration validation:

```text
backend/scripts/test_provenance_integration.py
```

Result:

```text
Passed : 20/20

✓ PROVENANCE INTEGRATION TEST PASSED
```

---

## Prompt / Context Integration

Timestamp-aware context is preserved when constructing the final grounded prompt.

Validation:

```text
backend/scripts/test_prompt_context_integration.py
```

Result:

```text
Passed : 9/9

✓ PROMPT / CONTEXT INTEGRATION TEST PASSED
```

Prompt builder regression:

```text
backend/scripts/test_prompt_builder.py
```

Result:

```text
RESULT: 7/7 TESTS PASSED
```

---

## Phase 14 Validation Summary

```text
Timestamp Formatting            : 7/7 PASSED
Video Jump Links                : 6/6 PASSED
Timestamp + Jump Integration    : 8/8 PASSED
Relevant Time-Range             : 13/13 PASSED
Time-Range Integration          : 9/9 PASSED
Prompt / Context Integration    : 9/9 PASSED
Prompt Builder Regression       : 7/7 PASSED
Context Provenance              : 15/15 PASSED
Provenance Integration          : 20/20 PASSED
Context Assembly Regression     : 9/9 PASSED
Timestamp-Grounded Explanation  : 14/14 PASSED
```

### Phase 14 Final Pipeline

```text
Final Reranked Top-K
        ↓
Context Assembly
        ↓
Metadata + Score Preservation
        ↓
Timestamp Formatting
        ↓
Relevant Time-Range
        ↓
YouTube Jump Link
        ↓
Provenance-Aware Context
        ↓
Timestamp-Grounded Prompt
        ↓
Groq LLM
        ↓
Grounded Answer
```

**Phase 14: COMPLETE**

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

Grounded Prompt Builder
    ✓ 7/7 checks passed

LLM Generator
    ✓ 6/6 checks passed

End-to-End Grounded RAG
    ✓ Passed

Grounding / Hallucination Guard
    ✓ 8/8 checks passed

Timestamp Formatting
    ✓ 7/7 checks passed

Video Jump Links
    ✓ 6/6 checks passed

Relevant Time-Range
    ✓ 13/13 checks passed

Timestamp + Jump Integration
    ✓ 8/8 checks passed

Time-Range Integration
    ✓ 9/9 checks passed

Prompt / Context Integration
    ✓ 9/9 checks passed

Context Provenance
    ✓ 15/15 checks passed

Provenance Integration
    ✓ 20/20 checks passed

Timestamp-Grounded Explanation
    ✓ 14/14 checks passed
```

The current validated retrieval-to-generation pipeline is:

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
Timestamp + Provenance Layer
  ↓
Grounded Prompt Builder
  ↓
Groq LLM
  ↓
Grounding Guard
  ↓
Grounded Answer
```

---

# 🧪 Testing

## Hybrid Retrieval Test

Run:

```powershell
python .\scripts\test_hybrid_retrieval.py
```

---

## Cross-Encoder Benchmark

Run:

```powershell
python .\scripts\benchmark_reranking.py
```

---

## Context Assembly Test

Run:

```powershell
python .\scripts\test_context_assembly.py
```

---

## Context Integration Test

Run:

```powershell
python .\scripts\test_context_integration.py
```

---

## Prompt Builder Test

Run:

```powershell
python .\scripts\test_prompt_builder.py
```

---

## LLM Generator Test

Run:

```powershell
python .\scripts\test_llm_generator.py
```

---

## End-to-End RAG Test

Run:

```powershell
python .\scripts\test_e2e_rag.py
```

---

## Grounding Quality Test

Run:

```powershell
python .\scripts\test_grounding_guard.py
```

The grounding test includes both deterministic prompt-level checks and a real
adversarial LLM test for unsupported questions.

---

## Timestamp Formatting Test

Run:

```powershell
python .\scripts\test_timestamp_formatting.py
```

---

## Video Jump Link Test

Run:

```powershell
python .\scripts\test_video_jump_links.py
```

---

## Timestamp + Jump Integration Test

Run:

```powershell
python .\scripts\test_timestamp_jump_integration.py
```

---

## Relevant Time-Range Test

Run:

```powershell
python .\scripts\test_relevant_time_range.py
```

---

## Relevant Time-Range Integration Test

Run:

```powershell
python .\scripts\test_relevant_time_range_integration.py
```

---

## Prompt / Context Integration Test

Run:

```powershell
python .\scripts\test_prompt_context_integration.py
```

---

## Context Provenance Test

Run:

```powershell
python .\scripts\test_context_provenance.py
```

---

## Provenance Integration Test

Run:

```powershell
python .\scripts\test_provenance_integration.py
```

---

## Timestamp-Grounded Explanation Test

Run:

```powershell
python .\scripts\test_timestamp_grounded_explanation.py
```

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
│   │       ├── prompt_builder.py
│   │       ├── llm_generator.py
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
│   │   ├── test_prompt_builder.py
│   │   ├── test_prompt_context_integration.py
│   │   ├── test_llm_generator.py
│   │   ├── test_e2e_rag.py
│   │   ├── test_grounding_guard.py
│   │   ├── test_timestamp_formatting.py
│   │   ├── test_video_jump_links.py
│   │   ├── test_timestamp_jump_integration.py
│   │   ├── test_relevant_time_range.py
│   │   ├── test_relevant_time_range_integration.py
│   │   ├── test_context_provenance.py
│   │   ├── test_provenance_integration.py
│   │   ├── test_timestamp_grounded_explanation.py
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

---

## Phase 2 — YouTube Transcript Ingestion

* [x] YouTube transcript extraction
* [x] Transcript storage
* [x] Timestamp preservation

---

## Phase 3 — Transcript Translation

* [x] Translation pipeline
* [x] Batched translation
* [x] Retry handling
* [x] Resume-safe checkpoints
* [ ] Complete translation of the remaining representative dataset

---

## Phase 4 — Intelligent Transcript Chunking

* [x] Character-aware chunking
* [x] Chunk overlap
* [x] Timestamp preservation
* [x] Chunk JSON generation

---

## Phase 5 — Embedding Generation

* [x] Sentence Transformer integration
* [x] 384-dimensional embeddings
* [x] Local embedding generation

---

## Phase 6 — Qdrant Vector Database

* [x] Qdrant collection
* [x] Vector ingestion
* [x] Payload metadata
* [x] Payload indexes
* [x] Deterministic point IDs

---

## Phase 7 — Semantic Retrieval

* [x] Query embedding
* [x] Vector search
* [x] Top-K retrieval
* [x] Structured retrieval results

---

## Phase 8 — DSA Knowledge & Metadata Layer

* [x] Canonical DSA taxonomy
* [x] Sub-pattern taxonomy
* [x] Playlist mapping
* [x] Metadata validation
* [x] Chunk metadata enrichment

---

## Phase 9 — Query Understanding

* [x] Intent classification
* [x] Pattern detection
* [x] Sub-pattern detection
* [x] Confidence scoring
* [x] Unsupported algorithm protection

---

## Phase 10 — Metadata-Aware Retrieval

* [x] Pattern filtering
* [x] Sub-pattern filtering
* [x] Metadata validation
* [x] Safe fallback behavior
* [x] Retrieval integration testing

---

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

* [x] LLM answer generation
* [x] Groq LLM integration
* [x] Source-grounded responses
* [x] Retrieval-context prompting
* [x] Grounding instructions
* [x] Insufficient-context handling
* [x] Structured generation result
* [x] Source metadata preservation
* [x] End-to-end grounded RAG integration
* [x] Adversarial unsupported-query test
* [x] Grounding quality validation

### Phase 13 Final Pipeline

```text
Final Reranked Top-K
        ↓
Context Assembly
        ↓
Grounded Prompt Builder
        ↓
Groq LLM
        ↓
Grounding Guard
        ↓
Grounded Answer
```

Validation:

```text
Prompt Builder        : 7/7 PASSED
LLM Generator         : 6/6 PASSED
Grounding Guard       : 8/8 PASSED
End-to-End RAG        : PASSED
```

**Phase 13: COMPLETE**

---

## Phase 14 — Timestamp-Aware Retrieval

* [x] Timestamp-aware result formatting
* [x] Video jump links
* [x] Relevant time-range extraction
* [x] Timestamp-grounded explanations

Additional engineering work:

* [x] Context provenance preservation
* [x] Timestamp + jump-link integration
* [x] Relevant time-range integration
* [x] Prompt/context timestamp integration
* [x] Provenance integration validation
* [x] Context assembly regression validation
* [x] Timestamp-grounded explanation validation

### Phase 14 Final Pipeline

```text
Final Reranked Top-K
        ↓
Context Assembly
        ↓
Metadata + Score Preservation
        ↓
Timestamp Formatting
        ↓
Relevant Time-Range
        ↓
YouTube Jump Link
        ↓
Provenance-Aware Context
        ↓
Timestamp-Grounded Prompt
        ↓
Groq LLM
        ↓
Grounded Answer
```

Validation:

```text
Timestamp Formatting            : 7/7 PASSED
Video Jump Links                : 6/6 PASSED
Timestamp + Jump Integration    : 8/8 PASSED
Relevant Time-Range             : 13/13 PASSED
Time-Range Integration          : 9/9 PASSED
Prompt / Context Integration    : 9/9 PASSED
Prompt Builder Regression       : 7/7 PASSED
Context Provenance              : 15/15 PASSED
Provenance Integration          : 20/20 PASSED
Context Assembly Regression     : 9/9 PASSED
Timestamp-Grounded Explanation  : 14/14 PASSED
```

**Phase 14: COMPLETE**

---

## Phase 15 — FastAPI Backend

* [ ] Retrieval API
* [ ] Query API
* [ ] RAG API
* [ ] Metadata endpoints
* [ ] Request validation

---

## Phase 16 — React Frontend

* [ ] Search interface
* [ ] Revision interface
* [ ] Retrieved source display
* [ ] Video/timestamp navigation

---

## Phase 17 — Pattern / Playlist Navigation

* [ ] Pattern browser
* [ ] Playlist navigation
* [ ] Video ordering
* [ ] Topic progression

---

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

---

## Phase 19 — Performance & Weakness Detection

* [ ] Track practice performance
* [ ] Detect weak sub-patterns
* [ ] Detect recurring mistakes
* [ ] Identify knowledge gaps

---

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

---

## Phase 21 — Evaluation System

* [ ] Retrieval evaluation dataset
* [ ] Recall@K
* [ ] Precision@K
* [ ] MRR
* [ ] nDCG@K
* [ ] Reranking evaluation
* [ ] RAG answer evaluation

---

## Phase 22 — Automated Testing

* [ ] Unit tests
* [ ] Integration tests
* [ ] Retrieval regression tests
* [ ] API tests
* [ ] End-to-end tests

---

## Phase 23 — Production Hardening

* [ ] Logging
* [ ] Error handling
* [ ] Performance optimization
* [ ] Model caching
* [ ] Security hardening
* [ ] Configuration cleanup

---

## Phase 24 — Deployment

* [ ] Backend deployment
* [ ] Frontend deployment
* [ ] Production Qdrant
* [ ] Monitoring
* [ ] Production documentation

---

# 📌 Current Project Status

The project has now completed the retrieval, context-construction, grounded
RAG generation, and timestamp-aware retrieval foundation through **Phase 14**.

The current validated system can:

```text
1. Ingest educational DSA videos
2. Extract transcripts
3. Translate transcript content
4. Create structured chunks
5. Enrich chunks with DSA metadata
6. Generate embeddings
7. Store vectors in Qdrant
8. Understand user queries
9. Apply metadata-aware retrieval
10. Perform semantic retrieval
11. Perform BM25 lexical retrieval
12. Fuse candidates using RRF
13. Rerank candidates using a Cross-Encoder
14. Assemble structured LLM context
15. Preserve retrieval provenance
16. Preserve source timestamps
17. Extract relevant time ranges
18. Generate YouTube timestamp jump links
19. Build grounded prompts
20. Generate answers using Groq
21. Ground explanations in timestamped evidence
22. Preserve source metadata
23. Handle insufficient retrieval context
24. Validate unsupported-query behavior
```

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
Semantic + BM25
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
Timestamp + Provenance
   ↓
Grounded Prompt Builder
   ↓
Groq LLM
   ↓
Grounding Guard
   ↓
Grounded Answer
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
Phase 13  ✓
Phase 14  ✓
```

`*` Phase 3 still contains the remaining representative-dataset translation
work.

The next major development stage is:

```text
Phase 15 — FastAPI Backend
```

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
      ↓
Grounded Prompt
      ↓
LLM
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

---

## 7. Grounding Is Evidence-First

The LLM should not be treated as the source of truth.

The intended generation architecture is:

```text
Retrieved Course Evidence
          ↓
Structured Context
          ↓
Grounded Prompt
          ↓
LLM
          ↓
Grounded Answer
```

The model is instructed to answer only from supplied retrieved context.

When sufficient evidence is unavailable, the system should prefer an explicit
insufficient-information response over guessing.

Timestamp and video references are also treated as evidence. The model must not
invent source locations that are not present in the retrieved context.

---

## 8. Retrieval Metadata Must Survive the RAG Pipeline

Retrieval metadata is not discarded after ranking.

Important metadata such as:

```text
point_id
video_id
pattern
sub_pattern
timestamp_start
timestamp_end
rrf_score
reranker_score
```

is preserved through context assembly and made available to downstream
generation and source presentation.

This enables:

```text
Source Provenance
      ↓
Timestamp-Aware Context
      ↓
Video Navigation
      ↓
Grounded Explanation
```

---

## 9. Retrieval Evaluation Must Be Evidence-Based

The system does not claim that a retrieval technique is better merely because its
score or ranking changed.

Meaningful retrieval evaluation should eventually use human-validated relevance
labels and metrics such as:

```text
Recall@K
Precision@K
MRR
nDCG@K
```

Similarly, grounded answer evaluation should eventually measure:

```text
Answer correctness
Faithfulness to retrieved evidence
Source attribution quality
Unsupported-claim rate
```

---

# 🚀 Development Philosophy

The project is being built incrementally as a real retrieval and RAG system.

Each major stage is validated before the next stage is added:

```text
Implement
   ↓
Unit Test
   ↓
Integration Test
   ↓
End-to-End Test
   ↓
Validate Behavior
   ↓
Move to Next Phase
```

The goal is not simply to make the system produce an answer.

The goal is to build a pipeline where:

```text
Retrieval
   ↓
Ranking
   ↓
Context
   ↓
Evidence
   ↓
Generation
   ↓
Source Navigation
```
