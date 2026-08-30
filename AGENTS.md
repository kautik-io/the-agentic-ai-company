# Agent Runtime

## Overview

The Agent Runtime (`backend/app/agent_runtime/`) provides a provider-agnostic abstraction for executing AI agent tasks.

## Architecture

```
AgentRuntime
  ├── OpenAIAdapter
  ├── AnthropicAdapter
  └── GoogleAdapter (Phase 4)
```

## AgentRunResult

Every execution produces:

| Field | Description |
|-------|-------------|
| run_id | Unique execution ID |
| agent_id | Employee ID |
| task_id | Task being executed |
| status | pending/running/completed/failed |
| output | Structured JSON output |
| token_usage | Tokens consumed |
| cost | Dollar cost |
| logs | Execution log lines |

## Structured Output

Agents must produce structured outputs for handoffs:

```json
{
  "status": "completed",
  "api_ready": true,
  "endpoints": ["POST /api/tickets"],
  "branch": "agent/backend-ticket-api",
  "pull_request": "PR-142",
  "tests_passed": 24,
  "notes": "Ready for frontend integration"
}
```

The orchestrator validates this output before unlocking dependent tasks.

## Configuration (per agent)

Configured via the Hire AI Employee form:
- AI provider (openai/anthropic/google)
- Model name
- Temperature
- System prompt
- Max token budget
- Max execution time
- Allowed tools

## Phase 4 Implementation

Real execution will:
1. Build context from task + dependencies + project memory
2. Call provider adapter
3. Parse structured output
4. Record run metrics
5. Emit activity events
6. Return result to orchestrator

**No fake progress** — dashboard metrics come from real run records.
