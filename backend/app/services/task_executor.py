from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent_runtime import AgentRuntime, RunStatus
from app.models import (
    ActivityEvent,
    Agent,
    AgentStatus,
    Project,
    ProjectStatus,
    Task,
    TaskStatus,
)
from app.services.ai_provider import AiProviderService
from app.services.task_execution_log import TaskExecutionLogService
from app.services.task_pipeline import TaskPipeline

logger = logging.getLogger(__name__)

_runtime = AgentRuntime()

ROLE_FALLBACKS: dict[str, list[str]] = {
    "UI/UX Designer": ["Frontend Developer"],
    "Backend Developer": ["DevOps Engineer", "Database Engineer"],
    "QA Engineer": ["Backend Developer", "Frontend Developer"],
    "Security Engineer": ["Backend Developer"],
    "Code Reviewer": ["Backend Developer", "Frontend Developer"],
}

STRUCTURED_OUTPUT_INSTRUCTION = """
Return JSON only:
{
  "status": "completed",
  "summary": "what was done",
  "files": [{"path": "src/login/index.html", "content": "<full file content>"}],
  "tests_passed": 0,
  "notes": "optional"
}
RULES:
- design: write spec content into files[0] targeting docs/features/<name>-design.md
- build/fix: MUST include every created file in files[] with full content (HTML, CSS, JS, Dockerfile, docker-compose.yml)
- test: run verification, set tests_passed >= 1 only if artifacts exist and pass checks
- Do NOT claim completed without providing files[] for build/fix/design phases
"""


class TaskExecutorService:
    @staticmethod
    async def _configured_provider_keys(db: AsyncSession, org_id: uuid.UUID) -> dict[str, str]:
        keys: dict[str, str] = {}
        for config in await AiProviderService.list(db, org_id, active_only=True):
            if config.api_key:
                keys[config.provider] = config.api_key
        return keys

    @staticmethod
    def _role_for_task(task: Task) -> str:
        ctx = task.input_context or {}
        if ctx.get("agent_role"):
            return str(ctx["agent_role"])
        phase = ctx.get("phase", "build")
        title = task.title.lower()
        if phase == "design":
            return "UI/UX Designer"
        if phase == "test":
            return "QA Engineer"
        if phase == "fix":
            return "Backend Developer"
        if any(k in title for k in ("ui", "page", "dashboard", "login", "frontend", "portal")):
            return "Frontend Developer"
        if any(k in title for k in ("deploy", "docker", "infra", "ci")):
            return "DevOps Engineer"
        return "Backend Developer"

    @staticmethod
    async def _resolve_agent(
        db: AsyncSession,
        org_id: uuid.UUID,
        task: Task,
        provider_keys: dict[str, str],
    ) -> Agent | None:
        agents_result = await db.execute(
            select(Agent).where(Agent.organization_id == org_id, Agent.is_active.is_(True))
        )
        agents = list(agents_result.scalars())

        def is_runnable(agent: Agent) -> bool:
            return (
                agent.ai_provider in provider_keys
                and agent.status == AgentStatus.IDLE
                and agent.tokens_used < agent.max_token_budget
            )

        def pick_for_role(role: str) -> Agent | None:
            matches = [a for a in agents if a.role == role and is_runnable(a)]
            if matches:
                return matches[0]
            for fallback_role in ROLE_FALLBACKS.get(role, []):
                fallback = [a for a in agents if a.role == fallback_role and is_runnable(a)]
                if fallback:
                    return fallback[0]
            return None

        assigned = next((a for a in agents if a.id == task.assigned_agent_id), None) if task.assigned_agent_id else None
        if assigned and is_runnable(assigned):
            return assigned
        if assigned:
            picked = pick_for_role(assigned.role)
            if picked:
                return picked

        return pick_for_role(TaskExecutorService._role_for_task(task))

    @staticmethod
    async def _unlock_dependents(db: AsyncSession, project_id: uuid.UUID) -> int:
        tasks_result = await db.execute(select(Task).where(Task.project_id == project_id))
        all_tasks = list(tasks_result.scalars())
        completed_ids = {str(t.id) for t in all_tasks if t.status == TaskStatus.COMPLETED}
        failed_ids = {str(t.id) for t in all_tasks if t.status == TaskStatus.FAILED}
        task_by_id = {str(t.id): t for t in all_tasks}
        unlocked = 0

        for task in all_tasks:
            if task.status not in (TaskStatus.BACKLOG, TaskStatus.WAITING):
                continue
            deps = [str(d) for d in (task.dependencies or [])]
            if not deps:
                continue

            phase = (task.input_context or {}).get("phase", "build")
            deps_ok = True
            for dep_id in deps:
                dep = task_by_id.get(dep_id)
                if dep_id in completed_ids:
                    continue
                if phase == "fix" and dep_id in failed_ids and dep and (dep.input_context or {}).get("phase") == "test":
                    continue
                deps_ok = False
                break
            if not deps_ok:
                continue
            if phase == "approval":
                task.status = TaskStatus.WAITING
                task.blocked_reason = "Build complete — ready for launch review"
            else:
                task.status = TaskStatus.READY
                task.blocked_reason = None
            unlocked += 1

        if unlocked:
            await db.flush()
        return unlocked

    @staticmethod
    def _build_prompt(task: Task, project: Project) -> str:
        lines = [
            f"Project: {project.name}",
            f"Task: TASK-{task.task_number} — {task.title}",
        ]
        if task.description:
            lines.append(f"Description: {task.description}")
        if project.description:
            lines.append(f"Project context: {project.description}")
        if project.requirements:
            lines.append("Requirements:\n- " + "\n- ".join(project.requirements))
        if project.tech_stack:
            lines.append("Tech stack: " + ", ".join(project.tech_stack))
        if task.input_context:
            lines.append(f"Phase: {task.input_context.get('phase', 'build')}")
        title_lower = task.title.lower()
        phase = (task.input_context or {}).get("phase", "build")
        if phase in ("build", "design", "test") and any(
            k in title_lower for k in ("login", "page", "dashboard", "portal", "ui", "frontend", "build:", "design:")
        ):
            lines.append(
                "UI OUTPUT REQUIRED: Return html_deliverable (full standalone HTML+CSS of the working page) "
                "and preview_url if deployed. This is auto-screenshotted for launch verification."
            )
        lines.append(STRUCTURED_OUTPUT_INSTRUCTION.strip())
        return "\n\n".join(lines)

    @staticmethod
    async def execute_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        task: Task,
        agent: Agent,
        provider_keys: dict[str, str],
    ) -> dict:
        project_result = await db.execute(select(Project).where(Project.id == task.project_id))
        project = project_result.scalar_one()

        api_key = provider_keys[agent.ai_provider]
        now = datetime.now(timezone.utc)
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = now
        task.assigned_agent_id = agent.id
        agent.status = AgentStatus.WORKING
        agent.current_task_id = task.id
        agent.last_error = None
        await db.flush()

        task_id = task.id
        agent_id = agent.id
        agent_name = agent.name
        task_number = task.task_number
        project_id = project.id
        prompt = TaskExecutorService._build_prompt(task, project)
        system_prompt = agent.system_prompt or f"You are {agent.name}, a {agent.role}."
        run_id = uuid.uuid4()
        phase = (task.input_context or {}).get("phase", "build")
        max_tokens = 8192 if phase in ("build", "fix") else 4096

        await TaskExecutionLogService.start_run(
            db,
            org_id=org_id,
            project_id=project_id,
            task_id=task_id,
            agent_id=agent_id,
            agent_name=agent_name,
            run_id=run_id,
        )
        await TaskExecutionLogService.append(
            db, run_id, f"▶ {agent_name} ({agent.role}) started TASK-{task_number}", "info"
        )
        await TaskExecutionLogService.append(db, run_id, f"Phase: {phase}", "info")
        await TaskExecutionLogService.append(
            db, run_id, f"$ call {agent.ai_provider}/{agent.ai_model} (max_tokens={max_tokens})", "cmd"
        )

        llm_kwargs = {
            "provider": agent.ai_provider,
            "api_key": api_key,
            "model": agent.ai_model,
            "system_prompt": system_prompt,
            "task_context": prompt,
            "temperature": agent.temperature,
            "max_tokens": max_tokens,
            "run_id": str(run_id),
            "agent_id": str(agent_id),
            "task_id": str(task_id),
        }
        await db.commit()

        result = await _runtime.run_agent_task(**llm_kwargs)

        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one()
        agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_result.scalar_one()

        for line in result.logs:
            await TaskExecutionLogService.append(db, run_id, line, "info")
        if result.token_usage:
            await TaskExecutionLogService.append(
                db, run_id, f"✓ LLM response — {result.token_usage} tokens", "success"
            )

        agent.tokens_used += result.token_usage
        agent.current_task_id = None
        agent.status = AgentStatus.IDLE

        if result.status == RunStatus.COMPLETED and result.output.get("status") != "failed":
            await TaskExecutionLogService.append(db, run_id, "Validating workspace deliverables…", "info")
            passed, validation_msg, written = await TaskPipeline.apply_and_validate(
                db, org_id, project, task, result.output, run_id=run_id
            )
            result.output["workspace_files"] = written
            result.output["validation_message"] = validation_msg

            if passed:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                task.output = result.output
                task.failure_reason = None
                message = f"TASK-{task_number} completed by {agent_name} — {validation_msg}"
                event_type = "task.completed"
                await TaskExecutionLogService.append(db, run_id, f"✓ {validation_msg}", "success")
            else:
                task.status = TaskStatus.FAILED
                task.failure_reason = validation_msg
                agent.last_error = validation_msg
                message = f"TASK-{task_number} failed validation: {validation_msg[:200]}"
                event_type = "task.failed"
                await TaskExecutionLogService.append(db, run_id, f"✗ {validation_msg}", "error")

            if passed:
                project_result = await db.execute(select(Project).where(Project.id == project_id))
                project_for_shot = project_result.scalar_one()
                preview_host = None
                target_id = (project_for_shot.settings or {}).get("execution_target_id")
                if target_id:
                    from app.services.execution_target import ExecutionTargetService

                    target = await ExecutionTargetService.get(db, org_id, uuid.UUID(str(target_id)))
                    if target and target.host:
                        preview_host = target.host
                try:
                    from app.services.task_screenshot import TaskScreenshotService

                    await TaskExecutionLogService.append(db, run_id, "Capturing UI screenshot…", "info")
                    await TaskScreenshotService.capture_for_completed_task(
                        db,
                        task,
                        project_for_shot,
                        agent_name,
                        result.output,
                        preview_host=preview_host,
                    )
                    await TaskExecutionLogService.append(db, run_id, "Screenshot saved", "success")
                except Exception:
                    await TaskExecutionLogService.append(db, run_id, "Screenshot capture skipped", "info")
                agent.last_error = None
        else:
            err = result.error or str(result.output)
            task.status = TaskStatus.FAILED
            task.failure_reason = err
            agent.last_error = task.failure_reason
            message = f"TASK-{task_number} failed: {task.failure_reason[:200]}"
            event_type = "task.failed"
            await TaskExecutionLogService.append(db, run_id, f"✗ Agent failed: {err[:500]}", "error")

        final_status = "completed" if task.status == TaskStatus.COMPLETED else "failed"
        await TaskExecutionLogService.finish_run(
            db,
            run_id,
            status=final_status,
            token_usage=result.token_usage,
            error=task.failure_reason if task.status == TaskStatus.FAILED else None,
        )
        await TaskExecutionLogService.append(
            db, run_id, f"— Run finished ({final_status}) —", "info"
        )

        db.add(
            ActivityEvent(
                organization_id=org_id,
                project_id=project_id,
                task_id=task.id,
                event_type=event_type,
                message=message,
                event_metadata={
                    "agent_id": str(agent.id),
                    "agent_name": agent_name,
                    "token_usage": result.token_usage,
                    "run_id": str(run_id),
                },
            )
        )
        await db.flush()

        unlocked = 0
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            unlocked = await TaskExecutorService._unlock_dependents(db, project_id)

        return {
            "task_id": str(task.id),
            "task_number": task_number,
            "status": task.status.value,
            "agent": agent_name,
            "tokens": result.token_usage,
            "unlocked": unlocked,
        }

    @staticmethod
    async def run_pending(db: AsyncSession, org_id: uuid.UUID, limit: int = 3) -> list[dict]:
        provider_keys = await TaskExecutorService._configured_provider_keys(db, org_id)
        if not provider_keys:
            return []

        projects_result = await db.execute(
            select(Project.id).where(
                Project.organization_id == org_id,
                Project.status == ProjectStatus.ACTIVE,
            )
        )
        project_ids = [row[0] for row in projects_result.all()]
        if not project_ids:
            return []

        tasks_result = await db.execute(
            select(Task)
            .where(Task.project_id.in_(project_ids), Task.status == TaskStatus.READY)
            .order_by(Task.task_number.asc())
        )
        ready_tasks = list(tasks_result.scalars())

        results: list[dict] = []
        busy_agent_ids: set[uuid.UUID] = set()

        for task in ready_tasks:
            if len(results) >= limit:
                break
            agent = await TaskExecutorService._resolve_agent(db, org_id, task, provider_keys)
            if agent is None or agent.id in busy_agent_ids:
                continue
            busy_agent_ids.add(agent.id)
            try:
                results.append(await TaskExecutorService.execute_task(db, org_id, task, agent, provider_keys))
            except Exception as exc:
                logger.exception("Task execution failed for %s", task.id)
                task.status = TaskStatus.FAILED
                task.failure_reason = str(exc)
                agent.status = AgentStatus.IDLE
                agent.current_task_id = None
                agent.last_error = str(exc)
                await db.flush()
                results.append({"task_id": str(task.id), "status": "failed", "error": str(exc)})

        return results

    @staticmethod
    async def run_all_organizations(db: AsyncSession, limit_per_org: int = 1) -> list[dict]:
        orgs_result = await db.execute(
            select(Project.organization_id)
            .where(Project.status == ProjectStatus.ACTIVE)
            .distinct()
        )
        all_results: list[dict] = []
        for (org_id,) in orgs_result.all():
            all_results.extend(await TaskExecutorService.run_pending(db, org_id, limit=limit_per_org))
        return all_results
