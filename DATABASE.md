# Database Schema

PostgreSQL 16 with SQLAlchemy ORM and Alembic migrations.

## Entity Relationship

```
users ──┬── organization_members ── organizations
        │                              ├── departments
        │                              ├── agents (self-ref manager)
        │                              ├── projects
        │                              │     ├── epics → features
        │                              │     ├── sprints
        │                              │     └── tasks
        │                              ├── activity_events
        │                              └── audit_logs
        └── tasks (created_by)
```

## Core Tables

### users
Human users (CEO/managers). Email + bcrypt password.

### organizations
Multi-tenant companies. Unique slug, JSONB settings.

### organization_members
User ↔ Org mapping with role: `owner`, `admin`, `member`, `viewer`.

### agents
AI employees with full configuration:
- Role, department, manager
- AI provider/model/temperature/system_prompt
- Permissions, tools, escalation rules
- Status enum (15 states): idle, working, blocked, etc.

### projects
Software projects with goals, requirements, tech_stack, repository_url.

### epics → features → tasks
Hierarchical work breakdown. Tasks have:
- Status workflow (12 states)
- Dependencies (JSONB array of task IDs)
- Structured input_context and output
- Assignment to agents

### sprints
Sprint planning with dates, velocity, capacity.

### activity_events
Immutable event log for live feed.

### audit_logs
Compliance audit trail for human actions.

## Migrations

```bash
cd backend
alembic upgrade head        # Apply
alembic revision --autogenerate -m "description"  # New migration
```

## Enums

| Enum | Values |
|------|--------|
| OrgRole | owner, admin, member, viewer |
| AgentStatus | idle, assigned, working, blocked, failed, ... (15) |
| ProjectStatus | planning, active, on_hold, completed, archived |
| TaskStatus | backlog, ready, in_progress, blocked, completed, ... (12) |
| TaskPriority | low, medium, high, critical |
| SprintStatus | planned, active, completed, cancelled |
