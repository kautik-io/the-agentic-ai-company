# Workflows

## Orchestrator (Phase 5)

All agent communication flows through the central Orchestrator. Direct agent-to-agent communication is never allowed.

### Responsibilities

1. **Dependency resolution** — When task A completes, unlock dependent tasks
2. **Agent handoff** — Pass structured outputs to the next agent
3. **Follow-up** — PM agent follows up on late agents
4. **Blocker routing** — Route blockers to the right resolver
5. **Escalation** — Escalate to human when unresolvable
6. **Approval gates** — Enforce human approval policies

## Workflow Builder (Phase 11)

Visual node-based workflow editor using React Flow.

### Node Types

Agent, Task, Condition, Approval, Wait, Parallel, Join, Retry, Escalate, Notification, Webhook, Git Action, Test, Deployment

### Example Flow

```
Requirement → PM → Design → DB → Backend → Frontend → QA → Security → Code Review → Human Approval → DevOps → Production
```

## Durable Execution

Celery + Redis for task queue (Temporal-ready architecture). Workflows survive server restarts.

## Current Status

Orchestrator class scaffolded at `backend/app/orchestrator/__init__.py`. Full implementation in Phases 5–6.
