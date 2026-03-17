# User Guide

## Purpose

This page explains how normal users should use the system.

## What the System Does

The system lets you:

- upload or ingest documents
- index them for semantic search
- ask grounded questions
- inspect the sources behind answers

## Frontend Workflow

Open:

- `http://localhost:3000`

The beta UI has four main areas:

- ingest
- indexed documents
- query
- jobs

## 1. Ingest Content

You can ingest:

- text payloads
- uploaded files

Use metadata whenever possible. Good metadata improves filtering and traceability.

Examples:

- `{"country":"NO","domain":"quotes"}`
- `{"department":"sales","version":"2026-Q1"}`

## 2. Reindex the Document

After a document is ingested, it is not query-ready until indexing runs.

From the UI:

- click `Reindex` for one document
- or click `Reindex All`

After reindexing, the document should show:

- chunks > 0
- embeddings > 0
- status `indexed`

## 3. Ask a Query

Enter a natural-language question in the query box.

Examples:

- `What VAT applies to consulting in Norway?`
- `What pricing rule applies in winter?`
- `Which document mentions seasonal pricing?`

Optional filter example:

```json
{"country":"NO"}
```

## 4. Read the Result

Each response includes:

- `answer`
- `sources`
- `trace`

### What to trust

Use answers as grounded summaries, not as a replacement for source review in critical cases.

Always review:

- the cited sources
- the excerpt text
- the document context

## 5. Re-ingesting Updated Content

If the same document source is ingested again:

- unchanged content stays on the same version
- changed content increments the version
- the system marks the document as needing reindex

That means:

- upload updated content
- run reindex again
- then query the new version

## 6. When Results Look Wrong

Check:

1. was the document indexed?
2. does the document metadata match the query filter?
3. did the source content actually contain the answer?
4. was the content updated and not reindexed yet?

If needed, ask an administrator to inspect the document and job status.

## 7. Cost Awareness

If the system is configured with real OpenAI providers, usage has a cost.

In practice:

- uploading alone does not cost OpenAI tokens
- reindexing costs embedding tokens
- asking questions costs embedding + generation tokens

For normal small-team use, costs are typically low, but repeated full reindexing and very large query contexts will increase spend.

Ask the administrator if you are unsure whether the system is running in:

- `mock` mode
- `openai` mode
