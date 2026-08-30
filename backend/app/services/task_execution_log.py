"""Persist and stream real agent execution logs per task."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityEvent, TaskExecutionRun


class TaskExecutionLogService:
    @staticmethod
    def _entry(level: str, message: str) -> dict:
        return {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }

    @staticmethod
    async def start_run(
        db: AsyncSession,
        *,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
        agent_id: uuid.UUID,
        agent_name: str,
        run_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        rid = run_id or uuid.uuid4()
        try:
            run = TaskExecutionRun(
                id=rid,
                organization_id=org_id,
                project_id=project_id,
                task_id=task_id,
                agent_id=agent_id,
                agent_name=agent_name,
                status="running",
                logs=[],
            )
            db.add(run)
            await db.flush()
        except Exception:
            await db.rollback()
        return rid

    @staticmethod
    async def append(
        db: AsyncSession,
        run_id: uuid.UUID,
        message: str,
        level: str = "info",
    ) -> None:
        if not message.strip():
            return
        try:
            result = await db.execute(select(TaskExecutionRun).where(TaskExecutionRun.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                return
            entry = TaskExecutionLogService._entry(level, message.strip())
            logs = list(run.logs or [])
            logs.append(entry)
            run.logs = logs
            await db.flush()
            await TaskExecutionLogService._broadcast(run.organization_id, run.task_id, entry)
        except Exception:
            await db.rollback()

    @staticmethod
    async def finish_run(
        db: AsyncSession,
        run_id: uuid.UUID,
        *,
        status: str,
        token_usage: int = 0,
        error: str | None = None,
    ) -> None:
        try:
            result = await db.execute(select(TaskExecutionRun).where(TaskExecutionRun.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                return
            run.status = status
            run.token_usage = token_usage
            run.error = error
            run.ended_at = datetime.now(timezone.utc)
            await db.flush()
        except Exception:
            await db.rollback()

    @staticmethod
    async def get_for_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> dict:
        try:
            result = await db.execute(
                select(TaskExecutionRun)
                .where(
                    TaskExecutionRun.organization_id == org_id,
                    TaskExecutionRun.task_id == task_id,
                )
                .order_by(TaskExecutionRun.started_at.desc())
            )
            runs = list(result.scalars())
            if runs:
                return {
                    "live": any(r.status == "running" for r in runs),
                    "runs": [
                        {
                            "id": str(r.id),
                            "status": r.status,
                            "agent_name": r.agent_name,
                            "token_usage": r.token_usage,
                            "error": r.error,
                            "started_at": r.started_at.isoformat() if r.started_at else None,
                            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                            "logs": r.logs or [],
                        }
                        for r in runs
                    ],
                }
        except Exception:
            await db.rollback()

        return await TaskExecutionLogService._activity_fallback(db, org_id, task_id)

    @staticmethod
    async def _activity_fallback(db: AsyncSession, org_id: uuid.UUID, task_id: uuid.UUID) -> dict:
        events_result = await db.execute(
            select(ActivityEvent)
            .where(
                ActivityEvent.organization_id == org_id,
                ActivityEvent.task_id == task_id,
            )
            .order_by(ActivityEvent.created_at.asc())
            .limit(50)
        )
        events = list(events_result.scalars())
        if not events:
            return {"live": False, "runs": []}

        logs = [
            TaskExecutionLogService._entry(
                "success" if "completed" in e.event_type else "error" if "failed" in e.event_type else "info",
                e.message,
            )
            for e in events
        ]
        return {
            "live": False,
            "runs": [
                {
                    "id": "activity-fallback",
                    "status": "completed",
                    "agent_name": None,
                    "token_usage": 0,
                    "error": None,
                    "started_at": events[0].created_at.isoformat(),
                    "ended_at": events[-1].created_at.isoformat(),
                    "logs": logs,
                }
            ],
        }

    @staticmethod
    async def _broadcast(org_id: uuid.UUID, task_id: uuid.UUID, entry: dict) -> None:
        try:
            from app.api.dashboard import manager

            await manager.broadcast(
                str(org_id),
                {"type": "task.log", "task_id": str(task_id), "entry": entry},
            )
        except Exception:
            pass
