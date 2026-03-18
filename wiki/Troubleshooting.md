# Troubleshooting

## API does not start

Check:

```bash
docker compose logs -f api
```

Likely causes:

- database not reachable
- migration failure
- invalid environment variable
- missing `OPENAI_API_KEY` while provider is set to `openai`

## Worker does not process jobs

Check:

```bash
docker compose logs -f worker
curl http://localhost:8000/jobs/<job_id>
```

Common causes:

- worker container not running
- database unavailable
- provider configuration invalid
- job superseded by a newer document version

## Query returns no sources

Check:

1. document was ingested
2. document was reindexed
3. `embedding_count` is greater than zero
4. query filters are not too restrictive
5. score threshold is not too high

Useful endpoint:

```bash
curl http://localhost:8000/documents
```

## Document shows `is_index_stale=true`

This means the content changed or indexing has not completed.

Fix:

```bash
curl -X POST http://localhost:8000/reindex \
  -H 'Content-Type: application/json' \
  -d '{"document_id":"<document_id>","run_inline":true,"strategy":"overlap","chunk_size":512,"overlap_tokens":64}'
```

## OpenAI mode fails

Check:

- `OPENAI_API_KEY` is set
- `EMBEDDING_PROVIDER=openai`
- `GENERATION_PROVIDER=openai`
- outbound internet access is allowed from containers

Verify the health endpoint and logs:

```bash
curl http://localhost:8000/health
docker compose logs -f api
```

## Frontend loads but requests fail

Check:

- API is reachable on `http://localhost:8000`
- `VITE_API_URL` is correct
- CORS allows the frontend origin

Current secure default:

- `http://localhost:3000`
- remote frontend origins must be added explicitly to `CORS_ORIGINS`

## Frontend container works differently from local `npm run dev`

This is expected:

- local development uses the Vite dev server
- Docker deployment serves the built frontend with Nginx on external port `3000`

If you changed frontend code and do not see it in Docker:

```bash
docker compose up -d --build frontend
```

## Migration issues

Run manually:

```bash
cd backend
PYTHONPATH=. ../.venv/bin/alembic -c alembic.ini upgrade head
```

If the DB is badly out of sync:

1. back up the DB first
2. inspect existing tables
3. decide whether to migrate in place or rebuild the environment

## Docker permission denied

If you see Docker socket permission errors:

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

Then retry:

```bash
docker compose up --build
```

## Docker Compose warns about Bake or buildx

If you see:

```text
Docker Compose is configured to build using Bake, but buildx isn't installed
```

install Docker Buildx and verify it is available:

```bash
sudo apt install -y docker-buildx
docker buildx version
```

Then retry:

```bash
docker compose up --build
```

## PostgreSQL data reset

Only do this if you intentionally want a clean database:

```bash
docker compose down -v
docker compose up --build
```

This removes the persisted volume.
