import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_org_membership
from app.models import User
from app.schemas.project import AgentCreate, AgentResponse, AgentUpdate
from app.services.project import AgentService

router = APIRouter(prefix="/organizations/{org_id}/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def hire_agent(
    org_id: uuid.UUID,
    data: AgentCreate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AgentService.create(db, org_id, data)


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AgentService.list(db, org_id)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    org_id: uuid.UUID,
    agent_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await AgentService.get(db, org_id, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    org_id: uuid.UUID,
    agent_id: uuid.UUID,
    data: AgentUpdate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    agent = await AgentService.update(db, org_id, agent_id, data)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent
