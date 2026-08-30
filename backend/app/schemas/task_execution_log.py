from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class TaskExecutionLogEntry(BaseModel):
    ts: str
    level: str
    message: str


class TaskExecutionRunResponse(BaseModel):
    id: str
    status: str
    agent_name: str | None
    token_usage: int
    error: str | None
    started_at: str | None
    ended_at: str | None
    logs: list[TaskExecutionLogEntry] = Field(default_factory=list)


class TaskExecutionLogsResponse(BaseModel):
    live: bool
    runs: list[TaskExecutionRunResponse] = Field(default_factory=list)
