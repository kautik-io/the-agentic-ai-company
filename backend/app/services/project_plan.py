from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityEvent,
    Agent,
    Epic,
    Feature,
    Project,
    ProjectStatus,
    Sprint,
    SprintStatus,
    Task,
    TaskPriority,
    TaskStatus,
)
from app.schemas.plan import ManualTaskAdd
from app.services.ai_provider import AiProviderService
from app.services.logic_graph import epic_graph, feature_graph
from app.services.project import EpicService, ProjectService, _project_slug
from app.services.project_planner import generate_plan


class ProjectPlanService:
    @staticmethod
    def _settings(project: Project) -> dict:
        return dict(project.settings or {})

    @staticmethod
    def planning_status(project: Project) -> str:
        return ProjectPlanService._settings(project).get("planning_status", "none")

    @staticmethod
    def get_draft(project: Project) -> dict | None:
        return ProjectPlanService._settings(project).get("plan_draft")

    @staticmethod
    async def attach_draft(
        db: AsyncSession,
        org_id: uuid.UUID,
        project: Project,
        user_id: uuid.UUID,
        goals: list[str],
        requirements: list[str],
    ) -> dict:
        draft = generate_plan(
            project.name,
            project.description,
            goals,
            requirements,
            project.tech_stack or [],
        )
        settings = ProjectPlanService._settings(project)
        settings["planning_status"] = "pending_approval"
        settings["plan_draft"] = draft
        settings["plan_summary"] = draft["summary"]
        project.settings = settings
        project.status = ProjectStatus.PLANNING
        await db.flush()

        db.add(
            ActivityEvent(
                organization_id=org_id,
                project_id=project.id,
                user_id=user_id,
                event_type="plan.created",
                message=f"Auto-plan ready: {len(draft['tasks'])} tasks — PM pipeline starting",
                event_metadata={"task_count": len(draft["tasks"]), "epic_count": len(draft["epics"])},
            )
        )
        await db.flush()
        return draft

    @staticmethod
    async def get_plan_response(db: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID) -> dict | None:
        project = await ProjectService.get(db, org_id, project_id)
        if project is None:
            return None
        settings = ProjectPlanService._settings(project)
        draft = settings.get("plan_draft") or {"epics": [], "features": [], "tasks": [], "manual_tasks": []}
        all_tasks = list(draft.get("tasks", [])) + list(draft.get("manual_tasks", []))
        return {
            "project_id": project.id,
            "planning_status": settings.get("planning_status", "none"),
            "summary": settings.get("plan_summary"),
            "epics": draft.get("epics", []),
            "features": draft.get("features", []),
            "tasks": draft.get("tasks", []),
            "manual_tasks": draft.get("manual_tasks", []),
            "total_tasks": len(all_tasks),
            "approved_at": settings.get("plan_approved_at"),
        }

    @staticmethod
    async def add_manual_task(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ManualTaskAdd,
    ) -> dict | None:
        project = await ProjectService.get(db, org_id, project_id)
        if project is None:
            return None

        status = ProjectPlanService.planning_status(project)
        item = {
            "title": data.title,
            "description": data.description,
            "epic": data.epic or "Manual additions",
            "feature": data.feature or data.title,
            "agent_role": data.agent_role,
            "priority": data.priority,
            "phase": "build",
            "estimated_minutes": 120,
            "depends_on": [],
            "task_type": "manual",
            "manual": True,
        }

        if status == "pending_approval":
            settings = ProjectPlanService._settings(project)
            draft = deepcopy(settings.get("plan_draft") or {"epics": [], "features": [], "tasks": [], "manual_tasks": []})
            draft.setdefault("manual_tasks", []).append(item)
            if item["epic"] not in {e["title"] for e in draft.get("epics", [])}:
                draft.setdefault("epics", []).append({"title": item["epic"], "description": "Manually added work"})
            draft.setdefault("features", []).append({
                "epic": item["epic"],
                "title": item["feature"],
                "slug": _project_slug(item["feature"]),
            })
            settings["plan_draft"] = draft
            project.settings = settings
            await db.flush()
            db.add(
                ActivityEvent(
                    organization_id=org_id,
                    project_id=project.id,
                    user_id=user_id,
                    event_type="plan.manual_task_added",
                    message=f"Manual task added to plan: {data.title}",
                )
            )
            await db.flush()
            return await ProjectPlanService.get_plan_response(db, org_id, project_id)

        # After approval — create real task immediately
        from app.schemas.project import TaskCreate
        from app.services.project import TaskService

        epic_id = None
        feature_id = None
        epics = await EpicService.list(db, project_id)
        for epic in epics:
            if epic.title == item["epic"]:
                epic_id = epic.id
                break

        task = await TaskService.create(
            db,
            org_id,
            project_id,
            user_id,
            TaskCreate(
                title=data.title,
                description=data.description,
                epic_id=epic_id,
                priority=data.priority,
            ),
        )
        return {"task_id": str(task.id), "planning_status": status}

    @staticmethod
    async def regenerate(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict | None:
        project = await ProjectService.get(db, org_id, project_id)
        if project is None:
            return None
        if ProjectPlanService.planning_status(project) == "approved":
            raise ValueError("Plan already approved — cannot regenerate")

        manual = []
        draft = ProjectPlanService.get_draft(project)
        if draft:
            manual = list(draft.get("manual_tasks", []))

        new_draft = generate_plan(
            project.name,
            project.description,
            project.goals or [],
            project.requirements or [],
            project.tech_stack or [],
        )
        new_draft["manual_tasks"] = manual
        settings = ProjectPlanService._settings(project)
        settings["planning_status"] = "pending_approval"
        settings["plan_draft"] = new_draft
        settings["plan_summary"] = new_draft["summary"]
        project.settings = settings
        await db.flush()
        return await ProjectPlanService.get_plan_response(db, org_id, project_id)

    @staticmethod
    async def repair_stale_approval_tasks(db: AsyncSession, project_id: uuid.UUID) -> None:
        """Fix launch-review tasks left blocked after plan was already approved."""
        result = await db.execute(
            select(Task).where(
                Task.project_id == project_id,
                Task.status == TaskStatus.BLOCKED,
                Task.blocked_reason == "Awaiting plan verification after auto-planning",
            )
        )
        changed = False
        for task in result.scalars():
            if task.dependencies:
                task.status = TaskStatus.BACKLOG
                task.blocked_reason = None
            else:
                task.status = TaskStatus.WAITING
                task.blocked_reason = "Build complete — ready for launch review"
            changed = True
        if changed:
            await db.flush()

    @staticmethod
    async def approve(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        project = await ProjectService.get(db, org_id, project_id)
        if project is None:
            raise ValueError("Project not found")

        settings = ProjectPlanService._settings(project)
        if settings.get("planning_status") == "approved":
            raise ValueError("Plan already approved")

        draft = settings.get("plan_draft")
        if not draft:
            raise ValueError("No plan draft to approve")

        agents_result = await db.execute(select(Agent).where(Agent.organization_id == org_id))
        configured = await AiProviderService.configured_providers(db, org_id)
        agents_list = list(agents_result.scalars())
        agents_by_role: dict[str, uuid.UUID] = {}
        for agent in agents_list:
            role = agent.role
            if role not in agents_by_role:
                agents_by_role[role] = agent.id
            elif agent.ai_provider in configured:
                existing = next(a for a in agents_list if a.id == agents_by_role[role])
                if existing.ai_provider not in configured:
                    agents_by_role[role] = agent.id

        # Remove starter epic/feature if still the only ones
        existing_epics = await EpicService.list(db, project_id)
        if len(existing_epics) == 1 and existing_epics[0].title == "Phase 1 — Planning":
            starter_id = existing_epics[0].id
            await db.execute(delete(Feature).where(Feature.epic_id == starter_id))
            await db.execute(delete(Epic).where(Epic.id == starter_id))
            await db.flush()

        epic_cache: dict[str, uuid.UUID] = {}
        feature_cache: dict[str, uuid.UUID] = {}
        task_by_title: dict[str, uuid.UUID] = {}

        for epic_spec in draft.get("epics", []):
            title = epic_spec["title"]
            epic = Epic(
                project_id=project_id,
                title=title,
                description=epic_spec.get("description"),
                logic_graph=epic_graph(title, epic_spec.get("description")),
            )
            db.add(epic)
            await db.flush()
            epic_cache[title] = epic.id

        for feat_spec in draft.get("features", []):
            epic_title = feat_spec["epic"]
            if epic_title not in epic_cache:
                continue
            feat_key = f"{epic_title}::{feat_spec['title']}"
            if feat_key in feature_cache:
                continue
            slug = feat_spec.get("slug") or _project_slug(feat_spec["title"])
            feature = Feature(
                epic_id=epic_cache[epic_title],
                title=feat_spec["title"],
                slug=slug,
                description=f"Feature: {feat_spec['title']}",
                logic_graph=feature_graph(feat_spec["title"], None),
            )
            db.add(feature)
            await db.flush()
            feature_cache[feat_key] = feature.id

        all_task_specs = list(draft.get("tasks", [])) + list(draft.get("manual_tasks", []))
        task_number = await db.execute(
            select(func.coalesce(func.max(Task.task_number), 0)).where(Task.project_id == project_id)
        )
        next_num = (task_number.scalar() or 0) + 1
        created = 0

        for spec in all_task_specs:
            epic_id = epic_cache.get(spec["epic"])
            feat_key = f"{spec['epic']}::{spec['feature']}"
            feature_id = feature_cache.get(feat_key)

            dep_ids: list[str] = []
            for dep_title in spec.get("depends_on", []):
                if dep_title in task_by_title:
                    dep_ids.append(str(task_by_title[dep_title]))

            has_deps = len(dep_ids) > 0
            phase = spec.get("phase", "build")
            blocked_reason: str | None = None
            if phase == "approval":
                # Plan draft is already approved here — this task is launch sign-off after builds.
                if has_deps:
                    status = TaskStatus.BACKLOG
                else:
                    status = TaskStatus.WAITING
                    blocked_reason = "Build complete — ready for launch review"
            elif not has_deps:
                status = TaskStatus.READY
            else:
                status = TaskStatus.BACKLOG

            agent_id = agents_by_role.get(spec.get("agent_role", "Backend Developer"))

            task = Task(
                project_id=project_id,
                epic_id=epic_id,
                feature_id=feature_id,
                assigned_agent_id=agent_id,
                task_number=next_num,
                title=spec["title"],
                description=spec.get("description"),
                priority=TaskPriority(spec.get("priority", "medium")),
                status=status,
                estimated_minutes=spec.get("estimated_minutes"),
                dependencies=dep_ids,
                blocked_reason=blocked_reason,
                input_context={"task_type": spec.get("task_type", "build"), "phase": phase},
            )
            db.add(task)
            await db.flush()
            task_by_title[spec["title"]] = task.id
            next_num += 1
            created += 1

        sprint = Sprint(
            project_id=project_id,
            name="Sprint 1 — Initial delivery",
            goal="Execute approved plan",
            status=SprintStatus.PLANNED,
        )
        db.add(sprint)
        await db.flush()

        settings["planning_status"] = "approved"
        settings["plan_approved_at"] = datetime.now(timezone.utc).isoformat()
        settings["plan_approved_by"] = str(user_id)
        project.settings = settings
        project.status = ProjectStatus.ACTIVE
        await db.flush()

        await ProjectService.refresh_project_graph(db, org_id, project_id)

        db.add(
            ActivityEvent(
                organization_id=org_id,
                project_id=project.id,
                user_id=user_id,
                event_type="plan.approved",
                message=f"Plan approved — {created} tasks created, automated pipeline started",
                event_metadata={"tasks_created": created},
            )
        )
        await db.flush()

        return {
            "planning_status": "approved",
            "tasks_created": created,
            "epics_created": len(epic_cache),
            "features_created": len(feature_cache),
            "message": f"Plan approved. {created} tasks aligned and ready.",
        }

    @staticmethod
    async def reject(
        db: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str | None = None,
    ) -> dict | None:
        project = await ProjectService.get(db, org_id, project_id)
        if project is None:
            return None
        settings = ProjectPlanService._settings(project)
        settings["planning_status"] = "rejected"
        if reason:
            settings["plan_rejection_reason"] = reason
        project.settings = settings
        await db.flush()
        db.add(
            ActivityEvent(
                organization_id=org_id,
                project_id=project.id,
                user_id=user_id,
                event_type="plan.rejected",
                message=reason or "Plan rejected — regenerate or add manual tasks",
            )
        )
        await db.flush()
        return await ProjectPlanService.get_plan_response(db, org_id, project_id)
