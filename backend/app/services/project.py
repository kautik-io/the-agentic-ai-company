from __future__ import annotations
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityEvent,
    Agent,
    AgentStatus,
    Department,
    Project,
    ProjectStatus,
    Sprint,
    Task,
    TaskStatus,
)
from app.schemas.project import (
    AgentCreate,
    AgentUpdate,
    NaturalLanguageProjectCreate,
    ProjectCreate,
    ProjectUpdate,
    SprintCreate,
    TaskCreate,
    TaskUpdate,
)


def _project_slug(name: str) -> str:
    import re

    slug = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[\s_-]+", "-", slug).strip("-") or "project"


class AgentService:
    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: AgentCreate) -> Agent:
        agent = Agent(organization_id=org_id, **data.model_dump())
        db.add(agent)
        await db.flush()
        return agent

    @staticmethod
    async def list(db: AsyncSession, org_id: uuid.UUID) -> list[Agent]:
        result = await db.execute(
            select(Agent).where(Agent.organization_id == org_id, Agent.is_active.is_(True))
        )
        return list(result.scalars().all())

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
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(agent, key, value)
        await db.flush()
        return agent


class ProjectService:
    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, data: ProjectCreate
    ) -> Project:
        project = Project(
            organization_id=org_id,
            name=data.name,
            slug=_project_slug(data.name),
            description=data.description,
            goals=data.goals,
            requirements=data.requirements,
            tech_stack=data.tech_stack,
            repository_url=data.repository_url,
        )
        db.add(project)
        await db.flush()

        db.add(
            ActivityEvent(
                organization_id=org_id,
                project_id=project.id,
                user_id=user_id,
                event_type="project.created",
                message=f"Project '{project.name}' created",
            )
        )
        await db.flush()
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
