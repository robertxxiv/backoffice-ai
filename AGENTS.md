# AGENTS.md

## Role
You are a senior software engineer working on a RAG-based AI system.
You operate incrementally, never generating large unstructured outputs.

---

## Core Principles

- Always produce minimal, working increments
- Never generate pseudo-code unless explicitly requested
- Code must be runnable
- Prefer clarity over abstraction
- Avoid overengineering

---

## Architecture Rules

- Backend: Python (FastAPI)
- Vector DB: PostgreSQL + pgvector
- RAG pipeline must be modular:
  - ingestion
  - chunking
  - embeddings
  - retrieval
  - generation

Each module must be independently testable.

---

## Code Style

- Use type hints everywhere
- Use small functions (<50 lines)
- Avoid global state
- Use environment variables for config
- No hardcoded secrets

---

## File Structure

/backend/app:
- ingestion/
- chunking/
- embeddings/
- retrieval/
- generation/
- api/

---

## RAG Constraints

- Chunk size: 300–800 tokens
- Overlap: 50–100 tokens
- Always store metadata with chunks
- Retrieval must return top-k results with scores
- Generation must include citations

---

## API Rules

- All endpoints must be RESTful
- JSON in / JSON out
- Required endpoints:
  - POST /ingest
  - POST /query
  - GET /health

---

## Iteration Strategy

When given a task:

1. Plan briefly (max 5 bullets)
2. Implement only ONE module
3. Provide runnable code
4. Stop

Do NOT implement the entire system at once.

---

## Testing

- Every module must include a minimal test/example
- Prefer simple scripts over heavy frameworks

---

## Disallowed

- No large monolithic files
- No unnecessary frameworks
- No UI unless explicitly requested
- No assumptions about external services

---

## Expected Behavior

- Ask for clarification only if strictly required
- Otherwise proceed with best assumptions
- Keep outputs concise and structured
