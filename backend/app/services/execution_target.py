from __future__ import annotations

import os
import socket
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ExecutionTarget,
    ExecutionTargetStatus,
    ExecutionTargetType,
)
from app.schemas.execution_target import ExecutionTargetCreate, ExecutionTargetResponse, ExecutionTargetUpdate
from app.services.workspace import WorkspaceError, WorkspaceService


def to_response(target: ExecutionTarget) -> ExecutionTargetResponse:
    return ExecutionTargetResponse(
        id=target.id,
        organization_id=target.organization_id,
        project_id=target.project_id,
        name=target.name,
        target_type=target.target_type.value,
        workspace_path=target.workspace_path,
        host=target.host,
        port=target.port,
        username=target.username,
        ssh_key_path=target.ssh_key_path,
        ssh_password_set=bool(target.ssh_password),
        docker_image=target.docker_image,
        is_default=target.is_default,
        status=target.status.value,
        last_error=target.last_error,
        last_verified_at=target.last_verified_at,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )


class ExecutionTargetService:
    @staticmethod
    async def list(db: AsyncSession, org_id: uuid.UUID) -> list[ExecutionTarget]:
        result = await db.execute(
            select(ExecutionTarget)
            .where(ExecutionTarget.organization_id == org_id)
            .order_by(ExecutionTarget.is_default.desc(), ExecutionTarget.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, target_id: uuid.UUID) -> ExecutionTarget | None:
        result = await db.execute(
            select(ExecutionTarget).where(
                ExecutionTarget.id == target_id,
                ExecutionTarget.organization_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _clear_default(db: AsyncSession, org_id: uuid.UUID) -> None:
        await db.execute(
            update(ExecutionTarget)
            .where(ExecutionTarget.organization_id == org_id, ExecutionTarget.is_default.is_(True))
            .values(is_default=False)
        )

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: ExecutionTargetCreate) -> ExecutionTarget:
        if data.is_default:
            await ExecutionTargetService._clear_default(db, org_id)
        target = ExecutionTarget(
            organization_id=org_id,
            name=data.name,
            target_type=ExecutionTargetType(data.target_type),
            workspace_path=data.workspace_path,
            project_id=data.project_id,
            host=data.host,
            port=data.port,
            username=data.username,
            ssh_key_path=data.ssh_key_path,
            ssh_password=data.ssh_password,
            docker_image=data.docker_image,
            is_default=data.is_default,
        )
        db.add(target)
        await db.flush()
        return target

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, target_id: uuid.UUID, data: ExecutionTargetUpdate
    ) -> ExecutionTarget | None:
        target = await ExecutionTargetService.get(db, org_id, target_id)
        if target is None:
            return None
        if data.is_default:
            await ExecutionTargetService._clear_default(db, org_id)
        payload = data.model_dump(exclude_unset=True)
        if "target_type" in payload:
            payload["target_type"] = ExecutionTargetType(payload["target_type"])
        for key, value in payload.items():
            setattr(target, key, value)
        await db.flush()
        await db.refresh(target)
        return target

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, target_id: uuid.UUID) -> bool:
        target = await ExecutionTargetService.get(db, org_id, target_id)
        if target is None:
            return False
        await db.delete(target)
        await db.flush()
        return True

    @staticmethod
    async def test_connection(target: ExecutionTarget) -> tuple[bool, str]:
        if target.target_type == ExecutionTargetType.LOCAL:
            if os.path.isdir(target.workspace_path):
                return True, f"Local path exists: {target.workspace_path}"
            if os.path.isabs(target.workspace_path):
                return False, f"Path not found on server: {target.workspace_path}. Create it or use SSH target."
            return False, "Workspace path must be an absolute path (e.g. /home/user/projects/my-app)"

        if target.target_type == ExecutionTargetType.SSH:
            if not target.host or not target.username:
                return False, "SSH target requires host and username"
            try:
                with socket.create_connection((target.host, target.port), timeout=5):
                    pass
                WorkspaceService._run_ssh(target, "echo ok")
                return True, f"SSH connected: {target.username}@{target.host}:{target.port}"
            except (OSError, WorkspaceError) as e:
                return False, f"SSH failed for {target.username}@{target.host}:{target.port} — {e}"

        if target.target_type == ExecutionTargetType.DOCKER:
            if not target.docker_image:
                return False, "Docker target requires an image name"
            return True, f"Docker config saved (runtime validation in Phase 4): {target.docker_image}"

        return False, "Unknown target type"

    @staticmethod
    async def run_test(db: AsyncSession, target: ExecutionTarget) -> ExecutionTarget:
        ok, message = await ExecutionTargetService.test_connection(target)
        target.status = ExecutionTargetStatus.CONNECTED if ok else ExecutionTargetStatus.ERROR
        target.last_error = None if ok else message
        target.last_verified_at = datetime.now(timezone.utc)
        await db.flush()
        return target
