from __future__ import annotations
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_org_membership
from app.services.project import ActivityService, DashboardService

router = APIRouter(prefix="/organizations/{org_id}", tags=["dashboard"])


class DashboardStats(BaseModel):
    active_projects: int
    total_agents: int
    active_agents: int
    total_tasks: int
    completed_tasks: int
    blocked_tasks: int
    failed_tasks: int
    completion_percentage: float


class ActivityResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    message: str
    project_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    task_id: uuid.UUID | None
    created_at: str


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await DashboardService.get_stats(db, org_id)


@router.get("/activities", response_model=list[ActivityResponse])
async def list_activities(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    project_id: uuid.UUID | None = None,
):
    events = await ActivityService.list(db, org_id, limit=limit, project_id=project_id)
    return [
        ActivityResponse(
            id=e.id,
            event_type=e.event_type,
            message=e.message,
            project_id=e.project_id,
            agent_id=e.agent_id,
            task_id=e.task_id,
            created_at=e.created_at.isoformat(),
        )
        for e in events
    ]


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, org_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(org_id, []).append(websocket)

    def disconnect(self, org_id: str, websocket: WebSocket):
        if org_id in self.active:
            self.active[org_id] = [ws for ws in self.active[org_id] if ws != websocket]

    async def broadcast(self, org_id: str, message: dict):
        for ws in self.active.get(org_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, org_id: uuid.UUID):
    await manager.connect(str(org_id), websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(str(org_id), websocket)
