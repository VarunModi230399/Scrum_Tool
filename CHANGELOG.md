# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Initial PRD (`docs/PRD.md`) — vision, personas, hierarchy philosophy, and
  a 7-phase build plan starting with a Phase 1 foundation scope.
- Initial architecture doc (`docs/ARCHITECTURE.md`) — tech stack, Clean
  Architecture/DDD module layout, system diagram, and the modeling decision
  for the unlimited-nesting work item hierarchy (single polymorphic table +
  materialized path).
- Initial database schema (`docs/DATABASE_SCHEMA.md`) for Phase 1: identity,
  workspaces/projects, unified `work_items` hierarchy, requirements module
  with M:N traceability, shared comments/attachments, audit log.
- Initial API contracts (`docs/API_CONTRACTS.md`) for Phase 1: auth,
  organizations/workspaces, projects, work items, requirements, labels/tags/
  custom fields, WebSocket channels.
- Repo skeleton, end-to-end runnable:
  - `apps/web`: Next.js 16 + TypeScript + Tailwind v4 + shadcn/ui (base-ui),
    React Query, next-themes (dark mode first-class), Framer Motion. Theme
    tokens extended with success/warning/info/ai accent colors per the
    design system; primary action color set to blue. Production Docker image
    via `output: "standalone"`.
  - `apps/api`: FastAPI on the Clean Architecture/DDD module layout from
    ARCHITECTURE.md (`modules/{identity,projects,requirements}` each with
    `domain/application/infrastructure/api`, plus `platform/` and
    `shared_kernel/`). Async SQLAlchemy + Alembic wired to `Base.metadata`,
    Celery app configured against Redis, structured logging, CORS, a
    shared `AppError` hierarchy mapped to the API's error envelope, and
    `/healthz` + `/api/v1/health` (DB connectivity check) endpoints.
  - `docker-compose.yml`: postgres, redis, api, worker (Celery), web —
    verified to build and run together, with host ports overridable via
    `POSTGRES_PORT`/`REDIS_PORT`/`API_PORT`/`WEB_PORT` env vars to avoid
    clashing with other local projects.
  - `.github/workflows/ci.yml`: lint + typecheck + build for web, lint +
    typecheck + test for api (against real Postgres/Redis service
    containers).
- Identity module (Phase 1, first vertical slice): register/login/refresh/
  logout/me, Google + Microsoft OAuth (authorization-code flow, gated behind
  configured client credentials), organizations, workspaces, and
  role-gated workspace membership management.
  - `docs/DATABASE_SCHEMA.md`: added `refresh_tokens` table for server-side
    revocation (logout, rotation-on-reuse breach detection).
  - Domain/application/infrastructure/api layers under
    `apps/api/src/modules/identity/`: JWT access+refresh tokens (rotation on
    refresh; reusing a spent refresh token 401s), bcrypt password hashing
    (used directly, not via the unmaintained `passlib` — passlib 1.7.4 is
    incompatible with modern `bcrypt`'s stricter 72-byte input validation),
    workspace RBAC (`admin/product_owner/scrum_master/developer/viewer`)
    enforced via a `require_workspace_role` FastAPI dependency.
  - Registering a user auto-creates a personal organization + workspace
    (creator as admin) so individuals/startups can start working with zero
    setup, per the PRD's target personas.
  - First Alembic migration (`identity module: organizations, users, oauth
    identities, workspaces, memberships, refresh tokens`); `docker-compose.yml`
    gained a one-shot `migrate` service that both `api` and `worker` depend
    on (`service_completed_successfully`) so a fresh `docker compose up`
    applies migrations automatically.
  - 15 integration tests (register/login/refresh-rotation/logout/me,
    organization+workspace CRUD, membership add/update-role/remove,
    authorization checks) against a real Postgres, all passing; CI now also
    runs `alembic upgrade head` + `alembic check` to catch model/migration
    drift.
