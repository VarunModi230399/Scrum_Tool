# Database Schema — Phase 1

**Status:** Living document. Every schema change must be reflected here in the
same change as the Alembic migration. Additive only — no breaking changes
without a migration plan noted in CHANGELOG.md.

Database: PostgreSQL. Extensions used: `pgcrypto` (UUIDs), `ltree` (materialized paths, optional — delimited-string fallback documented below).

---

## 1. Identity & Tenancy

```sql
organizations
  id              uuid PK
  name            text NOT NULL
  slug            text UNIQUE NOT NULL
  created_at      timestamptz NOT NULL DEFAULT now()
  updated_at      timestamptz NOT NULL DEFAULT now()

users
  id              uuid PK
  email           text UNIQUE NOT NULL
  full_name       text NOT NULL
  password_hash   text NULL            -- null if OAuth-only
  avatar_url      text NULL
  timezone        text NOT NULL DEFAULT 'UTC'
  created_at      timestamptz NOT NULL DEFAULT now()
  updated_at      timestamptz NOT NULL DEFAULT now()

oauth_identities
  id              uuid PK
  user_id         uuid FK -> users.id
  provider        text NOT NULL         -- 'google' | 'microsoft'
  provider_uid    text NOT NULL
  UNIQUE (provider, provider_uid)

workspaces
  id              uuid PK
  organization_id uuid FK -> organizations.id
  name            text NOT NULL
  slug            text NOT NULL
  created_at      timestamptz NOT NULL DEFAULT now()
  UNIQUE (organization_id, slug)

workspace_memberships
  id              uuid PK
  workspace_id    uuid FK -> workspaces.id
  user_id         uuid FK -> users.id
  role            text NOT NULL   -- 'admin' | 'product_owner' | 'scrum_master' | 'developer' | 'viewer'
  created_at      timestamptz NOT NULL DEFAULT now()
  UNIQUE (workspace_id, user_id)
```

RBAC roles are also assignable at `project_id` scope (Phase 1) via an
identical `project_memberships` table — see §2. Org-level and
sprint/task/comment-level permission scoping (per the platform brief's
permission list) is layered on top in Phase 2+ once sprints exist; the
`role` enum and scope tables are designed to extend without a schema
rewrite (add `sprint_memberships` etc. later, same shape).

## 2. Projects

```sql
portfolios                          -- optional grouping above projects
  id              uuid PK
  workspace_id    uuid FK -> workspaces.id
  name            text NOT NULL
  description     text NULL
  created_at      timestamptz NOT NULL DEFAULT now()

projects
  id              uuid PK
  workspace_id    uuid FK -> workspaces.id
  portfolio_id    uuid FK -> portfolios.id NULL
  key             text NOT NULL          -- short project key, e.g. "ENG"
  name            text NOT NULL
  description     text NULL
  status          text NOT NULL DEFAULT 'active'  -- active | archived | on_hold
  progress        numeric(5,2) NOT NULL DEFAULT 0
  progress_override numeric(5,2) NULL
  created_at      timestamptz NOT NULL DEFAULT now()
  updated_at      timestamptz NOT NULL DEFAULT now()
  UNIQUE (workspace_id, key)

project_memberships
  id              uuid PK
  project_id      uuid FK -> projects.id
  user_id         uuid FK -> users.id
  role            text NOT NULL
  UNIQUE (project_id, user_id)

milestones
  id              uuid PK
  project_id      uuid FK -> projects.id
  name            text NOT NULL
  description     text NULL
  due_date        date NULL
  status          text NOT NULL DEFAULT 'planned'  -- planned | in_progress | completed | missed
  progress        numeric(5,2) NOT NULL DEFAULT 0
  created_at      timestamptz NOT NULL DEFAULT now()
```

## 3. Work Items (unified hierarchy)

See ARCHITECTURE.md §7 for the rationale on a single polymorphic table.

```sql
work_items
  id              uuid PK
  project_id      uuid FK -> projects.id NOT NULL
  milestone_id    uuid FK -> milestones.id NULL
  parent_id       uuid FK -> work_items.id NULL
  type            text NOT NULL        -- 'epic' | 'feature' | 'story' | 'task' | 'subtask' | 'checklist_item'
  path            text NOT NULL        -- materialized path: '<ancestor1>.<ancestor2>...<self>'
  depth           int  NOT NULL DEFAULT 0
  title           text NOT NULL
  description     text NULL            -- rich text (stored as JSON/HTML, editor-defined)
  acceptance_criteria text NULL
  status          text NOT NULL DEFAULT 'todo'   -- todo | in_progress | in_review | blocked | done
  priority        text NOT NULL DEFAULT 'medium' -- low | medium | high | critical
  risk            text NULL            -- low | medium | high
  story_points    numeric(5,2) NULL
  estimated_hours numeric(7,2) NULL
  actual_hours    numeric(7,2) NULL
  start_date      date NULL
  due_date        date NULL
  owner_id        uuid FK -> users.id NULL
  reviewer_id     uuid FK -> users.id NULL
  progress        numeric(5,2) NOT NULL DEFAULT 0
  progress_override numeric(5,2) NULL
  position        int NOT NULL DEFAULT 0   -- ordering within parent/board column
  created_by      uuid FK -> users.id NOT NULL
  created_at      timestamptz NOT NULL DEFAULT now()
  updated_at      timestamptz NOT NULL DEFAULT now()

  INDEX idx_work_items_path (path text_pattern_ops)   -- fast descendant lookups
  INDEX idx_work_items_parent (parent_id)
  INDEX idx_work_items_project (project_id)

work_item_dependencies
  id                  uuid PK
  work_item_id        uuid FK -> work_items.id      -- the dependent item
  depends_on_id       uuid FK -> work_items.id      -- the blocker
  type                text NOT NULL DEFAULT 'blocks' -- blocks | relates_to
  created_at          timestamptz NOT NULL DEFAULT now()
  UNIQUE (work_item_id, depends_on_id)

labels
  id              uuid PK
  workspace_id    uuid FK -> workspaces.id
  name            text NOT NULL
  color           text NOT NULL
  UNIQUE (workspace_id, name)

work_item_labels
  work_item_id    uuid FK -> work_items.id
  label_id        uuid FK -> labels.id
  PRIMARY KEY (work_item_id, label_id)

tags                                    -- freeform, distinct from curated labels
  id              uuid PK
  workspace_id    uuid FK -> workspaces.id
  name            text NOT NULL
  UNIQUE (workspace_id, name)

work_item_tags
  work_item_id    uuid FK -> work_items.id
  tag_id          uuid FK -> tags.id
  PRIMARY KEY (work_item_id, tag_id)

custom_field_definitions
  id              uuid PK
  project_id      uuid FK -> projects.id
  name            text NOT NULL
  field_type      text NOT NULL   -- text | number | date | select | multi_select | checkbox
  options         jsonb NULL       -- for select/multi_select
  UNIQUE (project_id, name)

custom_field_values
  id                      uuid PK
  work_item_id            uuid FK -> work_items.id
  custom_field_definition_id uuid FK -> custom_field_definitions.id
  value                   jsonb NOT NULL
  UNIQUE (work_item_id, custom_field_definition_id)

time_logs
  id              uuid PK
  work_item_id    uuid FK -> work_items.id
  user_id         uuid FK -> users.id
  hours           numeric(6,2) NOT NULL
  logged_date     date NOT NULL
  note            text NULL
  created_at      timestamptz NOT NULL DEFAULT now()
```

## 4. Requirements Module

```sql
requirements
  id              uuid PK
  project_id      uuid FK -> projects.id NOT NULL
  type            text NOT NULL   -- business | functional | technical | non_functional
                                    -- | research | bug | enhancement | user_story
  title           text NOT NULL
  description     text NULL        -- rich text
  acceptance_criteria text NULL
  priority        text NOT NULL DEFAULT 'medium'
  status          text NOT NULL DEFAULT 'draft'  -- draft | in_review | approved | implemented | rejected
  owner_id        uuid FK -> users.id NULL
  reviewer_id     uuid FK -> users.id NULL
  due_date        date NULL
  created_by      uuid FK -> users.id NOT NULL
  created_at      timestamptz NOT NULL DEFAULT now()
  updated_at      timestamptz NOT NULL DEFAULT now()

requirement_versions                    -- version history, append-only
  id              uuid PK
  requirement_id  uuid FK -> requirements.id
  version_number  int NOT NULL
  snapshot        jsonb NOT NULL         -- full field snapshot at this version
  changed_by      uuid FK -> users.id
  changed_at      timestamptz NOT NULL DEFAULT now()
  UNIQUE (requirement_id, version_number)

requirement_relations                    -- "related requirements"
  id                  uuid PK
  requirement_id      uuid FK -> requirements.id
  related_requirement_id uuid FK -> requirements.id
  relation_type       text NOT NULL DEFAULT 'related'  -- related | duplicates | conflicts_with
  UNIQUE (requirement_id, related_requirement_id)

requirement_work_item_links              -- the traceability join table (M:N)
  id              uuid PK
  requirement_id  uuid FK -> requirements.id
  work_item_id    uuid FK -> work_items.id
  created_at      timestamptz NOT NULL DEFAULT now()
  UNIQUE (requirement_id, work_item_id)
```

## 5. Collaboration (shared across work items & requirements)

Polymorphic association via `(entity_type, entity_id)` rather than duplicate
comment/attachment tables per entity — one implementation, reused everywhere.

```sql
comments
  id              uuid PK
  entity_type     text NOT NULL     -- 'work_item' | 'requirement'
  entity_id       uuid NOT NULL
  author_id       uuid FK -> users.id
  body            text NOT NULL      -- rich text
  created_at      timestamptz NOT NULL DEFAULT now()
  updated_at      timestamptz NOT NULL DEFAULT now()
  INDEX idx_comments_entity (entity_type, entity_id)

attachments
  id              uuid PK
  entity_type     text NOT NULL
  entity_id       uuid NOT NULL
  uploaded_by     uuid FK -> users.id
  file_name       text NOT NULL
  file_url        text NOT NULL       -- object storage URL
  file_size_bytes bigint NOT NULL
  mime_type       text NOT NULL
  created_at      timestamptz NOT NULL DEFAULT now()
  INDEX idx_attachments_entity (entity_type, entity_id)

external_links                          -- reserved for Phase 6 integrations
  id              uuid PK
  entity_type     text NOT NULL
  entity_id       uuid NOT NULL
  source          text NOT NULL         -- 'github' | 'gitlab' | 'azure_devops' | ...
  external_id     text NOT NULL
  external_url    text NOT NULL
  created_at      timestamptz NOT NULL DEFAULT now()
```

## 6. Checklist Items

Modeled as `work_items.type = 'checklist_item'` (leaf nodes, typically under a
task/subtask), not a separate table — they get progress rollup, comments, and
attachments for free via the same mechanisms as every other work item, and
"unlimited nesting" falls out of the same parent/path design instead of a
special case.

## 7. Auditing

```sql
audit_log
  id              uuid PK
  entity_type     text NOT NULL
  entity_id       uuid NOT NULL
  actor_id        uuid FK -> users.id
  action          text NOT NULL        -- created | updated | deleted | status_changed | ...
  diff            jsonb NULL
  created_at      timestamptz NOT NULL DEFAULT now()
  INDEX idx_audit_entity (entity_type, entity_id)
```

## 8. Deferred to Later Phases (documented now, not built)

- `sprints`, `sprint_items`, `retro_notes` — Phase 2
- `automation_rules`, `automation_runs` — Phase 6
- `notifications`, `notification_preferences` — Phase 3 (dashboard) / Phase 5 (briefing)
- `briefing_preferences` (preferred time, channels) — Phase 5
