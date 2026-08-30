"""Write agent deliverables into local or SSH project workspaces."""

from __future__ import annotations

import shlex
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings
from app.models import ExecutionTarget, ExecutionTargetType, Project
from app.services.execution_target import ExecutionTargetService
from app.services.workspace import WorkspaceError, WorkspaceService


@dataclass
class WriteResult:
    written: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.written) > 0 and not self.errors


class WorkspaceWriter:
    @staticmethod
    async def _resolve_target(db, org_id, project: Project) -> ExecutionTarget | None:
        target_id = (project.settings or {}).get("execution_target_id")
        if not target_id:
            return None
        return await ExecutionTargetService.get(db, org_id, uuid.UUID(str(target_id)))

    @staticmethod
    def _write_local(project_path: str, rel_path: str, content: str) -> None:
        root = Path(project_path)
        if not root.is_absolute():
            root = Path(settings.workspaces_root) / project_path
        dest = root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    @staticmethod
    def _write_ssh(target: ExecutionTarget, project_path: str, rel_path: str, content: str) -> None:
        remote = f"{project_path.rstrip('/')}/{rel_path}"
        WorkspaceService._run_ssh(target, f"mkdir -p {shlex.quote(str(Path(remote).parent))}")
        WorkspaceService._write_remote_file(target, remote, content)

    @staticmethod
    async def write_files(
        db,
        org_id,
        project: Project,
        files: list[dict[str, str]],
    ) -> WriteResult:
        result = WriteResult()
        if not project.workspace_path or not files:
            return result

        target = await WorkspaceWriter._resolve_target(db, org_id, project)
        use_ssh = target and target.target_type == ExecutionTargetType.SSH

        for item in files:
            path = (item.get("path") or "").strip().lstrip("/")
            content = item.get("content")
            if not path or content is None:
                continue
            try:
                if use_ssh and target:
                    WorkspaceWriter._write_ssh(target, project.workspace_path, path, content)
                else:
                    WorkspaceWriter._write_local(project.workspace_path, path, content)
                result.written.append(path)
            except (WorkspaceError, OSError) as exc:
                result.errors.append(f"{path}: {exc}")

        return result

    @staticmethod
    async def remote_paths_exist(
        db, org_id, project: Project, rel_paths: list[str]
    ) -> tuple[bool, list[str]]:
        missing: list[str] = []
        if not project.workspace_path:
            return False, rel_paths

        target = await WorkspaceWriter._resolve_target(db, org_id, project)
        if target and target.target_type == ExecutionTargetType.SSH:
            for rel in rel_paths:
                remote = f"{project.workspace_path.rstrip('/')}/{rel.lstrip('/')}"
                try:
                    WorkspaceService._run_ssh(target, f"test -f {shlex.quote(remote)}")
                except WorkspaceError:
                    missing.append(rel)
            return len(missing) == 0, missing

        root = Path(project.workspace_path)
        if not root.is_absolute():
            root = Path(settings.workspaces_root) / project.workspace_path
        for rel in rel_paths:
            if not (root / rel).is_file():
                missing.append(rel)
        return len(missing) == 0, missing

    @staticmethod
    async def run_remote_cmd(db, org_id, project: Project, command: str) -> tuple[int, str]:
        target = await WorkspaceWriter._resolve_target(db, org_id, project)
        if not target or target.target_type != ExecutionTargetType.SSH:
            return 1, "No SSH target"
        try:
            proc = WorkspaceService._run_ssh(target, f"cd {shlex.quote(project.workspace_path)} && {command}")
            return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
        except WorkspaceError as exc:
            return 1, str(exc)
