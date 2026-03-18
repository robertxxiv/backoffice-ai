# Local AI Provider Tech Spec

## Goal

Allow Backoffice AI to run with cloud, local, or hybrid AI backends, configured entirely from `.env`, without changing the public API contract.

Supported target modes:

- `openai + openai`
- `local + local`
- `local + openai`
- `openai + local`

Where the first provider is for embeddings and the second is for generation.

## Scope

This specification covers:

- configuration model
- provider interfaces
- index compatibility rules
- deployment/runtime requirements
- rollout plan

This specification does not cover:

- automatic migration of old embeddings to new models
- multiple live embedding spaces in the same active index
- per-request runtime provider switching

## Provider Architecture

The existing module boundaries should remain stable.

### Embeddings interface

```python
embed_texts(texts: list[str]) -> list[list[float]]
embed_query(text: str) -> list[float]
```

### Generation interface

```python
generate_answer(query: str, chunks: list[RetrievedChunk]) -> dict[str, Any]
```

Provider families:

- embeddings
  - `openai`
  - `local`
- generation
  - `openai`
  - `local`

Local backends behind those providers:

- `ollama`
- `llama_cpp`
- later `vllm`

## Configuration

Top-level provider switches:

```env
EMBEDDING_PROVIDER=openai
GENERATION_PROVIDER=openai
```

### OpenAI settings

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
GENERATION_MODEL=gpt-5-mini
```

### Local settings

```env
LOCAL_EMBEDDING_BACKEND=ollama
LOCAL_EMBEDDING_MODEL=bge-m3
LOCAL_EMBEDDING_BASE_URL=http://ollama:11434

LOCAL_GENERATION_BACKEND=ollama
LOCAL_GENERATION_MODEL=qwen2.5:7b-instruct
LOCAL_GENERATION_BASE_URL=http://ollama:11434
```

### Optional operational settings

```env
LOCAL_REQUEST_TIMEOUT_SECONDS=120
LOCAL_MAX_CONTEXT_CHARS=6000
LOCAL_GENERATION_TEMPERATURE=0.1
LOCAL_GENERATION_MAX_TOKENS=800
```

## Provider Matrix

| Embeddings | Generation | Supported | Notes |
|---|---|---:|---|
| `openai` | `openai` | yes | current cloud mode |
| `local` | `local` | yes | full local mode |
| `local` | `openai` | yes | privacy/cost compromise |
| `openai` | `local` | yes | valid but less common |

## Index Compatibility Rules

Embedding spaces must be treated as incompatible unless all of these match:

- provider
- backend
- model
- vector dimension

Persist embedding identity with indexed data:

- `embedding_provider`
- `embedding_backend`
- `embedding_model`
- `embedding_dimensions`

Recommended additional derived field:

- `embedding_fingerprint = provider:backend:model:dimensions`

### Required behavior

- if the embedding config changes, the index becomes stale
- queries against mismatched embeddings must not silently proceed

Recommended v1 behavior:

- mark documents as stale
- require explicit reindex

Recommended error message:

`Indexed embeddings were created with a different embedding model/provider. Reindex required.`

## Database Changes

Recommended additions to persisted embedding metadata:

- `provider`
- `backend`
- `model`
- `dimensions`

Optional but useful:

- store active embedding fingerprint in document or index metadata for faster stale-index detection

## Runtime Behavior

### Ingest

No behavior change.

### Reindex

Uses the currently configured embedding provider and model.

### Query

- query embedding uses the currently configured embedding provider
- retrieval must only operate on compatible indexed embeddings
- generation uses the currently configured generation provider

### Mismatch case

If the active embedding provider/model does not match the indexed data:

- return `400` or `409`
- instruct the operator to reindex

## Local Backend Recommendation

First local backend to implement:

- `ollama`

Reason:

- simplest deployment path
- plain HTTP API
- practical for small-company deployments

### Recommended first local models

Embeddings:

- `bge-m3`
- `multilingual-e5-large`

Generation:

- `qwen2.5:7b-instruct`
- `llama3.1:8b-instruct`
- `mistral:7b-instruct`

## Deployment Model

Default stack remains unchanged.

Local AI should be optional through:

- a Docker Compose profile
- or a compose override file

Example direction:

```bash
docker compose --profile local-ai up -d
```

Possible local mode services:

- `api`
- `worker`
- `db`
- `frontend`
- optional `ollama`

## Error Handling

Need explicit provider-specific errors for:

- local backend unavailable
- local model not installed or not pulled
- embedding dimension mismatch
- unsupported local backend
- generation timeout
- malformed structured output from a local model

User-facing API responses should stay concise and actionable.

## Testing Requirements

Minimum coverage:

- config loads correctly for each provider mode
- provider factory selects the right implementation
- local embedding provider returns vectors
- local generation provider returns structured output
- embedding fingerprint mismatch marks index stale or blocks query
- query fails clearly when reindex is required

## Rollout Plan

1. Add config schema for local providers and backends.
2. Add provider factories for `local`.
3. Implement one local backend first: `ollama`.
4. Add embedding fingerprint persistence and mismatch detection.
5. Add docs and Compose profile for local mode.
6. Add regression tests for all supported provider combinations.

## Recommendation

Best first implementation path:

- local embeddings via `ollama` or a sentence-transformer service
- local generation via `ollama`
- keep OpenAI mode unchanged
- require reindex on any embedding provider/model change

This gives:

- clean `.env` switching
- hybrid capability
- minimal architectural churn
- a practical path to privacy-first deployments
