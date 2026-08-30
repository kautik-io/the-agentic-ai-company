# AI Engineering OS (AIOS) — Architecture

## Overview

AI Engineering OS is an event-driven, state-driven platform where AI agents operate as a coordinated engineering team within organizations. All agent communication flows through a central **Orchestrator** — never direct agent-to-agent channels.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  Dashboard │ Kanban │ Agents │ Workflows │ Live Feed │ Settings │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                      API Layer (FastAPI)                         │
│  Auth │ Orgs │ Projects │ Agents │ Tasks │ Sprints │ Workflows  │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Orchestrator │   │ Agent Runtime │   │ Event Bus     │
│  (workflow)   │   │ (LLM adapters)│   │ (Redis/SSE)   │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
              ┌─────────────────────────┐
              │  PostgreSQL + Redis     │
              └─────────────────────────┘
```

## Core Principles

1. **Event-driven**: Every action emits events persisted and broadcast live.
2. **State-driven**: Agent/task status transitions are explicit and auditable.
3. **Orchestrator-mediated**: All inter-agent communication goes through the orchestrator.
4. **No fake data**: Dashboard metrics come from real execution records.
5. **Durable workflows**: Pending work survives restarts (Celery + Redis, Temporal-ready).

## Layer Breakdown

### Frontend (`/frontend`)
- **Next.js 14** App Router, TypeScript, Tailwind CSS, shadcn/ui
- React Query for server state, WebSocket for live updates
- React Flow for workflow builder (Phase 11)

### Backend (`/backend`)
- **FastAPI** with async SQLAlchemy 2.0
- **PostgreSQL** for durable state
- **Redis** for pub/sub, caching, Celery broker
- **Celery** workers for agent execution (Phase 4+)

### Agent Runtime (`backend/app/agent_runtime/`)
- Provider-agnostic abstraction: OpenAI, Anthropic, Google, local models
- Structured output validation
- Token/cost tracking per run

### Orchestrator (`backend/app/orchestrator/`)
- Dependency resolution for tasks
- Agent handoff with structured outputs
- Follow-up, retry, and escalation logic
- Approval gate enforcement

## Data Model Hierarchy

```
Organization
 └── Department
 └── Agent (AI Employee)
 └── Project
      └── Epic → Feature → Task → Subtask
      └── Sprint
      └── Workflow
      └── Memory (project-scoped)
 └── Policy / Approval Rules
 └── Audit Log
```

## Real-Time Events

WebSocket channel per organization. Event types:

| Event | Description |
|-------|-------------|
| `agent.status.changed` | Agent working status update |
| `task.status.changed` | Task lifecycle transition |
| `task.assigned` | Task assigned to agent |
| `agent.message.created` | Orchestrator-routed message |
| `notification.created` | Human alert |
| `sprint.progress.changed` | Sprint metrics update |
| `activity.created` | Activity feed entry |

## Security

- JWT access + refresh tokens
- RBAC: org owner, admin, member, viewer
- Agent tool permissions scoped per employee
- Secrets stored encrypted, never in prompts
- Rate limiting on API and agent execution

## MVP Phases

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Auth + Organizations | ✅ Current |
| 2 | Projects + Agents + Tasks | 🔜 |
| 3 | Sprint + Kanban | 🔜 |
| 4 | Agent Execution Engine | 🔜 |
| 5 | Orchestrator | 🔜 |
| 6 | Agent Dependencies | 🔜 |
| 7 | Live WebSocket Dashboard | 🔜 |
| 8 | Git Integration | 🔜 |
| 9 | QA/Review Workflows | 🔜 |
| 10 | Notifications/Escalation | 🔜 |
| 11 | Workflow Builder | 🔜 |
| 12 | Analytics/Cost Tracking | 🔜 |
| 13 | Production Deployment | 🔜 |

## Directory Structure

```
the-agentic-ai-company/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── core/          # Config, security, deps
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── agent_runtime/ # LLM adapters (Phase 4)
│   │   ├── orchestrator/  # Workflow engine (Phase 5)
│   │   └── events/        # Event bus (Phase 7)
│   ├── alembic/           # Migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/           # Next.js routes
│       ├── components/    # UI components
│       └── lib/           # API client, hooks
├── docker-compose.yml
└── docs/
```
