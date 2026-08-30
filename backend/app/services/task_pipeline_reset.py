"""Reset and re-run project task pipeline after fake completions."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Task, TaskScreenshot, TaskStatus
from app.services.task_pipeline import is_login_task, merge_login_scaffold
from app.services.workspace_writer import WorkspaceWriter


class TaskPipelineReset:
    @staticmethod
    async def reset_project(db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """Reset execution tasks so design→build→test→fix runs again with validation."""
        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        if project is None:
            return {"reset": 0, "ready": 0}

        result = await db.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.task_number)
        )
        tasks = list(result.scalars())
        if not tasks:
            return {"reset": 0, "ready": 0}

        await db.execute(delete(TaskScreenshot).where(TaskScreenshot.project_id == project_id))

        reset_count = 0
        ready_count = 0
        build_completed = any(
            t.status == TaskStatus.COMPLETED
            and (t.input_context or {}).get("phase") in ("build", "fix")
            for t in tasks
        )

        for task in tasks:
            phase = (task.input_context or {}).get("phase", "build")

            if phase == "approval":
                task.status = TaskStatus.BACKLOG
                task.blocked_reason = None
            elif phase == "test" and build_completed and task.status in (TaskStatus.FAILED, TaskStatus.COMPLETED):
                # Re-run QA when build already exists but test failed under old rules
                task.status = TaskStatus.READY
                ready_count += 1
            elif phase == "fix" and task.status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.BACKLOG
                task.blocked_reason = None
            elif phase == "design" and not task.dependencies:
                task.status = TaskStatus.READY
                ready_count += 1
            elif not task.dependencies:
                task.status = TaskStatus.READY
                ready_count += 1
            elif task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.IN_PROGRESS):
                task.status = TaskStatus.BACKLOG
                task.blocked_reason = None
            else:
                task.status = TaskStatus.BACKLOG
                task.blocked_reason = None

            if task.status != TaskStatus.COMPLETED:
                reset_count += 1
            task.completed_at = None
            task.started_at = None
            task.assigned_agent_id = None
            task.output = {}
            task.failure_reason = None

        scaffold_written: list[str] = []
        if build_completed and any(is_login_task(t) for t in tasks):
            wr = await WorkspaceWriter.write_files(
                db, org_id, project, merge_login_scaffold([], force_required=True)
            )
            scaffold_written = wr.written

        await db.flush()
        return {
            "reset": reset_count,
            "ready": ready_count,
            "scaffold_files": scaffold_written,
            "message": f"Pipeline reset — {ready_count} task(s) ready, {reset_count} cleared for re-run",
        }

    @staticmethod
    async def retry_failed_test(db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """Apply login scaffold and re-queue a failed test without full pipeline reset."""
        from app.models import Agent, AgentStatus

        project_result = await db.execute(select(Project).where(Project.id == project_id))
        project = project_result.scalar_one_or_none()
        if project is None:
            return {"ready": 0, "message": "Project not found"}

        result = await db.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.task_number)
        )
        tasks = list(result.scalars())

        scaffold_written: list[str] = []
        if any(is_login_task(t) for t in tasks):
            wr = await WorkspaceWriter.write_files(
                db, org_id, project, merge_login_scaffold([], force_required=True)
            )
            scaffold_written = wr.written

        ready = 0
        for task in tasks:
            phase = (task.input_context or {}).get("phase")
            if phase == "test" and task.status == TaskStatus.FAILED:
                task.status = TaskStatus.READY
                task.failure_reason = None
                task.started_at = None
                task.completed_at = None
                ready += 1
            elif phase == "fix" and task.status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.BACKLOG
                task.started_at = None
                task.assigned_agent_id = None

        agents = await db.execute(select(Agent).where(Agent.organization_id == org_id))
        for agent in agents.scalars():
            if agent.current_task_id:
                agent.current_task_id = None
                agent.status = AgentStatus.IDLE

        await db.flush()
        return {
            "ready": ready,
            "scaffold_files": scaffold_written,
            "message": f"Test retry — {ready} task(s) ready, scaffold applied",
        }
