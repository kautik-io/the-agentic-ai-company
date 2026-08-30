from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExecutionTargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    target_type: str = Field(default="local", pattern="^(local|ssh|docker)$")
    workspace_path: str = Field(min_length=1, max_length=1000)
    project_id: uuid.UUID | None = None
    host: str | None = None
    port: int = Field(default=22, ge=1, le=65535)
    username: str | None = None
    ssh_key_path: str | None = None
    ssh_password: str | None = None
    docker_image: str | None = None
    is_default: bool = False


class ExecutionTargetUpdate(BaseModel):
    name: str | None = None
    target_type: str | None = None
    workspace_path: str | None = None
    project_id: uuid.UUID | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    ssh_key_path: str | None = None
    ssh_password: str | None = None
    docker_image: str | None = None
    is_default: bool | None = None


class ExecutionTargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    target_type: str
    workspace_path: str
    host: str | None
    port: int
    username: str | None
    ssh_key_path: str | None
    ssh_password_set: bool = False
    docker_image: str | None
    is_default: bool
    status: str
    last_error: str | None
    last_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def display_uri(self) -> str:
        if self.target_type == "ssh" and self.host and self.username:
            return f"ssh://{self.username}@{self.host}:{self.port}{self.workspace_path}"
        if self.target_type == "docker":
            return f"docker://{self.docker_image or 'default'}{self.workspace_path}"
        return self.workspace_path


class ConnectionTestResult(BaseModel):
    success: bool
    message: str
    status: str
