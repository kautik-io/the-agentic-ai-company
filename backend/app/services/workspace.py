"""Provision project workspaces locally or on SSH execution targets."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from app.core.config import settings
from app.models import ExecutionTarget, ExecutionTargetType


class WorkspaceError(Exception):
    pass


class WorkspaceService:
    @staticmethod
    def project_path(org_slug: str, project_slug: str) -> str:
        return str(Path(settings.workspaces_root) / org_slug / project_slug)

    @staticmethod
    def remote_project_path(target: ExecutionTarget, org_slug: str, project_slug: str) -> str:
        base = target.workspace_path.rstrip("/")
        return f"{base}/{org_slug}/{project_slug}"

    @staticmethod
    def _ssh_base_args(target: ExecutionTarget) -> list[str]:
        args = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=10",
        ]
        if not target.ssh_password:
            args.extend(["-o", "BatchMode=yes"])
        if target.ssh_key_path:
            args.extend(["-i", target.ssh_key_path])
        args.extend(["-p", str(target.port), f"{target.username}@{target.host}"])
        return args

    @staticmethod
    def _ssh_command(target: ExecutionTarget, remote_command: str) -> list[str]:
        ssh_args = WorkspaceService._ssh_base_args(target)
        if target.ssh_password:
            return ["sshpass", "-p", target.ssh_password, *ssh_args, remote_command]
        return [*ssh_args, remote_command]

    @staticmethod
    def _run_ssh(target: ExecutionTarget, remote_command: str) -> subprocess.CompletedProcess:
        if not target.host or not target.username:
            raise WorkspaceError("SSH target requires host and username")
        if not target.ssh_key_path and not target.ssh_password:
            raise WorkspaceError("SSH target requires a private key path or password")
        cmd = WorkspaceService._ssh_command(target, remote_command)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "SSH command failed").strip()
            raise WorkspaceError(err)
        return result

    @staticmethod
    def _write_remote_file(target: ExecutionTarget, remote_path: str, content: str) -> None:
        escaped = content.replace("'", "'\"'\"'")
        cmd = f"printf '%s' '{escaped}' > {shlex.quote(remote_path)}"
        WorkspaceService._run_ssh(target, cmd)

    @staticmethod
    def provision_ssh(
        target: ExecutionTarget,
        org_slug: str,
        project_slug: str,
        project_name: str,
        logic_graph: str,
    ) -> str:
        root = WorkspaceService.remote_project_path(target, org_slug, project_slug)
        subs = ("src", "docs", "agents", "tests", ".graphs", "docs/features")
        mkdir_parts = " ".join(shlex.quote(f"{root}/{s}") for s in subs)
        WorkspaceService._run_ssh(target, f"mkdir -p {mkdir_parts}")

        readme = (
            f"# {project_name}\n\n"
            f"Agent workspace for **{project_name}**.\n\n"
            f"- Logic graph: `docs/LOGIC_GRAPH.md`\n"
            f"- Agent sandboxes: `agents/`\n"
        )
        graph_doc = (
            f"# Logic Graph — {project_name}\n\n"
            f"```mermaid\n{logic_graph}\n```\n"
        )
        WorkspaceService._write_remote_file(target, f"{root}/README.md", readme)
        WorkspaceService._write_remote_file(target, f"{root}/docs/LOGIC_GRAPH.md", graph_doc)
        WorkspaceService._write_remote_file(target, f"{root}/.graphs/project.mmd", logic_graph)
        return root

    @staticmethod
    def provision_local(org_slug: str, project_slug: str, project_name: str, logic_graph: str) -> str:
        root = Path(settings.workspaces_root) / org_slug / project_slug
        for sub in ("src", "docs", "agents", "tests", ".graphs"):
            (root / sub).mkdir(parents=True, exist_ok=True)

        readme = root / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# {project_name}\n\n"
                f"Agent workspace for **{project_name}**.\n\n"
                f"- Logic graph: `docs/LOGIC_GRAPH.md`\n"
                f"- Agent sandboxes: `agents/`\n",
                encoding="utf-8",
            )

        graph_file = root / "docs" / "LOGIC_GRAPH.md"
        graph_file.write_text(
            f"# Logic Graph — {project_name}\n\n"
            f"```mermaid\n{logic_graph}\n```\n",
            encoding="utf-8",
        )
        (root / ".graphs" / "project.mmd").write_text(logic_graph, encoding="utf-8")
        return str(root)

    @staticmethod
    def provision(
        org_slug: str,
        project_slug: str,
        project_name: str,
        logic_graph: str,
        target: ExecutionTarget | None = None,
    ) -> str:
        if target and target.target_type == ExecutionTargetType.SSH:
            return WorkspaceService.provision_ssh(target, org_slug, project_slug, project_name, logic_graph)
        return WorkspaceService.provision_local(org_slug, project_slug, project_name, logic_graph)

    @staticmethod
    def write_feature_graph(project_path: str, feature_slug: str, logic_graph: str, title: str) -> None:
        graphs_dir = Path(project_path) / ".graphs"
        graphs_dir.mkdir(parents=True, exist_ok=True)
        (graphs_dir / f"{feature_slug}.mmd").write_text(logic_graph, encoding="utf-8")
        docs = Path(project_path) / "docs" / "features"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / f"{feature_slug}.md").write_text(
            f"# Feature: {title}\n\n```mermaid\n{logic_graph}\n```\n",
            encoding="utf-8",
        )

    @staticmethod
    def write_feature_graph_ssh(
        target: ExecutionTarget,
        project_path: str,
        feature_slug: str,
        logic_graph: str,
        title: str,
    ) -> None:
        WorkspaceService._run_ssh(target, f"mkdir -p {shlex.quote(project_path)}/.graphs {shlex.quote(project_path)}/docs/features")
        WorkspaceService._write_remote_file(
            target, f"{project_path}/.graphs/{feature_slug}.mmd", logic_graph
        )
        WorkspaceService._write_remote_file(
            target,
            f"{project_path}/docs/features/{feature_slug}.md",
            f"# Feature: {title}\n\n```mermaid\n{logic_graph}\n```\n",
        )

    @staticmethod
    def remove_ssh(target: ExecutionTarget, project_path: str) -> None:
        WorkspaceService._run_ssh(target, f"rm -rf {shlex.quote(project_path)}")

    @staticmethod
    def verify_ssh(target: ExecutionTarget, project_path: str) -> bool:
        result = WorkspaceService._run_ssh(
            target, f"test -f {shlex.quote(project_path)}/README.md && test -f {shlex.quote(project_path)}/docs/LOGIC_GRAPH.md"
        )
        return result.returncode == 0
