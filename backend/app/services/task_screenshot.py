"""Store and serve task completion screenshots."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Project, Task, TaskScreenshot


class TaskScreenshotService:
    @staticmethod
    def _upload_dir(project_id: uuid.UUID, task_id: uuid.UUID) -> Path:
        path = Path(settings.uploads_root) / "tasks" / str(project_id) / str(task_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def public_url(project_id: uuid.UUID, task_id: uuid.UUID, filename: str) -> str:
        return f"/api/uploads/tasks/{project_id}/{task_id}/{filename}"

    @staticmethod
    async def save(
        db: AsyncSession,
        task: Task,
        file: UploadFile,
        caption: str | None = None,
    ) -> TaskScreenshot:
        ext = Path(file.filename or "screenshot.png").suffix or ".png"
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            ext = ".png"
        filename = f"completion-{uuid.uuid4().hex[:12]}{ext}"
        dest_dir = TaskScreenshotService._upload_dir(task.project_id, task.id)
        dest_path = dest_dir / filename

        content = await file.read()
        dest_path.write_bytes(content)

        shot = TaskScreenshot(
            task_id=task.id,
            project_id=task.project_id,
            feature_id=task.feature_id,
            filename=filename,
            file_path=str(dest_path),
            caption=caption or f"Completion screenshot — {task.title}",
        )
        db.add(shot)
        await db.flush()
        return shot

    @staticmethod
    async def save_bytes(
        db: AsyncSession,
        task: Task,
        content: bytes,
        caption: str | None = None,
        ext: str = ".png",
    ) -> TaskScreenshot:
        filename = f"completion-{uuid.uuid4().hex[:12]}{ext}"
        dest_dir = TaskScreenshotService._upload_dir(task.project_id, task.id)
        dest_path = dest_dir / filename
        dest_path.write_bytes(content)

        shot = TaskScreenshot(
            task_id=task.id,
            project_id=task.project_id,
            feature_id=task.feature_id,
            filename=filename,
            file_path=str(dest_path),
            caption=caption or f"AI output — {task.title}",
        )
        db.add(shot)
        await db.flush()
        return shot

    @staticmethod
    async def capture_for_completed_task(
        db: AsyncSession,
        task: Task,
        project: Project,
        agent_name: str,
        output: dict,
        preview_host: str | None = None,
    ) -> list[TaskScreenshot]:
        try:
            from app.services.output_screenshot import capture_task_outputs

            shots: list[TaskScreenshot] = []
            for png_bytes, caption in await capture_task_outputs(
                task, project, agent_name, output, preview_host=preview_host
            ):
                shots.append(
                    await TaskScreenshotService.save_bytes(db, task, png_bytes, caption=caption)
                )
            return shots
        except Exception:
            return []

    @staticmethod
    async def list_for_task(db: AsyncSession, task_id: uuid.UUID) -> list[TaskScreenshot]:
        result = await db.execute(
            select(TaskScreenshot)
            .where(TaskScreenshot.task_id == task_id)
            .order_by(TaskScreenshot.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_for_project(db: AsyncSession, project_id: uuid.UUID) -> list[TaskScreenshot]:
        result = await db.execute(
            select(TaskScreenshot)
            .where(TaskScreenshot.project_id == project_id)
            .order_by(TaskScreenshot.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def to_dict(shot: TaskScreenshot, project_id: uuid.UUID, task_id: uuid.UUID) -> dict:
        return {
            "id": shot.id,
            "task_id": shot.task_id,
            "feature_id": shot.feature_id,
            "filename": shot.filename,
            "url": TaskScreenshotService.public_url(project_id, task_id, shot.filename),
            "caption": shot.caption,
            "created_at": shot.created_at,
        }
