# Project Wiki

This wiki documents the current first-beta Backoffice AI decision support system in this repository.

Use this wiki as the main reference for:

- deployment
- onboarding new developers
- day-to-day usage
- API integration
- operations and maintenance
- troubleshooting

## Wiki Contents

- [Architecture](./Architecture.md)
- [Deployment Guide](./Deployment.md)
- [Developer Onboarding](./Developer-Onboarding.md)
- [Administrator Guide](./Administrator-Guide.md)
- [User Guide](./User-Guide.md)
- [API Reference](./API-Reference.md)
- [Troubleshooting](./Troubleshooting.md)

## Current Scope

The system currently provides:

- document ingestion for `PDF`, `HTML`, `Markdown`, and `JSON`
- token-based chunking
- embeddings with `mock` or `OpenAI` providers
- PostgreSQL + `pgvector` retrieval
- grounded answer generation with citations
- metadata normalization for `category` with `domain` and `type` fallback
- Markdown answer rendering in the frontend
- structured `machine_output` for catalog-oriented formatting flows
- document lifecycle versioning and stale-index detection
- Alembic migrations
- React frontend for beta testing

## Current Non-Goals

These areas are not implemented yet:

- user authentication
- role-based permissions
- Excel workbook ingestion
- OCR for scanned PDFs
- reranking
- streaming query responses
- advanced evaluation dashboards

## Recommended Reading Order

1. [Deployment Guide](./Deployment.md)
2. [Administrator Guide](./Administrator-Guide.md)
3. [User Guide](./User-Guide.md)
4. [Developer Onboarding](./Developer-Onboarding.md)
