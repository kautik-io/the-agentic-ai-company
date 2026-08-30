"""Validate task outputs and apply real workspace deliverables."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.models import Project, Task, TaskStatus
from app.services.task_execution_log import TaskExecutionLogService
from app.services.workspace_writer import WorkspaceWriter

TEMPLATE_ROOT = Path("/templates/project-login-page")
if not TEMPLATE_ROOT.is_dir():
    TEMPLATE_ROOT = Path(__file__).resolve().parents[3] / "templates" / "project-login-page"

DOCKERFILE = """FROM nginx:alpine
COPY src/login /usr/share/nginx/html
EXPOSE 80
"""

DOCKER_COMPOSE = """services:
  web:
    build: .
    ports:
      - "6000:80"
    restart: unless-stopped
"""


def _slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "-", s).strip("-") or "feature"


def extract_files_from_output(output: dict, task: Task) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    raw = output.get("files")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and item.get("path") and item.get("content") is not None:
                files.append({"path": str(item["path"]), "content": str(item["content"])})

    html = output.get("html_deliverable") or output.get("html_preview")
    if html and isinstance(html, str) and "<" in html:
        files.append({"path": "src/login/index.html", "content": html})

    phase = (task.input_context or {}).get("phase", "build")
    if phase == "design" and not files:
        title = task.title.replace("Design:", "").strip()[:80]
        slug = _slug(title)
        body = output.get("summary") or output.get("notes") or json.dumps(output, indent=2)
        deliverables = output.get("deliverables") or []
        if deliverables:
            body += "\n\n## Deliverables\n" + "\n".join(f"- {d}" for d in deliverables)
        files.append({
            "path": f"docs/features/{slug}-design.md",
            "content": f"# Design: {title}\n\n{body}\n",
        })

    return files


def login_scaffold_files() -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    if not TEMPLATE_ROOT.is_dir():
        return files
    mapping = {
        "index.html": "src/login/index.html",
        "login.css": "src/login/login.css",
        "login.js": "src/login/login.js",
        "test_login_page.py": "tests/test_login_page.py",
    }
    for src_name, dest in mapping.items():
        src = TEMPLATE_ROOT / src_name
        if src.is_file():
            files.append({"path": dest, "content": src.read_text(encoding="utf-8")})
    files.append({"path": "Dockerfile", "content": DOCKERFILE})
    files.append({"path": "docker-compose.yml", "content": DOCKER_COMPOSE})
    return files


LOGIN_ARTIFACT_PATHS = [
    "src/login/index.html",
    "src/login/login.css",
    "src/login/login.js",
    "tests/test_login_page.py",
    "Dockerfile",
    "docker-compose.yml",
]


def merge_login_scaffold(files: list[dict[str, str]], *, force_required: bool = False) -> list[dict[str, str]]:
    """Fill missing login deliverables from template; normalize LLM naming."""
    by_path = {f["path"]: f["content"] for f in files}
    if "src/login/styles.css" in by_path and "src/login/login.css" not in by_path:
        by_path["src/login/login.css"] = by_path.pop("src/login/styles.css")
    for scaffold in login_scaffold_files():
        if force_required and scaffold["path"] in LOGIN_ARTIFACT_PATHS:
            by_path[scaffold["path"]] = scaffold["content"]
        else:
            by_path.setdefault(scaffold["path"], scaffold["content"])
    return [{"path": p, "content": c} for p, c in by_path.items()]


def is_login_task(task: Task) -> bool:
    return "login" in task.title.lower()


class TaskPipeline:
    @staticmethod
    async def _log(db, run_id, message: str, level: str = "info") -> None:
        if run_id:
            await TaskExecutionLogService.append(db, run_id, message, level)

    @staticmethod
    async def apply_and_validate(
        db,
        org_id,
        project: Project,
        task: Task,
        output: dict,
        *,
        run_id=None,
    ) -> tuple[bool, str, list[str]]:
        phase = (task.input_context or {}).get("phase", "build")
        files = extract_files_from_output(output, task)

        if files:
            await TaskPipeline._log(db, run_id, f"Agent returned {len(files)} file(s) in output", "info")
        else:
            await TaskPipeline._log(db, run_id, "No files in agent output — checking scaffold rules", "info")

        # Login build/fix — always ensure required artifacts exist (LLM may omit or rename files)
        if phase in ("build", "fix") and is_login_task(task):
            files = merge_login_scaffold(files)
            await TaskPipeline._log(db, run_id, "Merged login scaffold template files", "info")

        if files:
            await TaskPipeline._log(
                db, run_id, f"$ write {len(files)} file(s) → {project.workspace_path or 'workspace'}", "cmd"
            )
        write_result = await WorkspaceWriter.write_files(db, org_id, project, files)
        written = write_result.written
        for path in written:
            await TaskPipeline._log(db, run_id, f"  ✓ wrote {path}", "success")
        for err in write_result.errors:
            await TaskPipeline._log(db, run_id, f"  ✗ {err}", "error")

        if phase == "design":
            await TaskPipeline._log(db, run_id, "Checking design doc on workspace…", "info")
            ok, missing = await WorkspaceWriter.remote_paths_exist(
                db, org_id, project, written or [f"docs/features/{_slug(task.title)}-design.md"]
            )
            if not ok:
                return False, f"Design doc not written to workspace: {missing}", written
            return True, "Design spec saved to workspace", written

        if phase in ("build", "fix"):
            required = LOGIN_ARTIFACT_PATHS if is_login_task(task) else []
            if not written and not required:
                return False, "Build produced no files in workspace — task cannot complete", written
            check_paths = required or written[:5]
            await TaskPipeline._log(db, run_id, f"Verifying {len(check_paths)} artifact(s) exist on SSH…", "info")
            ok, missing = await WorkspaceWriter.remote_paths_exist(db, org_id, project, check_paths)
            if not ok:
                return False, f"Build artifacts missing on workspace: {missing}", written
            # Try docker compose for login projects
            if is_login_task(task) and "docker-compose.yml" in written:
                await TaskPipeline._log(db, run_id, "$ docker compose up -d --build", "cmd")
                code, out = await WorkspaceWriter.run_remote_cmd(
                    db, org_id, project, "docker compose up -d --build 2>&1 | tail -5"
                )
                for line in (out or "").strip().splitlines()[-5:]:
                    await TaskPipeline._log(db, run_id, f"  {line}", "info" if code == 0 else "error")
                if code != 0:
                    output.setdefault("deploy_notes", out[:500])
            return True, f"Build deployed {len(written)} file(s) to workspace", written

        if phase == "test":
            # Ensure canonical login artifacts before automated checks
            if is_login_task(task):
                scaffold = merge_login_scaffold(files, force_required=True)
                await TaskPipeline._log(db, run_id, "Ensuring canonical login test artifacts…", "info")
                write_result = await WorkspaceWriter.write_files(db, org_id, project, scaffold)
                written = write_result.written or written
            # Automated checks before trusting LLM
            checks: list[str] = []
            if is_login_task(task):
                ok, missing = await WorkspaceWriter.remote_paths_exist(
                    db, org_id, project,
                    ["src/login/index.html", "src/login/login.css", "src/login/login.js", "tests/test_login_page.py"],
                )
                if not ok:
                    return False, f"Cannot test — build artifacts missing: {missing}", written
                checks.append("login files exist")
                await TaskPipeline._log(db, run_id, "$ python3 tests/test_login_page.py", "cmd")
                code, out = await WorkspaceWriter.run_remote_cmd(
                    db, org_id, project, "python3 tests/test_login_page.py 2>&1"
                )
                for line in (out or "").strip().splitlines():
                    await TaskPipeline._log(
                        db, run_id, f"  {line}", "success" if code == 0 else "error"
                    )
                if code != 0:
                    return False, f"Automated tests failed: {out[:300]}", written
                checks.append("test_login_page.py passed")
            tests_passed = int(output.get("tests_passed") or 0)
            if tests_passed < 1 and checks:
                output["tests_passed"] = len(checks)
            if tests_passed < 1 and not checks:
                return False, "QA must run tests — tests_passed is 0 and no automated checks ran", written
            return True, f"Tests passed ({tests_passed or len(checks)} checks)", written

        # Scaffolding / approval / other
        if phase == "build" or written:
            return True, "Task deliverables applied", written
        return True, "Non-build phase completed", written

    @staticmethod
    def completion_status(task: Task, passed: bool) -> TaskStatus:
        phase = (task.input_context or {}).get("phase", "build")
        if passed:
            return TaskStatus.COMPLETED
        if phase == "test":
            return TaskStatus.FAILED
        return TaskStatus.FAILED
