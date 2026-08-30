from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityEvent,
    Agent,
    AgentStatus,
    Department,
    Epic,
    ExecutionTarget,
    ExecutionTargetType,
    Feature,
    Organization,
    Project,
    ProjectStatus,
    Sprint,
    Task,
    TaskStatus,
)
from app.schemas.project import (
    AgentCreate,
    AgentUpdate,
    EpicCreate,
    FeatureCreate,
    NaturalLanguageProjectCreate,
    ProjectCreate,
    ProjectUpdate,
    SprintCreate,
    TaskCreate,
    TaskUpdate,
)
from app.services.ai_provider import AiProviderService
from app.services.execution_target import ExecutionTargetService
from app.services.logic_graph import epic_graph, feature_graph, project_graph
from app.services.workspace import WorkspaceError, WorkspaceService


def _project_slug(name: str) -> str:
    import re

    slug = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[\s_-]+", "-", slug).strip("-") or "project"


class AgentService:
    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: AgentCreate) -> Agent:
        await AiProviderService.validate_agent_provider(db, org_id, data.ai_provider, data.ai_model)
        agent = Agent(organization_id=org_id, **data.model_dump())
        db.add(agent)
        await db.flush()
        return agent

    @staticmethod
    async def _repair_stale_pil_errors(db: AsyncSession, org_id: uuid.UUID) -> None:
        await db.execute(
            update(Agent)
            .where(
                Agent.organization_id == org_id,
                Agent.last_error.isnot(None),
                Agent.last_error.contains("PIL"),
            )
            .values(last_error=None)
        )
        await db.flush()

    @staticmethod
    async def list(
        db: AsyncSession, org_id: uuid.UUID, configured_only: bool = True
    ) -> list[Agent]:
        await AgentService._repair_stale_pil_errors(db, org_id)
        result = await db.execute(
            select(Agent).where(Agent.organization_id == org_id, Agent.is_active.is_(True))
        )
        agents = list(result.scalars().all())
        if not configured_only:
            return agents
        providers = await AiProviderService.configured_providers(db, org_id)
        if not providers:
            return []
        return [a for a in agents if a.ai_provider in providers]

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, agent_id: uuid.UUID) -> Agent | None:
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.organization_id == org_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, agent_id: uuid.UUID, data: AgentUpdate
    ) -> Agent | None:
        agent = await AgentService.get(db, org_id, agent_id)
        if agent is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "status" in update_data:
            update_data["status"] = AgentStatus(update_data["status"])
        provider = update_data.get("ai_provider", agent.ai_provider)
        model = update_data.get("ai_model", agent.ai_model)
        if "ai_provider" in update_data or "ai_model" in update_data:
            await AiProviderService.validate_agent_provider(db, org_id, provider, model)
        for key, value in update_data.items():
            setattr(agent, key, value)
        await db.flush()
        await db.refresh(agent)
        return agent


class ProjectService:
    @staticmethod
    async def _get_org_slug(db: AsyncSession, org_id: uuid.UUID) -> str:
        result = await db.execute(select(Organization.slug).where(Organization.id == org_id))
        return result.scalar_one()

    @staticmethod
    async def _resolve_execution_target(
        db: AsyncSession, org_id: uuid.UUID, execution_target_id: uuid.UUID | None
    ) -> ExecutionTarget | None:
        if execution_target_id:
            return await ExecutionTargetService.get(db, org_id, execution_target_id)
        result = await db.execute(
            select(ExecutionTarget).where(
                ExecutionTarget.organization_id == org_id,
                ExecutionTarget.target_type == ExecutionTargetType.SSH,
                ExecutionTarget.is_default.is_(True),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, data: ProjectCreate
    ) -> Project:
        slug = _project_slug(data.name)
        graph = project_graph(data.name, data.description)
        org_slug = await ProjectService._get_org_slug(db, org_id)
        target = await ProjectService._resolve_execution_target(db, org_id, data.execution_target_id)

        try:
            workspace_path = WorkspaceService.provision(
                org_slug, slug, data.name, graph, target=target
            )
        except WorkspaceError as e:
            raise ValueError(f"Workspace provisioning failed: {e}") from e

        project_settings: dict = {}
        if target:
            project_settings["execution_target_id"] = str(target.id)
            project_settings["workspace_type"] = target.target_type.value

        project = Project(
            organization_id=org_id,
            name=data.name,
            slug=slug,
            description=data.description,
            goals=data.goals,
            requirements=data.requirements,
            tech_stack=data.tech_stack,
            repository_url=data.repository_url,
            workspace_path=workspace_path,
            logic_graph=graph,
            settings=project_settings,
        )
        db.add(project)
        await db.flush()

        if target:
            target.project_id = project.id

        db.add(
            ActivityEvent(
                organization_id=org_id,
                project_id=project.id,
                user_id=user_id,
                event_type="project.created",
                message=f"Project '{project.name}' created at {workspace_path}",
            )
        )
        await db.flush()

        epic = Epic(
            project_id=project.id,
            title="Phase 1 — Planning",
            description=data.description,
            logic_graph=epic_graph("Phase 1 — Planning", data.description),
        )
        db.add(epic)
        await db.flush()

        feature = Feature(
            epic_id=epic.id,
            title="Initial scope",
            slug="initial-scope",
            description=data.description,
            logic_graph=feature_graph("Initial scope", data.description),
        )
        db.add(feature)
        await db.flush()

        if project.workspace_path and target and target.target_type == ExecutionTargetType.SSH:
            WorkspaceService.write_feature_graph_ssh(
                target, project.workspace_path, "initial-scope", feature.logic_graph, feature.title
            )
        elif project.workspace_path:
            WorkspaceService.write_feature_graph(
                project.workspace_path, "initial-scope", feature.logic_graph, feature.title
            )
        await ProjectService.refresh_project_graph(db, org_id, project.id)

        from app.services.project_plan import ProjectPlanService

        await ProjectPlanService.attach_draft(
            db, org_id, project, user_id, data.goals, data.requirements
        )
        await ProjectPlanService.approve(db, org_id, project.id, user_id)

        await db.refresh(project)
        return project

    @staticmethod
    async def list(db: AsyncSession, org_id: uuid.UUID) -> list[Project]:
        result = await db.execute(
            select(Project).where(Project.organization_id == org_id).order_by(Project.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID) -> Project | None:
        result = await db.execute(
            select(Project).where(Project.id == project_id, Project.organization_id == org_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID, data: ProjectUpdate
    ) -> Project | None:
        project = await ProjectService.get(db, org_id, project_id)
        if project is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        await db.flush()
        return project

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID) -> bool:
        project = await ProjectService.get(db, org_id, project_id)
        if project is None:
            return False

        target_id = project.settings.get("execution_target_id") if project.settings else None
        if target_id and project.workspace_path:
            target = await ExecutionTargetService.get(db, org_id, uuid.UUID(str(target_id)))
            if target and target.target_type == ExecutionTargetType.SSH:
                try:
                    WorkspaceService.remove_ssh(target, project.workspace_path)
                except WorkspaceError:
                    pass

        await db.delete(project)
        await db.flush()
        return True

    @staticmethod
    async def refresh_project_graph(db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID) -> None:
        project = await ProjectService.get(db, org_id, project_id)
        if project is None:
            return
        epics = await EpicService.list(db, project_id)
        epic_tuples = [(e.title, str(e.id)) for e in epics]
        graph = project_graph(project.name, project.description, epic_tuples)
        project.logic_graph = graph
        if project.workspace_path:
            org_slug = await ProjectService._get_org_slug(db, org_id)
            target_id = project.settings.get("execution_target_id") if project.settings else None
            target = None
            if target_id:
                target = await ExecutionTargetService.get(db, org_id, uuid.UUID(str(target_id)))
            WorkspaceService.provision(org_slug, project.slug, project.name, graph, target=target)
        await db.flush()


class EpicService:
    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID, data: EpicCreate
    ) -> Epic:
        graph = data.logic_graph or epic_graph(data.title, data.description)
        epic = Epic(
            project_id=project_id,
            title=data.title,
            description=data.description,
            logic_graph=graph,
        )
        db.add(epic)
        await db.flush()
        await ProjectService.refresh_project_graph(db, org_id, project_id)
        return epic

    @staticmethod
    async def list(db: AsyncSession, project_id: uuid.UUID) -> list[Epic]:
        result = await db.execute(
            select(Epic).where(Epic.project_id == project_id).order_by(Epic.created_at)
        )
        return list(result.scalars().all())


class FeatureService:
    @staticmethod
    async def create(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        epic_id: uuid.UUID,
        data: FeatureCreate,
    ) -> Feature:
        graph = data.logic_graph or feature_graph(data.title, data.description)
        slug = _project_slug(data.title)
        feature = Feature(
            epic_id=epic_id,
            title=data.title,
            slug=slug,
            description=data.description,
            logic_graph=graph,
        )
        db.add(feature)
        await db.flush()

        project = await ProjectService.get(db, org_id, project_id)
        if project and project.workspace_path:
            WorkspaceService.write_feature_graph(project.workspace_path, slug, graph, data.title)

        await ProjectService.refresh_project_graph(db, org_id, project_id)
        return feature

    @staticmethod
    async def list_for_project(db: AsyncSession, project_id: uuid.UUID) -> list[Feature]:
        result = await db.execute(
            select(Feature)
            .join(Epic)
            .where(Epic.project_id == project_id)
            .order_by(Feature.created_at)
        )
        return list(result.scalars().all())


class TaskService:
    @staticmethod
    async def _next_task_number(db: AsyncSession, project_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.coalesce(func.max(Task.task_number), 0)).where(Task.project_id == project_id)
        )
        return (result.scalar() or 0) + 1

    @staticmethod
    async def create(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID | None,
        data: TaskCreate,
    ) -> Task:
        task_number = await TaskService._next_task_number(db, project_id)
        task = Task(
            project_id=project_id,
            task_number=task_number,
            created_by_id=user_id,
            **data.model_dump(),
        )
        db.add(task)
        await db.flush()

        db.add(
            ActivityEvent(
                organization_id=org_id,
                project_id=project_id,
                task_id=task.id,
                user_id=user_id,
                event_type="task.created",
                message=f"TASK-{task_number} created: {task.title}",
            )
        )
        await db.flush()
        return task

    @staticmethod
    async def list_for_project(db: AsyncSession, project_id: uuid.UUID) -> list[Task]:
        result = await db.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.task_number.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, project_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        result = await db.execute(
            select(Task).where(Task.id == task_id, Task.project_id == project_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID, task_id: uuid.UUID, data: TaskUpdate
    ) -> Task | None:
        task = await TaskService.get(db, project_id, task_id)
        if task is None:
            return None
        old_status = task.status
        update_data = data.model_dump(exclude_unset=True)
        if "status" in update_data:
            update_data["status"] = TaskStatus(update_data["status"])
        for key, value in update_data.items():
            setattr(task, key, value)
        if "status" in update_data and update_data["status"] == TaskStatus.COMPLETED:
            if task.completed_at is None:
                task.completed_at = datetime.now(timezone.utc)
        if "status" in update_data and update_data["status"] != old_status:
            db.add(
                ActivityEvent(
                    organization_id=org_id,
                    project_id=project_id,
                    task_id=task.id,
                    event_type="task.status.changed",
                    message=f"TASK-{task.task_number} status: {old_status.value} → {update_data['status'].value}",
                    event_metadata={"old_status": old_status.value, "new_status": update_data["status"].value},
                )
            )
        await db.flush()
        return task


class SprintService:
    @staticmethod
    async def create(db: AsyncSession, project_id: uuid.UUID, data: SprintCreate) -> Sprint:
        sprint = Sprint(project_id=project_id, **data.model_dump())
        db.add(sprint)
        await db.flush()
        return sprint

    @staticmethod
    async def list(db: AsyncSession, project_id: uuid.UUID) -> list[Sprint]:
        result = await db.execute(
            select(Sprint).where(Sprint.project_id == project_id).order_by(Sprint.created_at.desc())
        )
        return list(result.scalars().all())


class DepartmentService:
    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, name: str, description: str | None) -> Department:
        dept = Department(organization_id=org_id, name=name, description=description)
        db.add(dept)
        await db.flush()
        return dept

    @staticmethod
    async def list(db: AsyncSession, org_id: uuid.UUID) -> list[Department]:
        result = await db.execute(
            select(Department).where(Department.organization_id == org_id).order_by(Department.name)
        )
        return list(result.scalars().all())


class ActivityService:
    @staticmethod
    async def list(
        db: AsyncSession, org_id: uuid.UUID, limit: int = 50, project_id: uuid.UUID | None = None
    ) -> list[ActivityEvent]:
        query = select(ActivityEvent).where(ActivityEvent.organization_id == org_id)
        if project_id:
            query = query.where(ActivityEvent.project_id == project_id)
        query = query.order_by(ActivityEvent.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


class DashboardService:
    @staticmethod
    async def get_stats(db: AsyncSession, org_id: uuid.UUID) -> dict:
        projects = await db.execute(
            select(func.count(Project.id)).where(
                Project.organization_id == org_id, Project.status == ProjectStatus.ACTIVE
            )
        )
        agents = await db.execute(
            select(func.count(Agent.id)).where(Agent.organization_id == org_id, Agent.is_active.is_(True))
        )
        active_agents = await db.execute(
            select(func.count(Agent.id)).where(
                Agent.organization_id == org_id,
                Agent.status.in_([
                    AgentStatus.WORKING,
                    AgentStatus.ANALYZING,
                    AgentStatus.TESTING,
                    AgentStatus.REVIEWING,
                ]),
            )
        )
        tasks = await db.execute(
            select(func.count(Task.id))
            .join(Project)
            .where(Project.organization_id == org_id)
        )
        completed_tasks = await db.execute(
            select(func.count(Task.id))
            .join(Project)
            .where(Project.organization_id == org_id, Task.status == TaskStatus.COMPLETED)
        )
        blocked_tasks = await db.execute(
            select(func.count(Task.id))
            .join(Project)
            .where(Project.organization_id == org_id, Task.status == TaskStatus.BLOCKED)
        )
        failed_tasks = await db.execute(
            select(func.count(Task.id))
            .join(Project)
            .where(Project.organization_id == org_id, Task.status == TaskStatus.FAILED)
        )

        total = tasks.scalar() or 0
        completed = completed_tasks.scalar() or 0
        completion_pct = round((completed / total * 100) if total > 0 else 0, 1)

        return {
            "active_projects": projects.scalar() or 0,
            "total_agents": agents.scalar() or 0,
            "active_agents": active_agents.scalar() or 0,
            "total_tasks": total,
            "completed_tasks": completed,
            "blocked_tasks": blocked_tasks.scalar() or 0,
            "failed_tasks": failed_tasks.scalar() or 0,
            "completion_percentage": completion_pct,
        }
