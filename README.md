# Enterprise AI Scrum & Project Management Platform

Status: Phase 1 repo skeleton — Next.js frontend, FastAPI backend, Postgres,
Redis, and Celery are wired up and run end-to-end. No product features yet.

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

- Web: http://localhost:3000 (or `$WEB_PORT`)
- API: http://localhost:8000 (or `$API_PORT`) — health check at `/healthz`, DB check at `/api/v1/health`

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
uvicorn src.main:app --reload
```

Run the API test suite: `pytest -q`. Lint/typecheck: `ruff check .` and `mypy src`.
