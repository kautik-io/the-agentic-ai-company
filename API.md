# API Reference

Base URL: `http://localhost:8000/api`

Interactive docs: `/api/docs` (Swagger) and `/api/redoc`

## Authentication

### POST /auth/register

```json
{ "email": "user@example.com", "password": "password123", "full_name": "Jane Doe" }
```

### POST /auth/login

```json
{ "email": "user@example.com", "password": "password123" }
```

Returns `{ "access_token", "refresh_token", "token_type": "bearer" }`

### GET /auth/me

Requires `Authorization: Bearer <token>`

## Organizations

| Method | Path | Description |
|--------|------|-------------|
| POST | /organizations | Create organization |
| GET | /organizations | List user's organizations |
| GET | /organizations/{id} | Get organization |
| PATCH | /organizations/{id} | Update organization |
| GET | /organizations/{id}/members | List members |
| POST | /organizations/{id}/departments | Create department |
| GET | /organizations/{id}/departments | List departments |

## AI Agents

| Method | Path | Description |
|--------|------|-------------|
| POST | /organizations/{id}/agents | Hire agent |
| GET | /organizations/{id}/agents | List agents |
| GET | /organizations/{id}/agents/{agent_id} | Get agent |
| PATCH | /organizations/{id}/agents/{agent_id} | Update agent |

## Projects & Tasks

| Method | Path | Description |
|--------|------|-------------|
| POST | /organizations/{id}/projects | Create project |
| GET | /organizations/{id}/projects | List projects |
| POST | /organizations/{id}/projects/from-natural-language | NL project creation |
| POST | /organizations/{id}/projects/{pid}/tasks | Create task |
| GET | /organizations/{id}/projects/{pid}/tasks | List tasks |
| PATCH | /organizations/{id}/projects/{pid}/tasks/{tid} | Update task |
| POST | /organizations/{id}/projects/{pid}/sprints | Create sprint |
| GET | /organizations/{id}/projects/{pid}/sprints | List sprints |

## Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | /organizations/{id}/dashboard | Dashboard stats |
| GET | /organizations/{id}/activities | Activity feed |
| WS | /organizations/{id}/ws | WebSocket events |

## Health

`GET /api/health` — service health check
