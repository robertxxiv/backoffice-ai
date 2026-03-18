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

The beta UI is now organized as separate views:

- landing page
- dashboard
- ingestion
- search
- documents
- jobs
- settings

## 1. Start From the Landing Page

The landing page is the first entry point.

From there you can:

- enter the workspace
- jump directly to search

After entering the workspace, use the sidebar navigation to move between pages.

## 2. Ingest Content

You can ingest:

- text payloads
- uploaded files

Use metadata whenever possible. Good metadata improves filtering and traceability.

Examples:

- `{"country":"NO","domain":"quotes"}`
- `{"type":"travel_catalog","language":"it"}`
- `{"department":"sales","version":"2026-Q1"}`

Metadata behavior:

- the system uses `category` as the main grouping field
- if you provide `domain` or `type`, the backend also derives `category`
- the query UI `Category` dropdown updates automatically from ingested document metadata

Use the `Ingestion` page for uploads and payload ingest.

Use the `Documents` page to manage the indexed corpus.

## 3. Reindex the Document

After a document is ingested, it is not query-ready until indexing runs.

From the UI:

- go to `Documents`
- click `Reindex` for one document
- or click `Reindex All`

After reindexing, the document should show:

- chunks > 0
- embeddings > 0
- status `indexed`

## 4. Ask a Query

Open the `Search` page and enter a natural-language question.

Examples:

- `What VAT applies to consulting in Norway?`
- `What pricing rule applies in winter?`
- `Which document mentions seasonal pricing?`

The main query UI is designed for non-technical users:

- one main question field
- `Category` dropdown
- `Country` dropdown
- optional `Advanced` section for retrieval breadth and raw JSON filters

Examples:

- choose `Category: Travel Catalog`
- choose `Country: NO`
- then ask `Quali attività posso fare ad Alta?`

## 5. Read the Result

Each response includes:

- `answer` rendered as Markdown
- `sources`
- `trace`
- optional structured data panel when available

### What to trust

Use answers as grounded summaries, not as a replacement for source review in critical cases.

Always review:

- the cited sources
- the excerpt text
- the document context

### During query execution

While a query is running, the result area shows a staged loading panel instead of staying blank. This is expected and indicates that retrieval and answer generation are in progress.

## 6. Re-ingesting Updated Content

If the same document source is ingested again:

- unchanged content stays on the same version
- changed content increments the version
- the system marks the document as needing reindex

That means:

- upload updated content
- run reindex again
- then query the new version

## 7. When Results Look Wrong

Check:

1. was the document indexed?
2. does the document metadata match the query filter?
3. did the source content actually contain the answer?
4. was the content updated and not reindexed yet?

If needed, ask an administrator to inspect the document and job status.

## 8. Other Pages

Use the remaining pages like this:

- `Dashboard`: overview and quick links
- `Documents`: corpus management, reindex, delete
- `Jobs`: recent pipeline activity
- `Settings`: read-only runtime and limit information

## 9. Cost Awareness

If the system is configured with real OpenAI providers, usage has a cost.

In practice:

- uploading alone does not cost OpenAI tokens
- reindexing costs embedding tokens
- asking questions costs embedding + generation tokens

For normal small-team use, costs are typically low, but repeated full reindexing and very large query contexts will increase spend.

Ask the administrator if you are unsure whether the system is running in:

- `mock` mode
- `openai` mode
