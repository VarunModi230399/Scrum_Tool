# Enterprise AI Scrum & Project Management Platform

Status: Phase 1 — repo skeleton, identity (auth, orgs, workspaces), and the
Projects/Work Items hierarchy (Epic→...→Checklist, dependencies, automatic
progress rollup) are built. Next.js frontend, FastAPI backend, Postgres,
Redis, and Celery run end-to-end; migrations apply automatically.

Start here:
- [`docs/PRD.md`](docs/PRD.md) — vision, personas, phased roadmap
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — tech stack, module layout, key modeling decisions
- [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) — Phase 1 schema
- [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md) — Phase 1 REST/WebSocket contracts
- [`CHANGELOG.md`](CHANGELOG.md) — running log of what changed and why

## Project layout

```
apps/
  web/     Next.js + TypeScript + Tailwind + shadcn/ui frontend
  api/     FastAPI backend (Clean Architecture / DDD module layout)
docs/      PRD, architecture, database schema, API contracts
```

## Running everything with Docker Compose (recommended)

```bash
cp .env.example .env               # only needed if the default ports (5432/6379/8000/3000) collide locally
cp apps/api/.env.example apps/api/.env
docker compose up -d --build
```

This also runs a one-shot `migrate` service (`alembic upgrade head`) before
`api`/`worker` start, so the database schema is always current.

- Web: http://localhost:3000 (or `$WEB_PORT`)
- API: http://localhost:8000 (or `$API_PORT`) — health check at `/healthz`, DB check at `/api/v1/health`

Try the identity API:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"a-strong-password","full_name":"Your Name"}'
# -> { "data": { "user": {...}, "access_token": "...", "refresh_token": "..." } }

curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <access_token>"
```
Registering also creates a personal organization + workspace with you as admin.

Google/Microsoft login requires `GOOGLE_OAUTH_CLIENT_ID`/`_SECRET` or
`MICROSOFT_OAUTH_CLIENT_ID`/`_SECRET` in `apps/api/.env` (unset by default —
those endpoints 422 until configured with real OAuth app credentials).

## Running services individually

**Web** (`apps/web`):
```bash
npm install
npm run dev
```

**API** (`apps/api`), with Postgres/Redis available (e.g. via `docker compose up postgres redis`):
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn src.main:app --reload
```

Run the API test suite: `pytest -q` (spins up/tears down its own tables on
whatever `DATABASE_URL` points to — point it at a real Postgres, e.g. via
`docker compose up -d postgres`). Lint/typecheck: `ruff check .` and `mypy src`.
