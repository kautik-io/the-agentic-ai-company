import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_org_membership
from app.models import User
from app.schemas.project import (
    NaturalLanguageProjectCreate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    SprintCreate,
    SprintResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.project import ActivityService, DashboardService, ProjectService, SprintService, TaskService

router = APIRouter(prefix="/organizations/{org_id}/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    org_id: uuid.UUID,
    data: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ProjectService.create(db, org_id, current_user.id, data)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ProjectService.list(db, org_id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ProjectUpdate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.update(db, org_id, project_id, data)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    data: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await TaskService.create(db, org_id, project_id, current_user.id, data)


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await TaskService.list_for_project(db, project_id)


@router.patch("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskUpdate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await TaskService.update(db, org_id, project_id, task_id, data)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/{project_id}/sprints", response_model=SprintResponse, status_code=status.HTTP_201_CREATED)
async def create_sprint(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    data: SprintCreate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await SprintService.create(db, project_id, data)


@router.get("/{project_id}/sprints", response_model=list[SprintResponse])
async def list_sprints(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await SprintService.list(db, project_id)


@router.post("/from-natural-language", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_from_nl(
    org_id: uuid.UUID,
    data: NaturalLanguageProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a project from natural language — PM agent planning queued for Phase 4."""
    name = data.project_name or "New Project"
    project = await ProjectService.create(
        db,
        org_id,
        current_user.id,
        ProjectCreate(
            name=name,
            description=data.description,
            requirements=[data.description],
        ),
    )
    return project
