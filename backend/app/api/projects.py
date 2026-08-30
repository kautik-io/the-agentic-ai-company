import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_org_membership
from app.models import Feature, Organization, Task, TaskStatus, User
from app.schemas.project import (
    EpicCreate,
    EpicResponse,
    FeatureCreate,
    FeatureResponse,
    LogicGraphUpdate,
    NaturalLanguageProjectCreate,
    ProjectCreate,
    ProjectGraphResponse,
    ProjectResponse,
    ProjectUpdate,
    SprintCreate,
    SprintResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.project import (
    ActivityService,
    DashboardService,
    EpicService,
    FeatureService,
    ProjectService,
    SprintService,
    TaskService,
)
from app.services.project_plan import ProjectPlanService
from app.services.task_screenshot import TaskScreenshotService
from app.services.workspace import WorkspaceService
from app.schemas.plan import ManualTaskAdd, PlanApprovalResult, ProjectPlanResponse
from app.schemas.task_execution_log import TaskExecutionLogsResponse
from app.schemas.task_screenshot import FeatureTaskReview, TaskScreenshotResponse
from app.services.task_execution_log import TaskExecutionLogService

router = APIRouter(prefix="/organizations/{org_id}/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    org_id: uuid.UUID,
    data: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await ProjectService.create(db, org_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ProjectService.list(db, org_id)


@router.post("/from-natural-language", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_from_nl(
    org_id: uuid.UUID,
    data: NaturalLanguageProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create project + workspace + starter epic/feature with logic graphs."""
    name = data.project_name or "New Project"
    return await ProjectService.create(
        db,
        org_id,
        current_user.id,
        ProjectCreate(
            name=name,
            description=data.description,
            requirements=[data.description],
        ),
    )


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


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    deleted = await ProjectService.delete(db, org_id, project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


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
    await ProjectPlanService.repair_stale_approval_tasks(db, project_id)
    tasks = await TaskService.list_for_project(db, project_id)
    shots = await TaskScreenshotService.list_for_project(db, project_id)
    by_task: dict[uuid.UUID, list] = {}
    for s in shots:
        by_task.setdefault(s.task_id, []).append(
            TaskScreenshotService.to_dict(s, project_id, s.task_id)
        )
    for task_id, items in by_task.items():
        items.sort(
            key=lambda x: (
                0 if x.get("caption") and "working" in x["caption"].lower() else 1,
                x.get("created_at") or "",
            )
        )
    result = []
    for t in tasks:
        data = TaskResponse.model_validate(t).model_dump()
        data["screenshots"] = by_task.get(t.id, [])
        result.append(TaskResponse(**data))
    return result


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


@router.post(
    "/{project_id}/tasks/{task_id}/screenshot",
    response_model=TaskScreenshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_task_screenshot(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    caption: str | None = Query(None),
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    task = await TaskService.get(db, project_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.COMPLETED:
        task.status = TaskStatus.COMPLETED
        if task.completed_at is None:
            from datetime import datetime, timezone

            task.completed_at = datetime.now(timezone.utc)

    shot = await TaskScreenshotService.save(db, task, file, caption=caption)
    await db.flush()
    return TaskScreenshotResponse(
        **TaskScreenshotService.to_dict(shot, project_id, task_id),
    )


@router.get("/{project_id}/tasks/{task_id}/screenshots", response_model=list[TaskScreenshotResponse])
async def list_task_screenshots(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await TaskService.get(db, project_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    shots = await TaskScreenshotService.list_for_task(db, task_id)
    return [
        TaskScreenshotResponse(**TaskScreenshotService.to_dict(s, project_id, task_id))
        for s in shots
    ]


@router.get("/{project_id}/tasks/{task_id}/execution-logs", response_model=TaskExecutionLogsResponse)
async def get_task_execution_logs(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await TaskService.get(db, project_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    data = await TaskExecutionLogService.get_for_task(db, org_id, task_id)
    return TaskExecutionLogsResponse(**data)


@router.get("/{project_id}/feature-reviews", response_model=list[FeatureTaskReview])
async def list_feature_reviews(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Task).where(Task.project_id == project_id, Task.status == TaskStatus.COMPLETED)
    )
    tasks = list(result.scalars().all())
    features = await FeatureService.list_for_project(db, project_id)
    feature_map = {f.id: f.title for f in features}
    shots = await TaskScreenshotService.list_for_project(db, project_id)
    shots_by_task: dict[uuid.UUID, list] = {}
    for s in shots:
        shots_by_task.setdefault(s.task_id, []).append(
            TaskScreenshotService.to_dict(s, project_id, s.task_id)
        )

    grouped: dict[str, dict] = {}
    for task in tasks:
        fid = str(task.feature_id) if task.feature_id else "none"
        title = feature_map.get(task.feature_id, "General") if task.feature_id else "General"
        if fid not in grouped:
            grouped[fid] = {"feature_id": task.feature_id, "feature_title": title, "tasks": []}
        grouped[fid]["tasks"].append({
            "task_id": str(task.id),
            "task_number": task.task_number,
            "title": task.title,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "screenshots": shots_by_task.get(task.id, []),
        })

    return [FeatureTaskReview(**g) for g in grouped.values()]


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


@router.get("/{project_id}/graph", response_model=ProjectGraphResponse)
async def get_project_graph(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    epics = await EpicService.list(db, project_id)
    features = await FeatureService.list_for_project(db, project_id)
    return ProjectGraphResponse(
        project_id=project.id,
        project_name=project.name,
        logic_graph=project.logic_graph,
        epics=epics,
        features=features,
    )


@router.patch("/{project_id}/graph", response_model=ProjectResponse)
async def update_project_graph(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    data: LogicGraphUpdate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.update(
        db, org_id, project_id, ProjectUpdate(logic_graph=data.logic_graph)
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.workspace_path:
        result = await db.execute(select(Organization.slug).where(Organization.id == org_id))
        org_slug = result.scalar_one()
        WorkspaceService.provision(org_slug, project.slug, project.name, data.logic_graph)
    return project


@router.get("/{project_id}/epics", response_model=list[EpicResponse])
async def list_epics(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await EpicService.list(db, project_id)


@router.post("/{project_id}/epics", response_model=EpicResponse, status_code=status.HTTP_201_CREATED)
async def create_epic(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    data: EpicCreate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await EpicService.create(db, org_id, project_id, data)


@router.post("/{project_id}/epics/{epic_id}/features", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    epic_id: uuid.UUID,
    data: FeatureCreate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await FeatureService.create(db, org_id, project_id, epic_id, data)


@router.get("/{project_id}/features", response_model=list[FeatureResponse])
async def list_features(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await FeatureService.list_for_project(db, project_id)


@router.get("/{project_id}/plan", response_model=ProjectPlanResponse)
async def get_project_plan(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    plan = await ProjectPlanService.get_plan_response(db, org_id, project_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return plan


@router.post("/{project_id}/pipeline/retry-test")
async def retry_project_test(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.project import ProjectService
    from app.services.task_pipeline_reset import TaskPipelineReset

    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await TaskPipelineReset.retry_failed_test(db, org_id, project_id)


@router.post("/{project_id}/pipeline/reset")
async def reset_project_pipeline(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.services.project import ProjectService
    from app.services.task_pipeline_reset import TaskPipelineReset

    project = await ProjectService.get(db, org_id, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await TaskPipelineReset.reset_project(db, org_id, project_id)


@router.post("/{project_id}/plan/approve", response_model=PlanApprovalResult)
async def approve_project_plan(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await ProjectPlanService.approve(db, org_id, project_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{project_id}/plan/reject", response_model=ProjectPlanResponse)
async def reject_project_plan(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    plan = await ProjectPlanService.reject(db, org_id, project_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return plan


@router.post("/{project_id}/plan/regenerate", response_model=ProjectPlanResponse)
async def regenerate_project_plan(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        plan = await ProjectPlanService.regenerate(db, org_id, project_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return plan


@router.post("/{project_id}/plan/tasks", response_model=ProjectPlanResponse)
async def add_manual_plan_task(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ManualTaskAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await ProjectPlanService.add_manual_task(db, org_id, project_id, current_user.id, data)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if "project_id" in result:
        return result
    plan = await ProjectPlanService.get_plan_response(db, org_id, project_id)
    return plan or result
