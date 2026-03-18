# Deployment Guide

This page covers full deployment for local, server, and first beta usage. It is intentionally explicit.

## 1. Deployment Targets

The recommended deployment target for this repository is:

- Docker Compose
- one host
- one PostgreSQL instance
- one API container
- one worker container
- one frontend container

This is sufficient for the current small-team beta phase.

## 2. Prerequisites

Install on the target host:

- Docker Engine
- Docker Compose v2

Verify:

```bash
docker --version
docker compose version
```

Optional but useful:

- `git`
- `curl`
- `jq`

## 3. Clone the Project

```bash
git clone <your-repo-url> backoffice-ai
cd backoffice-ai
```

If you are deploying from an already prepared directory, ensure these files exist:

- `docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `.env.example`

## 4. Prepare Environment Variables

Start from the sample file:

```bash
cp .env.example .env
```

### Minimum local beta settings

`.env`

```bash
POSTGRES_DB=rag_system
POSTGRES_USER=backofficeai
POSTGRES_PASSWORD=change-this-password
DATABASE_URL=postgresql+psycopg://backofficeai:change-this-password@db:5432/rag_system
EMBEDDING_PROVIDER=mock
GENERATION_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
GENERATION_MODEL=gpt-5-mini
TRUSTED_HOSTS=["localhost","127.0.0.1","your-server-ip-or-hostname"]
ENABLE_API_DOCS=false
CORS_ORIGINS=["http://localhost:3000"]
RUN_MIGRATIONS_ON_STARTUP=true
```

### Real OpenAI settings

To use real embeddings and generation:

```bash
EMBEDDING_PROVIDER=openai
GENERATION_PROVIDER=openai
OPENAI_API_KEY=<your-api-key>
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
GENERATION_MODEL=gpt-5-mini
```

Important:

- the API key stays server-side only
- the frontend never needs the OpenAI key
- change `POSTGRES_PASSWORD` before first deployment
- set `TRUSTED_HOSTS` to the exact hostnames or LAN IPs users will use to access the API
- API docs are disabled by default in this hardened setup; enable them only when needed

## 5. PostgreSQL Setup and Configuration

This project supports two PostgreSQL setup patterns:

- a fresh installation using the bundled Docker `db` service
- an existing PostgreSQL installation that you already operate

### Case A: fresh installation with the bundled Docker PostgreSQL service

This is the recommended path for first deployment.

What you need to do:

1. keep the `db` service enabled in `docker-compose.yml`
2. keep `DATABASE_URL` set to:

```bash
DATABASE_URL=postgresql+psycopg://backofficeai:change-this-password@db:5432/rag_system
```

3. start the stack with:

```bash
docker compose up -d --build
```

What happens automatically:

- PostgreSQL starts inside the `db` container
- the `rag_system` database is created by container environment variables
- data is stored in the `pgdata` Docker volume
- the API applies Alembic migrations on startup
- the schema is created or upgraded
- `pgvector` is enabled by migration startup logic when the database supports it

Fresh-install notes:

- you do not need to run `CREATE DATABASE` manually in this mode
- you do not need to install PostgreSQL on the host in this mode
- PostgreSQL is reachable only inside the Docker network by default
- backups still matter because the database volume is persistent
- if you need an admin shell, use:

```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

### Case B: existing PostgreSQL installation

Use this when you already have a PostgreSQL server running outside the Docker `db` container.

Requirements for the existing server:

- PostgreSQL reachable from the API and worker
- the `pgvector` extension installed on that PostgreSQL instance
- one database for this application
- one role/user for this application

Recommended setup steps on the PostgreSQL server:

```sql
CREATE USER rag_user WITH PASSWORD 'change-this-password';
CREATE DATABASE rag_system OWNER rag_user;
\c rag_system
CREATE EXTENSION IF NOT EXISTS vector;
GRANT ALL PRIVILEGES ON DATABASE rag_system TO rag_user;
```

If you use an existing shared role instead of creating `rag_user`, adapt the commands accordingly.

Set the application connection string to the existing server:

```bash
DATABASE_URL=postgresql+psycopg://rag_user:change-this-password@your-db-host:5432/rag_system
```

If SSL is required in your environment, append the needed connection parameters to the URL according to your PostgreSQL policy.

Important behavior with the current `docker-compose.yml`:

- the local `db` container may still start because `api` and `worker` depend on it
- this is acceptable even if unused
- the API and worker will use whatever database is in `DATABASE_URL`
- the bundled `db` service is no longer published on host port `5432` by default

That means an external PostgreSQL deployment works immediately by changing `DATABASE_URL`, even if the bundled `db` service is still present.

If you want a cleaner external-DB deployment later, you can add a compose override that removes the local database service from the runtime path.

### Verifying PostgreSQL configuration

Before starting the application, verify:

1. the database exists
2. the application user can connect
3. `pgvector` is available
4. the API host can reach the database host and port

Useful checks:

```bash
psql "postgresql://rag_user:change-this-password@your-db-host:5432/rag_system" -c '\dx'
psql "postgresql://rag_user:change-this-password@your-db-host:5432/rag_system" -c 'SELECT current_database();'
```

You should see the `vector` extension listed in `\dx`.

### PostgreSQL configuration summary

For this application, the PostgreSQL layer must provide:

- one writable application database
- one application role with create/read/write privileges in that database
- `pgvector`
- reliable disk persistence and backups
- network access from the API and worker

## 6. Review Docker Compose Behavior

Current service responsibilities:

- `api`
  - serves REST endpoints
  - runs Alembic migrations on startup by default
- `worker`
  - processes pending reindex jobs
  - does not run migrations by default
- `db`
  - persists application data
  - includes `pgvector`
- `frontend`
  - serves the React beta UI
  - by default resolves the API on the same host using port `8000`

## 7. Build and Start the Stack

### Start in foreground

```bash
docker compose up --build
```

### Start in background

```bash
docker compose up -d --build
```

### What happens on startup

1. PostgreSQL starts.
2. The API waits for the database healthcheck.
3. The API runs database migrations to `head`.
4. The API exposes port `8000`.
5. The worker starts and polls for indexing jobs.
6. The frontend starts on port `3000`.

## 8. Verify the Deployment

### Check containers

```bash
docker compose ps
```

Expected services:

- `api`
- `worker`
- `db`
- `frontend`

### Check API health

```bash
curl http://localhost:8000/health
```

Expected response structure:

```json
{
  "status": "ok",
  "database": "ok",
  "embedding_provider": "mock",
  "generation_provider": "mock"
}
```

### Open the UI

Visit:

- `http://localhost:3000`

## 9. Remote Access

You can access the system remotely, but you need to distinguish between:

- access from another machine on the same private network
- access from the public internet

Important current limitation:

- this project does **not** implement authentication yet
- do **not** expose the API or frontend directly to the public internet without an access control layer in front of it

### Case A: remote access on the same private network

If the Docker host is reachable on your LAN or VPN, the simplest setup is:

1. start the stack normally
2. identify the server IP address
3. open the required firewall ports
4. access the frontend and API from another machine using the server IP

### Step 1: start the stack

```bash
docker compose up -d --build
```

### Step 2: find the server IP

On the server:

```bash
hostname -I
```

Example result:

```text
192.168.1.50
```

### Step 3: confirm the exposed ports

Current ports from `docker-compose.yml`:

- frontend: `3000`
- API: `8000`
- PostgreSQL: `5432`

For normal remote usage, users usually need only:

- `3000` for the frontend
- optionally `8000` if you want direct API access from another machine

### Step 4: open firewall rules if needed

Example with `ufw`:

```bash
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp
```

Do **not** open `5432` externally unless you intentionally need remote PostgreSQL access.

### Step 5: access from another machine

Frontend:

```text
http://<server-ip>:3000
```

API health:

```text
http://<server-ip>:8000/health
```

Example:

- frontend: `http://192.168.1.50:3000`
- API: `http://192.168.1.50:8000/health`

Frontend behavior note:

- the frontend now derives the API base URL from the browser hostname by default
- if a user opens `http://192.168.1.50:3000`, the UI will call `http://192.168.1.50:8000`
- this avoids the common remote-access failure where the browser tries to call its own `localhost:8000`
- the backend CORS policy accepts frontend origins on port `3000` by default, which covers typical LAN/VPN access by IP or hostname

### Case B: remote access from the public internet

This is technically possible, but in the current project state it is **not recommended** to expose the stack directly because there is no built-in auth yet.

If you must allow remote internet access before auth is implemented, put a protective layer in front of the app.

Recommended minimum options:

- VPN access only
- reverse proxy with HTTPS and IP allowlist
- reverse proxy with HTTPS and external authentication

Preferred short-term approach:

- keep the server on a private network
- connect through VPN
- access the app using the private server IP and exposed ports

### Safer internet-facing pattern

Use a reverse proxy such as Nginx, Caddy, or Traefik in front of:

- frontend on port `3000`
- API on port `8000`

The reverse proxy should provide:

- HTTPS/TLS
- hostname-based routing
- request size limits for uploads
- optional IP allowlisting
- optional external auth layer

If you later host the frontend and API on different origins, set `VITE_API_URL` explicitly during frontend build.
If you use a different frontend host or port, also adjust `CORS_ORIGINS` and `CORS_ORIGIN_REGEX`.

### Example remote access process for a small team

For a 3-user company, the practical recommendation is:

1. deploy the stack on one Linux host
2. keep Docker Compose
3. do not expose PostgreSQL externally
4. allow frontend and API only on the private network or VPN
5. if offsite access is needed, use VPN first
6. add application auth before exposing the system publicly

### Remote access verification checklist

From a remote machine:

1. open `http://<server-ip>:3000`
2. verify the UI loads
3. open `http://<server-ip>:8000/health`
4. ingest a small payload
5. reindex it
6. run a query

If remote users cannot connect, check:

- the host IP address
- firewall rules
- cloud security group rules if hosted in the cloud
- Docker container status
- whether the server is reachable over VPN or LAN

## 10. First-Time Beta Smoke Test

### Step 1: ingest a payload

```bash
curl -X POST http://localhost:8000/ingest \
  -H 'Content-Type: application/json' \
  -d '{
    "payload":"Norwegian VAT for consulting is 25 percent. Winter pricing applies from December to February.",
    "metadata":{"country":"NO","domain":"quotes"},
    "source_name":"pricing-rules"
  }'
```

Save the returned `document_id`.

### Step 2: reindex the document

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

### Step 3: run a query

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query":"What VAT applies to consulting in Norway?",
    "filters":{"country":"NO"}
  }'
```

### Step 4: confirm source traceability

The response should include:

- `answer`
- `sources`
- `trace`

This confirms end-to-end ingest, chunking, embedding, retrieval, and generation.

## 11. Deployment Modes

### Mock mode

Use when:

- testing deployment wiring
- onboarding new developers
- running local demos without API cost

Limitations:

- answer quality is not representative of real OpenAI output
- embeddings are deterministic mock vectors

### OpenAI mode

Use when:

- beta users need realistic answer quality
- you are validating actual retrieval and generation behavior

Requirements:

- valid `OPENAI_API_KEY`
- internet access from the API and worker containers

## 12. Database and Persistence

Persistent database data is stored in the Docker volume:

- `pgdata`

Inspect:

```bash
docker volume ls
docker volume inspect backoffice-ai_pgdata
```

## 13. Backup Procedure

Do not skip backups if the system is used daily.

### Create a SQL dump

```bash
docker compose exec db pg_dump -U postgres -d rag_system > rag_system_backup.sql
```

### Create a timestamped backup

```bash
mkdir -p backups
docker compose exec db pg_dump -U postgres -d rag_system > backups/rag_system_$(date +%F_%H-%M-%S).sql
```

Recommended:

- back up before upgrading
- back up before manual DB work
- keep at least several recent dumps

## 14. Restore Procedure

### Stop application writes

```bash
docker compose stop api worker frontend
```

### Restore into PostgreSQL

```bash
cat rag_system_backup.sql | docker compose exec -T db psql -U postgres -d rag_system
```

### Restart services

```bash
docker compose start api worker frontend
```

If the database is being restored into a fresh environment, start `db` first, restore, then start the application services.

## 15. Upgrade Procedure

When deploying a new version:

1. back up the database
2. pull the new code
3. review `.env`
4. rebuild containers
5. bring the stack up
6. verify health and smoke test

Commands:

```bash
git pull
docker compose up -d --build
curl http://localhost:8000/health
```

The API will run Alembic migrations automatically on startup when `RUN_MIGRATIONS_ON_STARTUP=true`.

## 16. Stop and Restart

### Stop without deleting data

```bash
docker compose stop
```

### Start again

```bash
docker compose start
```

### Stop and remove containers, keep data volume

```bash
docker compose down
```

### Stop and remove everything including DB data

```bash
docker compose down -v
```

Use `-v` only if you intentionally want to wipe the database.

## 17. Logs

### Follow all logs

```bash
docker compose logs -f
```

### Follow API logs only

```bash
docker compose logs -f api
```

### Follow worker logs only

```bash
docker compose logs -f worker
```

### Follow database logs only

```bash
docker compose logs -f db
```

## 18. Production Notes for a Small Team

For a 3-user company deployment, the current recommended approach is:

- run on one VM or one dedicated Linux host
- keep Docker Compose
- use PostgreSQL volume backups
- use real OpenAI providers
- keep the frontend behind a reverse proxy if exposing externally

Not yet implemented:

- authentication
- authorization
- HTTPS termination inside this repo

If exposed outside a private network, add a reverse proxy and TLS in front of `frontend` and `api`.
