from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentRunResult:
    run_id: str
    agent_id: str
    task_id: str
    status: RunStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    token_usage: int = 0
    cost: float = 0.0
    logs: list[str] = field(default_factory=list)
