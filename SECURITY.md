# Security

## Authentication

- JWT access tokens (60 min) + refresh tokens (7 days)
- bcrypt password hashing
- Token validation on every protected endpoint

## Authorization (RBAC)

| Role | Permissions |
|------|-------------|
| owner | Full control, delete org |
| admin | Manage agents, projects, settings |
| member | Create tasks, view dashboard |
| viewer | Read-only access |

## Organization Isolation

All queries scoped by organization_id. Cross-tenant access prevented at API layer.

## Agent Security

- Agents run in isolated workspaces (`/workspaces/project/agent-role/`)
- API keys stored in secrets manager, never in prompts
- Tool permissions scoped per agent
- Rate limiting on agent execution
- Max token budget and execution time limits

## Audit

All important actions logged to `audit_logs` table with previous/new values.

## Input Validation

Pydantic schemas validate all API inputs. SQL injection prevented via SQLAlchemy ORM.

## Production Requirements

- HTTPS everywhere
- Secure cookie settings
- CORS restricted to known origins
- Secrets via environment/secrets manager
- Regular dependency updates
- Agent sandboxing (Docker containers)
