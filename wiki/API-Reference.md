# API Reference

Base URL:

- `http://localhost:8000`

All endpoints use JSON unless otherwise noted.

## `GET /health`

Checks API and database readiness.

### Response

```json
{
  "status": "ok",
  "database": "ok",
  "embedding_provider": "mock",
  "generation_provider": "mock"
}
```

## `POST /ingest`

Ingests a document by multipart upload or JSON body.

### Multipart upload

Fields:

- `file`
- optional `metadata` as JSON string

Example:

```bash
curl -X POST http://localhost:8000/ingest \
  -F 'file=@sample.md' \
  -F 'metadata={"country":"NO"}'
```

### JSON payload

Exactly one of:

- `url`
- `payload`

Example:

```json
{
  "payload": "Norwegian VAT is 25 percent.",
  "metadata": {
    "country": "NO"
  },
  "source_name": "pricing-rules"
}
```

### Response

```json
{
  "document_id": "uuid",
  "source_type": "payload",
  "source_ref": "pricing-rules",
  "version": 1,
  "status": "ingested",
  "lifecycle_action": "created",
  "content_length": 123,
  "metadata_summary": {
    "country": "NO",
    "category": "quotes"
  },
  "last_ingested_at": "2026-03-17T00:00:00Z",
  "last_indexed_at": null,
  "is_index_stale": true
}
```

Metadata notes:

- `category` is the canonical filter/display field
- if you upload `domain` or `type`, the backend also derives `category`
- original metadata keys are preserved

## `GET /documents`

Returns document summaries.

Important fields:

- `version`
- `status`
- `chunk_count`
- `embedding_count`
- `is_index_stale`
- `index_error`

## `GET /documents/{document_id}`

Returns detailed information for one document.

Adds:

- `content_type`
- `content_preview`

## `DELETE /documents/{document_id}`

Deletes the document and related indexing state.

### Response

- status `204`

## `POST /documents/{document_id}/chunks`

Creates chunks for a document manually.

### Request

```json
{
  "strategy": "overlap",
  "chunk_size": 512,
  "overlap_tokens": 64
}
```

## `GET /documents/{document_id}/chunks`

Returns chunk metadata and chunk content for a document.

## `POST /reindex`

Creates reindex jobs.

### Request

```json
{
  "document_id": "uuid-or-null",
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

## `GET /jobs/{job_id}`

Returns one job record.

Useful fields:

- `status`
- `document_version`
- `error_message`

## `POST /query`

Runs the retrieval and generation pipeline.

### Request

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

Filtering notes:

- use `category` as the preferred content grouping filter
- `country` remains supported directly
- `domain` and `type` metadata are normalized into `category` for compatibility

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

Response notes:

- `answer` is Markdown intended for direct human display
- `sources` remains the citation/evidence list
- `machine_output` is optional structured JSON for formatting-oriented workflows such as travel/activity catalog extraction
- visible `answer` content should not expose UUIDs or internal identifiers even when source chunks use them internally
