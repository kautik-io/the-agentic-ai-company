from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict


class TaskScreenshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    feature_id: uuid.UUID | None
    filename: str
    url: str
    caption: str | None
    created_at: datetime


class FeatureTaskReview(BaseModel):
    feature_id: uuid.UUID | None
    feature_title: str
    tasks: list[dict]
