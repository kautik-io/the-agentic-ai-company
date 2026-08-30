from __future__ import annotations
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=1, max_length=255)
    department_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None
    description: str = Field(min_length=1)
    responsibilities: list[str] = Field(min_length=1)
    skills: list[str] = Field(min_length=1)
    ai_provider: str = "openai"
    ai_model: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0, le=2)
    system_prompt: str | None = None
    max_token_budget: int = Field(default=100000, ge=1000)
    max_execution_time: int = Field(default=3600, ge=60)
    allowed_tools: list[str] = Field(default_factory=list)
    allowed_repositories: list[str] = Field(default_factory=list)
    allowed_projects: list[str] = Field(default_factory=list)
    permission_level: str = "standard"
    working_hours: dict = Field(default_factory=dict)
    escalation_rules: dict = Field(default_factory=dict)
    execution_target_id: uuid.UUID | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    department_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None
    description: str | None = None
    responsibilities: list[str] | None = None
    skills: list[str] | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    temperature: float | None = None
    system_prompt: str | None = None
    max_token_budget: int | None = None
    max_execution_time: int | None = None
    allowed_tools: list[str] | None = None
    allowed_repositories: list[str] | None = None
    allowed_projects: list[str] | None = None
    permission_level: str | None = None
    working_hours: dict | None = None
    escalation_rules: dict | None = None
    is_active: bool | None = None
    execution_target_id: uuid.UUID | None = None
    status: str | None = None
    last_error: str | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    department_id: uuid.UUID | None
    manager_id: uuid.UUID | None
    execution_target_id: uuid.UUID | None
    name: str
    role: str
    description: str | None
    responsibilities: list
    skills: list
    ai_provider: str
    ai_model: str
    temperature: float
    system_prompt: str | None
    max_token_budget: int
    max_execution_time: int
    allowed_tools: list
    allowed_repositories: list
    allowed_projects: list
    permission_level: str
    working_hours: dict
    escalation_rules: dict
    status: str
    last_error: str | None
    tokens_used: int
    current_task_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    goals: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    repository_url: str | None = None
    execution_target_id: uuid.UUID | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    goals: list[str] | None = None
    requirements: list[str] | None = None
    tech_stack: list[str] | None = None
    repository_url: str | None = None
    status: str | None = None
    settings: dict | None = None
    logic_graph: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    goals: list
    requirements: list
    tech_stack: list
    repository_url: str | None
    workspace_path: str | None
    logic_graph: str | None
    environments: dict
    status: str
    settings: dict
    created_at: datetime
    updated_at: datetime


class EpicCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    logic_graph: str | None = None


class EpicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    logic_graph: str | None
    status: str
    created_at: datetime


class FeatureCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    logic_graph: str | None = None


class FeatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    epic_id: uuid.UUID
    title: str
    slug: str | None
    description: str | None
    logic_graph: str | None
    status: str
    created_at: datetime


class LogicGraphUpdate(BaseModel):
    logic_graph: str = Field(min_length=1)


class ProjectGraphResponse(BaseModel):
    project_id: uuid.UUID
    project_name: str
    logic_graph: str | None
    epics: list[EpicResponse]
    features: list[FeatureResponse]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    epic_id: uuid.UUID | None = None
    feature_id: uuid.UUID | None = None
    sprint_id: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None = None
    assigned_agent_id: uuid.UUID | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: str = "medium"
    estimated_minutes: int | None = None
    deadline: datetime | None = None
    dependencies: list[str] = Field(default_factory=list)
    required_output: dict = Field(default_factory=dict)
    input_context: dict = Field(default_factory=dict)


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assigned_agent_id: uuid.UUID | None = None
    acceptance_criteria: list[str] | None = None
    priority: str | None = None
    status: str | None = None
    estimated_minutes: int | None = None
    deadline: datetime | None = None
    blocked_reason: str | None = None
    sprint_id: uuid.UUID | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    epic_id: uuid.UUID | None
    feature_id: uuid.UUID | None
    sprint_id: uuid.UUID | None
    parent_task_id: uuid.UUID | None
    assigned_agent_id: uuid.UUID | None
    task_number: int
    title: str
    description: str | None
    acceptance_criteria: list
    priority: str
    status: str
    estimated_minutes: int | None
    actual_minutes: int | None
    deadline: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    retry_count: int
    blocked_reason: str | None
    failure_reason: str | None
    dependencies: list
    output: dict
    screenshots: list = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @property
    def display_id(self) -> str:
        return f"TASK-{self.task_number}"


class SprintCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    goal: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    capacity: int | None = None


class SprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    goal: str | None
    start_date: datetime | None
    end_date: datetime | None
    velocity: float | None
    capacity: int | None
    status: str
    created_at: datetime


class NaturalLanguageProjectCreate(BaseModel):
    description: str = Field(min_length=10)
    project_name: str | None = None
