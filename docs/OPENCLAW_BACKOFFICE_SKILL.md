# OpenClaw Skill: Backoffice.AI RAG Client

Use this skill when OpenClaw must store content in Backoffice.AI or query indexed company knowledge.

## Purpose

This skill gives OpenClaw a strict, grounded way to:

- ingest raw text, structured payloads, URLs, or uploaded files into Backoffice.AI
- trigger indexing so new content becomes searchable
- query only the indexed corpus
- return cited answers and optional structured extraction output

## Base URL

Set the Backoffice.AI API base URL before using this skill.

Example:

- `http://localhost:8000`
- `http://172.16.5.48:8000`

## Rules

- Treat Backoffice.AI as the source of truth for indexed knowledge.
- Do not assume a document is searchable immediately after ingest.
- After ingest, reindex the document before querying it.
- Use metadata whenever possible so retrieval can be filtered later.
- If Backoffice.AI returns that context is insufficient, stop. Do not continue with external search unless a separate tool explicitly authorizes that behavior.
- Expect JSON in and JSON out.
- This API currently has no built-in auth. Use it only on a trusted internal network.

## Supported Workflows

### 1. Health check

Use to verify the API is reachable before ingest or query.

Request:

```http
GET /health
```

Success response:

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

### 2. Ingest text or structured payload

Use when OpenClaw already has the content in memory.

Request:

```http
POST /ingest
Content-Type: application/json
```

Body:

```json
{
  "payload": "Norwegian VAT for consulting is 25 percent.",
  "metadata": {
    "category": "agent_notes",
    "source": "openclaw",
    "country": "NO"
  },
  "source_name": "openclaw-note-001"
}
```

Important:

- `payload` can be a string, object, or array
- `metadata.category` is the preferred grouping field
- `domain` or `type` are also accepted, and Backoffice.AI derives `category`

### 3. Ingest a URL

Use only for allowed public URLs.

Request:

```http
POST /ingest
Content-Type: application/json
```

Body:

```json
{
  "url": "https://example.com/pricing-page",
  "metadata": {
    "category": "pricing_page",
    "source": "openclaw"
  }
}
```

Important:

- private-network and unsafe URLs may be blocked by SSRF protections
- do not use URL ingest for internal-only hosts unless the backend has been configured to allow them

### 4. Reindex a document

Use after every successful ingest if the document must become searchable immediately.

Request:

```http
POST /reindex
Content-Type: application/json
```

Body:

```json
{
  "document_id": "93907148-3d1c-4d7a-bf09-43ce6d4a22c9",
  "run_inline": true,
  "strategy": "overlap",
  "chunk_size": 512,
  "overlap_tokens": 64
}
```

Success response:

```json
{
  "jobs": [
    {
      "id": "job-id",
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
      "completed_at": "2026-03-18T00:00:03Z"
    }
  ]
}
```

### 5. Query indexed knowledge

Use only after the target content has been indexed.

Request:

```http
POST /query
Content-Type: application/json
```

Body:

```json
{
  "query": "What VAT applies to consulting in Norway?",
  "top_k": 5,
  "filters": {
    "category": "agent_notes",
    "country": "NO"
  }
}
```

Success response:

```json
{
  "answer": "## Answer\n\nThe indexed material states that Norwegian VAT for consulting is 25 percent.",
  "sources": [
    {
      "document": "openclaw-note-001",
      "chunk": "chunk-id",
      "score": 0.94,
      "excerpt": "Norwegian VAT for consulting is 25 percent.",
      "metadata": {
        "category": "agent_notes",
        "source": "openclaw",
        "country": "NO"
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

## Required Behaviors

### Ingest-and-query sequence

When storing new knowledge:

1. call `POST /ingest`
2. read `document_id`
3. call `POST /reindex` with that `document_id`
4. only query after indexing completes

### Metadata discipline

Whenever possible, set:

- `category`
- `source`
- `country`
- `language`

This makes later retrieval more controllable.

### Out-of-context behavior

If Backoffice.AI says the indexed context is insufficient:

- return that grounded answer
- do not offer web search
- do not blend in outside knowledge

## Error Handling

Typical error shape:

```json
{
  "detail": "Human-readable error message"
}
```

Important statuses:

- `400`: invalid request or invalid metadata JSON
- `404`: document or job not found
- `413`: payload or upload too large
- `415`: unsupported content type
- `502`: upstream provider or URL fetch failure

## Recommended OpenClaw Methods

Expose these actions inside OpenClaw:

- `backoffice_health()`
- `backoffice_ingest_payload(payload, metadata, source_name)`
- `backoffice_ingest_url(url, metadata)`
- `backoffice_reindex(document_id)`
- `backoffice_query(question, filters, top_k=5)`

## Minimal Usage Pattern

### Store agent memory or extracted notes

- ingest as `payload`
- set `metadata.source = "openclaw"`
- set a useful `category`
- reindex immediately

### Search company knowledge

- call `POST /query`
- pass metadata filters when the search should stay within one corpus
- trust `sources` and `machine_output`, not only the natural-language answer

## Constraints

- This skill does not authenticate yet because Backoffice.AI currently exposes no auth layer.
- This skill assumes Backoffice.AI is reachable on the network.
- This skill does not handle file multipart uploads directly unless OpenClaw supports file upload actions.
