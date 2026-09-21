# Retrieval-augmented generation

> Status: designed, implemented in Phase 3.

## Pipeline

```text
Upload → Validate → Extract / OCR → Clean → Chunk → Metadata
      → Embed → Vector store → Retrieve → Rerank → LLM → Cited answer
```

## Chunk metadata

Every chunk stores: `university`, `department`, `course`, `semester`,
`document_type`, `academic_year`, `uploaded_by`, `created_at`, `source`,
`page_number`. Retrieval filters on this metadata before ranking, so a
second-semester student is not answered from another programme's regulations.

## Citations

Document-grounded answers render the claim and its source:

> According to the Academic Regulations document, students must maintain 75%
> attendance to sit the end-semester examination.
> **Source:** Academic Regulations 2026, page 18.

If retrieval returns nothing above the similarity threshold, the system states
that no source was found rather than generating an answer from model memory.

## Vector store

pgvector is the default because PostgreSQL is already in the stack. Access goes
through a repository interface, so Qdrant or Weaviate can be substituted by
changing `VECTOR_BACKEND` and providing the corresponding implementation.

## Access control

Retrieval is always scoped to documents the requesting user may read: their own
uploads, their department and programme material, and university-wide public
documents. Access is enforced in the query, not in the prompt.
