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
