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
- Projects & Work Items module (Phase 1, second vertical slice): the core
  hierarchy — Epic → Feature → Story → Task → Subtask → Checklist Item —
  with unlimited nesting, dependencies, and automatic progress rollup.
  - Modeled as a single `work_items` table with a `type` discriminator and a
    materialized `path` column (dot-delimited ancestor UUIDs), exactly as
    specified in ARCHITECTURE.md §7 — `LIKE 'prefix.%'` gives O(1) descendant
    lookups, splitting `path` gives ancestors, both backed by a
    `text_pattern_ops` index.
  - Full CRUD, `children`/`ancestors` lookups, `move` (reparent — rejects
    moving into self, into one's own descendant, or across projects, and
    updates the whole subtree's `path`/`depth` in one pass), and
    `dependencies` (`blocks`/`relates_to`; rejects self-deps, duplicates, and
    the direct reverse edge — full transitive cycle detection deferred to
    the Phase 2 Dependency Graph view).
  - `ProgressRollupService` (`modules/projects/application/progress.py`):
    weighted-average rollup by `story_points` (equal-weight fallback), leaf
    progress derived from status, `progress_override` cascades its value
    upward without being overwritten. Implemented **synchronously** rather
    than the async Celery cascade ARCHITECTURE.md originally sketched —
    simpler, directly testable, and tree depth doesn't yet justify the async
    complexity; see ARCHITECTURE.md §8 for the reasoning and the revisit
    condition.
  - Deleting a work item cascades to its entire subtree (deleting an Epic
    deletes its Stories/Tasks) rather than orphaning children or blocking on
    the FK.
  - Projects module (`modules/projects/`): project CRUD scoped to a
    workspace, admin/product-owner-gated rename/archive. Cross-module
    workspace-RBAC coupling is called out and justified in ARCHITECTURE.md §3.
  - Second Alembic migration (`projects module: projects, work_items,
    work_item_dependencies`).
  - 28 total integration tests now passing (13 new: hierarchy, move/cycle
    rejection, cross-project rejection, dependency lifecycle, and four
    progress-rollup scenarios including the override-cascade case), verified
    live end-to-end via `docker compose` (status→done on a story correctly
    rolled its parent Epic to 100%).
  - **Deferred** (documented in API_CONTRACTS.md §3–4, need shared
    polymorphic infra not yet built): milestones, comments, attachments,
    labels/tags, custom fields, time logs, and board-position ordering on
    move.
- Collaboration module: shared comments + attachments, usable by any entity
  type (`work_item` now, `requirement` later) via a polymorphic
  `entity_type`/`entity_id` pair, matching DATABASE_SCHEMA.md §5. Deliberately
  has no API routes of its own — the owning module (projects, for now) mounts
  `/work-items/{id}/comments` and `/work-items/{id}/attachments` and calls
  into collaboration's use cases/repos directly.
  - Attachments use local-disk storage (`UPLOAD_DIR`, served via a `/uploads`
    static mount) with a 25MB default limit and randomly-generated stored
    filenames (never the client-supplied name, to avoid path traversal).
  - `GET /api/v1/me/workspaces` (identity module): lists every workspace the
    current user belongs to across all organizations — the endpoint the
    frontend uses to bootstrap after login, since nothing else exposes "all
    my workspaces."
  - Third Alembic migration (`collaboration module: comments, attachments`).
  - 5 new integration tests (comment/attachment lifecycle, empty-comment
    rejection, membership-gated access); 34 total, all passing.
- **First working frontend** (`apps/web`): register/login, a workspace
  dashboard with project creation, and a per-project Kanban board (To Do →
  In Progress → In Review → Blocked → Done) with work-item creation,
  quick status changes, a detail sheet (status/priority/progress/comments),
  and delete. JWT stored client-side with automatic refresh-and-retry on 401.
  Verified with a scripted Playwright run through the entire flow
  (register → create project → create task → mark done → comment → see the
  board and progress bar update) against the dockerized stack, zero console
  errors.
  - Three real bugs were found and fixed via that end-to-end pass (backend
    unit/integration tests alone hadn't caught them — nothing had exercised
    "project progress after a real user action, seen through the UI" before):
    1. **Project progress never rolled up.** `ProgressRollupService` cascaded
       through the work-item tree but never touched the owning `Project` row.
       Fixed by extending it to recompute the project's progress (weighted
       average of *root* work items) once the cascade reaches the top; added
       a regression test (`test_project_progress_rolls_up_from_root_work_items`)
       covering both the "new root item" and "status change" trigger paths,
       since creating a root item previously didn't trigger recompute either.
    2. **`NEXT_PUBLIC_API_URL` was baked in at the wrong time.** Next.js
       inlines `NEXT_PUBLIC_*` vars into the client bundle at *build* time;
       the Dockerfile/compose only set it as a container *runtime* env var,
       so the browser always called the hardcoded fallback regardless of
       configuration. Fixed by accepting it as a Docker build `ARG` and
       passing it via `docker-compose.yml`'s `build.args`.
    3. **Frontend cache staleness.** `useUpdateWorkItem`/`useCreateWorkItem`/
       `useDeleteWorkItem` invalidated the work-items list but not the
       project query, so the project's progress bar in the UI went stale
       after any work-item change even though the backend value was correct.
  - `docker-compose.yml`: `CORS_ORIGINS`/`API_BASE_URL`/`FRONTEND_URL` for the
    `api` service are now derived from the same `WEB_PORT`/`API_PORT` vars as
    the port mappings, so remapping ports (e.g. to dodge a local collision)
    no longer requires separately hand-editing `apps/api/.env` to match —
    this exact mismatch caused a CORS failure during verification.
  - README gained a warning about a footgun hit during verification: the
    test suite's `Base.metadata.drop_all()` teardown will wipe the schema
    out from under a `docker compose` stack if both point at the same
    Postgres instance.
