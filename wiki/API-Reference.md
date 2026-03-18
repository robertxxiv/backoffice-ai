# API Reference

This page documents the current HTTP API exposed by Backoffice AI.

Base URL:

- `http://localhost:8000`

Content types:

- JSON request / JSON response for most endpoints
- multipart form data for file uploads to `POST /ingest`

Current auth model:

- no authentication yet
- treat the API as trusted-internal only

## Conventions

### Error shape

Most API errors return:

```json
{
  "detail": "Human-readable error message"
}
```

### Metadata behavior

The system normalizes metadata for filtering and display.

Important rules:

- `category` is the canonical grouping field
- if uploaded metadata includes `domain` or `type`, the backend also derives `category`
- original metadata keys are preserved

Examples:

- input metadata: `{"domain":"quotes","country":"NO"}`
- returned metadata summary: `{"domain":"quotes","country":"NO","category":"quotes"}`

### Query result model

`POST /query` returns three output layers:

- `answer`: Markdown intended for direct user display
- `sources`: evidence chunks used for the answer
- `machine_output`: optional structured JSON for extraction-oriented flows such as travel/activity catalogs

## `GET /health`

Checks API and database readiness.

### Example

```bash
curl http://localhost:8000/health
```

### Response

```json
{
  "status": "ok",
  "database": "ok",
  "embedding_provider": "openai",
  "generation_provider": "openai",
  "api_docs_enabled": false,
  "upload_limits": {
    "file_bytes": 10485760,
    "request_bytes": 12582912,
    "json_bytes": 2097152
  }
}
```

## `POST /ingest`

Ingests a document by file upload or JSON request.

Supported inputs:

- file upload: `PDF`, `HTML`, `Markdown`, `JSON`
- URL fetch
- raw text or JSON payload

### Multipart upload

Fields:

- `file`
- optional `metadata` as JSON string

### Example: upload a PDF

```bash
curl -X POST http://localhost:8000/ingest \
  -F 'file=@catalog.pdf' \
  -F 'metadata={"type":"travel_catalog","language":"it","country":"NO"}'
```

### Example: upload Markdown

```bash
curl -X POST http://localhost:8000/ingest \
  -F 'file=@pricing-rules.md' \
  -F 'metadata={"domain":"quotes","country":"NO"}'
```

### JSON payload mode

Exactly one of these is required:

- `url`
- `payload`

Optional:

- `metadata`
- `source_name`

### Example: JSON payload

```bash
curl -X POST http://localhost:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "payload": {
      "service": "Audit",
      "vat": 25,
      "season": "winter"
    },
    "metadata": {
      "domain": "quotes",
      "country": "NO"
    },
    "source_name": "pricing-rules"
  }'
```

### Example: URL ingest

```bash
curl -X POST http://localhost:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://example.com/pricing-page",
    "metadata": {
      "category": "pricing_page",
      "language": "en"
    }
  }'
```

### Response

```json
{
  "document_id": "93907148-3d1c-4d7a-bf09-43ce6d4a22c9",
  "source_type": "payload",
  "source_ref": "pricing-rules",
  "version": 1,
  "status": "ingested",
  "lifecycle_action": "created",
  "content_length": 123,
  "metadata_summary": {
    "domain": "quotes",
    "country": "NO",
    "category": "quotes"
  },
  "last_ingested_at": "2026-03-18T00:00:00Z",
  "last_indexed_at": null,
  "is_index_stale": true
}
```

### Common failure cases

- `400`: invalid metadata JSON or invalid request body
- `415`: wrong content type
- `502`: upstream URL fetch failed

## `GET /documents`

Returns document summaries ordered by newest first.

### Example

```bash
curl http://localhost:8000/documents
```

### Response

```json
[
  {
    "id": "93907148-3d1c-4d7a-bf09-43ce6d4a22c9",
    "source_type": "payload",
    "source_ref": "pricing-rules",
    "version": 1,
    "status": "indexed",
    "metadata_summary": {
      "domain": "quotes",
      "country": "NO",
      "category": "quotes"
    },
    "chunk_count": 3,
    "embedding_count": 3,
    "last_ingested_at": "2026-03-18T00:00:00Z",
    "last_indexed_at": "2026-03-18T00:00:05Z",
    "is_index_stale": false,
    "index_error": null,
    "created_at": "2026-03-18T00:00:00Z"
  }
]
```

### Important fields

- `status`
- `version`
- `chunk_count`
- `embedding_count`
- `is_index_stale`
- `index_error`
- `metadata_summary.category`

## `GET /documents/{document_id}`

Returns one document with preview content.

### Example

```bash
curl http://localhost:8000/documents/93907148-3d1c-4d7a-bf09-43ce6d4a22c9
```

### Additional fields

- `content_type`
- `content_preview`

### Failure

- `404`: document not found

## `DELETE /documents/{document_id}`

Deletes the document and its related chunk, embedding, and pending indexing state.

### Example

```bash
curl -X DELETE http://localhost:8000/documents/93907148-3d1c-4d7a-bf09-43ce6d4a22c9
```

### Response

- HTTP `204 No Content`

## `POST /documents/{document_id}/chunks`

Creates chunks for a document manually.

This is mostly useful for debugging or manual indexing workflows.

### Request body

```json
{
  "strategy": "overlap",
  "chunk_size": 512,
  "overlap_tokens": 64
}
```

### Example

```bash
curl -X POST http://localhost:8000/documents/<document_id>/chunks \
  -H 'Content-Type: application/json' \
  -d '{
    "strategy": "overlap",
    "chunk_size": 512,
    "overlap_tokens": 64
  }'
```

### Failure

- `404`: document not found

## `GET /documents/{document_id}/chunks`

Returns chunk metadata and content for a document.

### Example

```bash
curl http://localhost:8000/documents/<document_id>/chunks
```

### Typical use cases

- inspect chunk boundaries
- debug metadata propagation
- verify chunking strategy output

## `POST /reindex`

Creates reindex jobs and optionally runs them inline.

### Request body

```json
{
  "document_id": null,
  "run_inline": true,
  "strategy": "overlap",
  "chunk_size": 512,
  "overlap_tokens": 64
}
```

### Behavior

- `document_id` present: reindex one document
- `document_id` null: reindex all documents
- `run_inline=true`: API processes the job immediately
- `run_inline=false`: worker processes the job asynchronously

### Example: reindex one document inline

```bash
curl -X POST http://localhost:8000/reindex \
  -H 'Content-Type: application/json' \
  -d '{
    "document_id": "93907148-3d1c-4d7a-bf09-43ce6d4a22c9",
    "run_inline": true,
    "strategy": "overlap",
    "chunk_size": 512,
    "overlap_tokens": 64
  }'
```

### Example: queue all documents for worker processing

```bash
curl -X POST http://localhost:8000/reindex \
  -H 'Content-Type: application/json' \
  -d '{
    "document_id": null,
    "run_inline": false,
    "strategy": "overlap",
    "chunk_size": 512,
    "overlap_tokens": 64
  }'
```

### Response

```json
{
  "jobs": [
    {
      "id": "03321f70-a8a7-4e51-9ed4-188f797f0ff7",
      "document_id": "93907148-3d1c-4d7a-bf09-43ce6d4a22c9",
      "document_version": 1,
      "job_type": "reindex",
      "status": "completed",
      "payload": {
        "strategy": "overlap",
        "chunk_size": 512,
        "overlap_tokens": 64
      },
      "error_message": null,
      "created_at": "2026-03-18T00:00:00Z",
      "started_at": "2026-03-18T00:00:00Z",
      "completed_at": "2026-03-18T00:00:02Z"
    }
  ]
}
```

## `GET /jobs/{job_id}`

Returns one indexing job.

### Example

```bash
curl http://localhost:8000/jobs/03321f70-a8a7-4e51-9ed4-188f797f0ff7
```

### Useful fields

- `status`
- `document_version`
- `error_message`

### Failure

- `404`: job not found

## `POST /query`

Runs retrieval plus grounded generation.

### Request body

```json
{
  "query": "What VAT applies to consulting in Norway?",
  "top_k": 5,
  "score_threshold": 0.2,
  "filters": {
    "country": "NO"
  }
}
```

### Request fields

- `query`: user question
- `top_k`: max number of chunks to return before generation
- `score_threshold`: optional minimum retrieval score
- `filters`: metadata filters

### Filtering rules

Preferred filter keys:

- `category`
- `country`

Compatibility behavior:

- `domain` and `type` are normalized into `category`

### Example: generic query

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What VAT applies to consulting in Norway?",
    "top_k": 5,
    "filters": {
      "country": "NO",
      "category": "quotes"
    }
  }'
```

### Example: catalog query

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Quali attività posso fare ad Alta?",
    "top_k": 5,
    "filters": {
      "category": "travel_catalog"
    }
  }'
```

### Response

```json
{
  "answer": "## Answer\n\n- Norwegian VAT for consulting is 25 percent.",
  "sources": [
    {
      "document": "pricing-rules",
      "chunk": "chunk-uuid",
      "score": 0.74,
      "excerpt": "Norwegian VAT for consulting is 25 percent...",
      "metadata": {
        "country": "NO",
        "domain": "quotes",
        "category": "quotes"
      }
    }
  ],
  "trace": {
    "top_k": 5,
    "threshold": 0.2,
    "retrieval_count": 1,
    "retrieval_mode": "pgvector",
    "embedding_provider": "openai",
    "generation_provider": "openai"
  },
  "machine_output": null
}
```

### Catalog-style response example

```json
{
  "answer": "# HUMAN OUTPUT\n\n## Husky safari\n\n### Overview\nEsperienza artica in slitta trainata da husky.\n\n### Details\n- Location: Tromsø\n- Duration: Non specificato\n- Environment: Outdoor / Neve",
  "sources": [
    {
      "document": "nordikae_catalog_winter_2026_27",
      "chunk": "chunk-uuid",
      "score": 0.36,
      "excerpt": "Husky safari ...",
      "metadata": {
        "type": "travel_catalog",
        "category": "travel_catalog",
        "language": "it"
      }
    }
  ],
  "trace": {
    "top_k": 5,
    "threshold": 0.2,
    "retrieval_count": 3,
    "retrieval_mode": "pgvector",
    "embedding_provider": "openai",
    "generation_provider": "openai"
  },
  "machine_output": {
    "activities": [
      {
        "activity": "Husky safari",
        "location": "Tromsø",
        "duration": null,
        "environment": "Outdoor / Neve",
        "requirements": {
          "age": null,
          "license": null,
          "notes": null
        }
      }
    ]
  }
}
```

### Response notes

- `answer` is Markdown
- visible `answer` content should not expose UUIDs or internal identifiers
- `sources` is the evidence list used for grounding
- `machine_output` is optional and intended for integrations or validation logic

### Common query errors

Example provider timeout:

```json
{
  "detail": "The answer generation request timed out. Try a shorter question or retry shortly."
}
```

Example embedding failure:

```json
{
  "detail": "The embedding provider rate limit was reached. Retry shortly."
}
```

Example internal failure:

```json
{
  "detail": "The query could not be completed. Check the API logs for details."
}
```

## Recommended End-to-End Workflow

### 1. Ingest

```bash
curl -X POST http://localhost:8000/ingest \
  -F 'file=@catalog.pdf' \
  -F 'metadata={"type":"travel_catalog","language":"it"}'
```

### 2. Reindex

```bash
curl -X POST http://localhost:8000/reindex \
  -H 'Content-Type: application/json' \
  -d '{
    "document_id": "<document_id>",
    "run_inline": true,
    "strategy": "overlap",
    "chunk_size": 512,
    "overlap_tokens": 64
  }'
```

### 3. Query

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Quali attività posso fare ad Alta?",
    "filters": {
      "category": "travel_catalog"
    }
  }'
```

### 4. Review

Check:

- `answer` for readable output
- `sources` for grounding
- `machine_output` if you need structured extraction
