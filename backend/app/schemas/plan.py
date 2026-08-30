from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class PlannedTaskItem(BaseModel):
    title: str
    description: str | None = None
    epic: str
    feature: str
    agent_role: str = "Backend Developer"
    priority: str = "medium"
    phase: str = "build"
    estimated_minutes: int | None = None
    depends_on: list[str] = Field(default_factory=list)
    task_type: str = "build"
    manual: bool = False


class ManualTaskAdd(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    epic: str | None = None
    feature: str | None = None
    priority: str = "medium"
    agent_role: str = "Backend Developer"


class ProjectPlanResponse(BaseModel):
    project_id: uuid.UUID
    planning_status: str
    summary: str | None = None
    epics: list[dict] = Field(default_factory=list)
    features: list[dict] = Field(default_factory=list)
    tasks: list[dict] = Field(default_factory=list)
    manual_tasks: list[dict] = Field(default_factory=list)
    total_tasks: int = 0
    approved_at: str | None = None


class PlanApprovalResult(BaseModel):
    planning_status: str
    tasks_created: int
    epics_created: int
    features_created: int
    message: str
