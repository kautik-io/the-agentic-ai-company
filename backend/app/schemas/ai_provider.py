from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AiProviderCreate(BaseModel):
    provider: str = Field(pattern="^(openai|anthropic|google)$")
    api_key: str = Field(min_length=8)
    enabled_models: list[str] = Field(min_length=1)


class AiProviderUpdate(BaseModel):
    api_key: str | None = Field(default=None, min_length=8)
    enabled_models: list[str] | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class AiProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    provider: str
    api_key_masked: str
    enabled_models: list
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProviderModelCatalog(BaseModel):
    provider: str
    label: str
    models: list[str]


class FetchModelsRequest(BaseModel):
    provider: str = Field(pattern="^(openai|anthropic|google)$")
    api_key: str = Field(min_length=8)


class FetchModelsResponse(BaseModel):
    provider: str
    models: list[str]
    recommended: list[str]
    message: str | None = None
