# Administrator Guide

## Purpose

This page is for the person operating the system day to day.

## What an Administrator Does

- starts and stops the stack
- monitors indexing jobs
- verifies documents are indexed
- reruns indexing when content changes
- deletes obsolete documents
- checks logs when users report issues
- creates database backups

## Core Services

- `api`
- `worker`
- `db`
- `frontend`

## Frontend Views

The operator-facing frontend is now split into these routes:

- `/`
- `/dashboard`
- `/ingestion`
- `/search`
- `/documents`
- `/jobs`
- `/settings`

Operationally:

- `Ingestion` is for new source entry
- `Documents` is for reindex/delete management
- `Jobs` is for pipeline visibility
- `Settings` is read-only runtime information

## Token Usage and Cost

This matters only when the system is running with:

- `EMBEDDING_PROVIDER=openai`
- `GENERATION_PROVIDER=openai`

If the system is running in `mock` mode, there is no OpenAI cost.

### When cost happens

Cost is incurred when:

- documents are reindexed
- users run queries

Upload alone does not consume OpenAI tokens.

### Current model defaults

- embeddings: `text-embedding-3-small`
- generation: `gpt-5-mini`

Reference pricing used for estimation:

- embeddings: `$0.02 / 1M input tokens`
- generation input: `$0.25 / 1M input tokens`
- generation output: `$2.00 / 1M output tokens`

Official references:

- https://developers.openai.com/api/docs/models/text-embedding-3-small
- https://developers.openai.com/api/docs/models/gpt-5-mini
- https://developers.openai.com/api/docs/pricing

### Reindex estimate

Formula:

```text
embedding_cost = embedded_tokens / 1,000,000 * 0.02
```

Because the default chunking overlaps chunks, the embedded token count is usually higher than the original document token count.

### Query estimate

Formula:

```text
query_cost =
(query_embedding_tokens / 1,000,000 * 0.02)
+ (llm_input_tokens / 1,000,000 * 0.25)
+ (llm_output_tokens / 1,000,000 * 2.00)
```

Typical example:

- query embedding: `20` tokens
- generation input: `1,500` tokens
- generation output: `200` tokens
- estimated query cost: about `$0.00078`

### Operational advice

- avoid unnecessary reindexing of unchanged documents
- keep `top_k` and context size reasonable
- review the OpenAI usage dashboard regularly
- if you need exact per-query cost tracking, add usage logging in the application layer

### Local estimation helper

This repository includes a simple local estimator:

```bash
.venv/bin/python backend/scripts/cost_calculator.py index --document-tokens 50000
.venv/bin/python backend/scripts/cost_calculator.py query --input-tokens 1500 --output-tokens 200
```

## Operational Checks

### Health check

```bash
curl http://localhost:8000/health
```

### List documents

```bash
curl http://localhost:8000/documents
```

Useful fields:

- `status`
- `version`
- `chunk_count`
- `embedding_count`
- `is_index_stale`
- `index_error`
- `metadata_summary.category`

### Inspect one document

```bash
curl http://localhost:8000/documents/<document_id>
```

### Inspect one job

```bash
curl http://localhost:8000/jobs/<job_id>
```

## Document Lifecycle Policy

The system treats `source_type + source_ref` as the canonical identity.

That means:

- ingesting the same source again does not create a second independent document
- if content changes, the existing record is updated and versioned
- any old chunk or embedding state is invalidated automatically

Metadata normalization policy:

- `category` is the canonical content grouping field
- if users upload documents with `domain` or `type` only, the backend also derives `category`
- user-facing filters in the frontend are based on normalized metadata, not on raw key naming

## Indexing Policy

When a document changes:

- the document becomes stale
- old chunks and embeddings are cleared
- the document must be reindexed

You can reindex:

- a single document
- all documents

### Reindex one document

```bash
curl -X POST http://localhost:8000/reindex \
  -H 'Content-Type: application/json' \
  -d '{
    "document_id":"<document_id>",
    "run_inline":true,
    "strategy":"overlap",
    "chunk_size":512,
    "overlap_tokens":64
  }'
```

### Reindex everything

```bash
curl -X POST http://localhost:8000/reindex \
  -H 'Content-Type: application/json' \
  -d '{
    "run_inline":false,
    "strategy":"overlap",
    "chunk_size":512,
    "overlap_tokens":64
  }'
```

Use `run_inline=false` when you want the worker to process jobs asynchronously.

## Recommended Daily Checks

At minimum:

1. check `/health`
2. check the landing page and dashboard load
3. verify no documents are unexpectedly stale
4. verify no jobs are stuck in `failed`

## Backup Policy

Recommended minimum policy:

- daily PostgreSQL dump
- before every deployment
- before any manual data fix

Example:

```bash
mkdir -p backups
docker compose exec db pg_dump -U postgres -d rag_system > backups/rag_system_$(date +%F_%H-%M-%S).sql
```

## Safe Restart Procedure

If the system becomes unstable:

```bash
docker compose restart api worker frontend
```

If the DB itself is unhealthy:

```bash
docker compose restart db
docker compose restart api worker frontend
```

## When to Delete a Document

Delete a document when:

- it was uploaded by mistake
- it is obsolete and should not be retrieved
- the source identity should be reset completely

Command:

```bash
curl -X DELETE http://localhost:8000/documents/<document_id>
```

Deleting a document removes its chunks, embeddings, and related pending job state.

## Current Operational Limitation

The system does not yet support:

- login
- user permissions
- per-document access control

Treat the deployment as trusted-internal only until auth is added.

## Current Query Output Model

The current query response is split into two layers:

- `answer`: Markdown for direct user display
- `machine_output`: optional structured JSON for formatting-oriented flows, especially travel/activity catalog extraction

For admins, this means:

- the frontend is expected to render Markdown, not plain text
- catalog questions may return richer structured data alongside the visible answer
- source UUIDs remain internal and should not appear in the visible answer body
