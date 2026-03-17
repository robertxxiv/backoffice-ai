# Developer Onboarding

## Goal

This page is for engineers working on the codebase.

## Prerequisites

Install:

- Python 3.12+
- Node 20+
- npm
- Docker
- Docker Compose

Verify:

```bash
python3 --version
npm --version
docker --version
docker compose version
```

## Repository Structure

```text
/backend
  /alembic
  /app
    /api
    /chunking
    /core
    /db
    /embeddings
    /generation
    /indexing
    /ingestion
    /retrieval
  /tests
/frontend
/wiki
```

## Local Setup

### Backend

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
```

### Frontend

```bash
cd frontend
npm install
cd ..
```

## Running Locally

### Backend only with SQLite

```bash
. .venv/bin/activate
export DATABASE_URL=sqlite+pysqlite:///rag-system.db
cd backend
PYTHONPATH=. uvicorn app.main:app --reload
```

### Frontend only

```bash
cd frontend
npm run dev
```

### Full stack with Docker

```bash
docker compose up --build
```

## Test Commands

### Backend tests

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m unittest \
  tests.test_ingestion \
  tests.test_chunking \
  tests.test_query \
  tests.test_retrieval \
  tests.test_lifecycle
```

### Frontend build

```bash
cd frontend
npm run build
```

## Migrations

### Apply migrations manually

```bash
cd backend
PYTHONPATH=. ../.venv/bin/alembic -c alembic.ini upgrade head
```

### Create a new migration

This repo does not yet include an automated migration-generation workflow. For now:

1. update SQLAlchemy models
2. add a new file under `backend/alembic/versions`
3. implement `upgrade()` and `downgrade()`
4. test against SQLite and PostgreSQL

## Development Workflow

Recommended sequence for changes:

1. update or add tests
2. change backend or frontend code
3. run local tests
4. run frontend build
5. validate Docker Compose config

## Key Design Rules

- keep modules independently testable
- prefer environment variables over hardcoded config
- keep functions small
- do not put provider-specific logic directly into routes
- preserve source-based document identity
- if a change affects the schema, add a migration

## Current Development Caveats

- auth is not implemented yet
- SQLite is only a fallback for local dev and tests
- production retrieval quality should be evaluated in PostgreSQL mode with real embeddings
