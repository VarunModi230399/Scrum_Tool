# API Contracts — v1

**Status:** Living document. FastAPI's generated OpenAPI schema is the
executable source of truth once code exists; this doc is the design-time
contract that precedes it and must stay in sync.

Base path: `/api/v1`
Auth: `Authorization: Bearer <JWT>` unless noted. All list endpoints support
`?page=&page_size=` cursor-free pagination for Phase 1 (cursor pagination is
a Phase 3 upgrade once dataset sizes justify it — not built speculatively).

---

## 1. Auth — implemented

```
POST   /api/v1/auth/register              { email, password, full_name }
                                           -> { user, access_token, refresh_token }
                                           registering also creates a personal organization
                                           + workspace with the caller as admin (see §2)
POST   /api/v1/auth/login                 { email, password } -> { user, access_token, refresh_token }
POST   /api/v1/auth/refresh               { refresh_token } -> { access_token, refresh_token }
                                           rotates the refresh token: the presented one is
                                           revoked, reuse returns 401 (breach detection)
POST   /api/v1/auth/logout                { refresh_token } -> 204, revokes it
GET    /api/v1/auth/oauth/{provider}/start    provider: google | microsoft -> 302 redirect
GET    /api/v1/auth/oauth/{provider}/callback -> 302 redirect to
                                           `{FRONTEND_URL}/auth/callback#access_token=...&refresh_token=...`
                                           (tokens in the URL fragment, never sent to the server/logs)
GET    /api/v1/auth/me                    -> current user profile
```

OAuth requires `GOOGLE_OAUTH_CLIENT_ID`/`_SECRET` or `MICROSOFT_OAUTH_CLIENT_ID`/`_SECRET`
configured server-side; unconfigured providers return `VALIDATION_ERROR`.

## 2. Organizations & Workspaces — implemented

```
GET    /api/v1/organizations/{org_id}                      requires membership in one of its workspaces
POST   /api/v1/organizations                { name }
GET    /api/v1/organizations/{org_id}/workspaces            only workspaces the caller is a member of
POST   /api/v1/organizations/{org_id}/workspaces   { name }  creator becomes admin
GET    /api/v1/workspaces/{workspace_id}                     requires membership (any role)
PATCH  /api/v1/workspaces/{workspace_id}     { name }         admin only
GET    /api/v1/workspaces/{workspace_id}/members              requires membership (any role)
POST   /api/v1/workspaces/{workspace_id}/members    { user_id, role }   admin only
PATCH  /api/v1/workspaces/{workspace_id}/members/{user_id}   { role }   admin only
DELETE /api/v1/workspaces/{workspace_id}/members/{user_id}    admin only; cannot remove self
```

## 3. Projects — implemented (milestones deferred)

```
GET    /api/v1/workspaces/{workspace_id}/projects            any workspace member
POST   /api/v1/workspaces/{workspace_id}/projects   { key, name, description? }   any member; key is
                                                     upper-cased and must be unique within the workspace
GET    /api/v1/projects/{project_id}                          any workspace member
PATCH  /api/v1/projects/{project_id}   { name?, description?, status? }   admin/product_owner only
DELETE /api/v1/projects/{project_id}                (soft delete -> status=archived)   admin/product_owner only
```

Deferred: `portfolio_id` on create, and the `/milestones` sub-resource
entirely (`milestone_id` exists as a nullable, unused column reservation on
`work_items` — see DATABASE_SCHEMA.md — but there's no Milestone entity yet).

## 4. Work Items — implemented (see deferrals below)

```
GET    /api/v1/projects/{project_id}/work-items
  query: ?type=&status=&owner_id=&parent_id=          any workspace member
POST   /api/v1/projects/{project_id}/work-items
  { type, parent_id?, title, description?, acceptance_criteria?, priority?,
    risk?, story_points?, estimated_hours?, start_date?, due_date?, owner_id?,
    reviewer_id? }                                     any workspace member
GET    /api/v1/work-items/{work_item_id}                     any workspace member
PATCH  /api/v1/work-items/{work_item_id}                     any workspace member
DELETE /api/v1/work-items/{work_item_id}            any workspace member; cascades to the entire subtree

GET    /api/v1/work-items/{work_item_id}/children
GET    /api/v1/work-items/{work_item_id}/ancestors
PATCH  /api/v1/work-items/{work_item_id}/move          { new_parent_id }
  rejects moving into self, into a descendant (cycle), or across projects
PATCH  /api/v1/work-items/{work_item_id}/progress-override   { value: 0-100 | null }

GET    /api/v1/work-items/{work_item_id}/dependencies
POST   /api/v1/work-items/{work_item_id}/dependencies   { depends_on_id, type: blocks|relates_to }
  rejects self-dependency and the direct reverse edge (A→B blocks B→A); full
  transitive cycle detection deferred to the Dependency Graph view (Phase 2)
DELETE /api/v1/work-items/{work_item_id}/dependencies/{dependency_id}
```

Every endpoint above requires the caller to be a member of the work item's/
project's workspace (any role) unless noted otherwise.

**Deferred to a follow-up increment** (need shared polymorphic
comment/attachment infrastructure that doesn't exist yet — see
DATABASE_SCHEMA.md §5): `position` (board-column ordering) is stored but not
yet settable via the API; `time-logs`, `comments`, `attachments`, `labels`/
`tags`, and `custom-fields` sub-resources are not implemented.

`move`'s `position` parameter (board-column ordering within the new parent)
is not yet implemented — moves always land at the default position.

## 5. Requirements

```
GET    /api/v1/projects/{project_id}/requirements
  query: ?type=&status=&owner_id=
POST   /api/v1/projects/{project_id}/requirements
  { type, title, description, acceptance_criteria, priority, due_date }
GET    /api/v1/requirements/{id}
PATCH  /api/v1/requirements/{id}                (writes a new requirement_versions row)
DELETE /api/v1/requirements/{id}

GET    /api/v1/requirements/{id}/versions
GET    /api/v1/requirements/{id}/versions/{version_number}

GET    /api/v1/requirements/{id}/relations
POST   /api/v1/requirements/{id}/relations      { related_requirement_id, relation_type }

GET    /api/v1/requirements/{id}/work-items      (traceability: linked work items)
POST   /api/v1/requirements/{id}/work-items      { work_item_id }
DELETE /api/v1/requirements/{id}/work-items/{work_item_id}

GET    /api/v1/work-items/{id}/requirements       (reverse traceability lookup)

GET    /api/v1/requirements/{id}/comments
POST   /api/v1/requirements/{id}/comments
POST   /api/v1/requirements/{id}/attachments
```

## 6. Labels, Tags, Custom Fields

```
GET    /api/v1/workspaces/{workspace_id}/labels
POST   /api/v1/workspaces/{workspace_id}/labels     { name, color }
GET    /api/v1/workspaces/{workspace_id}/tags
POST   /api/v1/workspaces/{workspace_id}/tags       { name }

PUT    /api/v1/work-items/{id}/labels               { label_ids: [...] }
PUT    /api/v1/work-items/{id}/tags                 { tag_ids: [...] }

GET    /api/v1/projects/{project_id}/custom-fields
POST   /api/v1/projects/{project_id}/custom-fields  { name, field_type, options? }
PUT    /api/v1/work-items/{id}/custom-fields/{field_id}   { value }
```

## 7. Response Conventions

- Success: `{ "data": ..., "meta": {...}? }`
- List: `{ "data": [...], "meta": { "page", "page_size", "total" } }`
- Error: `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {...}? } }`
- All timestamps ISO 8601 UTC.
- All IDs are UUIDv4 strings.

## 8. Standard Error Codes

| Code | HTTP | Meaning |
|---|---|---|
| `UNAUTHENTICATED` | 401 | Missing/invalid token |
| `FORBIDDEN` | 403 | Authenticated but lacks permission for this scope |
| `NOT_FOUND` | 404 | Entity doesn't exist or isn't visible to caller |
| `VALIDATION_ERROR` | 422 | Request body/query failed schema validation |
| `CONFLICT` | 409 | Uniqueness or state conflict (e.g. duplicate slug) |
| `RATE_LIMITED` | 429 | Too many requests |

## 9. WebSocket Channels (real-time updates)

```
WS /api/v1/ws/projects/{project_id}
  Server -> Client events:
    work_item.created | work_item.updated | work_item.moved | work_item.deleted
    requirement.created | requirement.updated
    comment.created
    progress.recalculated  { entity_type, entity_id, new_progress }
```

## 10. Deferred to Later Phases

- `/sprints`, `/backlog`, `/standups` — Phase 2
- `/dashboard/executive` — Phase 3
- `/ai/*` (generate-epics, detect-duplicates, impact-analysis) — Phase 4
- `/briefings/*` — Phase 5
- `/automation-rules/*` — Phase 6
- `/integrations/*` — Phase 6
