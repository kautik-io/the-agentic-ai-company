"""Rule-based project planner — auto-generates epics, features, and aligned tasks."""

from __future__ import annotations

import re
from typing import Any


def _slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_-]+", "-", s).strip("-") or "item"


def _pick_role(requirement: str, phase: str) -> str:
    req = requirement.lower()
    if phase == "design":
        return "UI/UX Designer"
    if phase == "test":
        return "QA Engineer"
    if phase == "fix":
        return "Backend Developer"
    if any(k in req for k in ("ui", "page", "dashboard", "login", "frontend", "portal")):
        return "Frontend Developer"
    if any(k in req for k in ("api", "backend", "database", "schema", "auth")):
        return "Backend Developer"
    if any(k in req for k in ("deploy", "docker", "infra", "ci")):
        return "DevOps Engineer"
    if any(k in req for k in ("security", "audit")):
        return "Security Engineer"
    return "Backend Developer"


def _feature_tasks(requirement: str, epic_title: str) -> list[dict[str, Any]]:
    """Build → test → fix chain per requirement."""
    req_short = requirement[:80]
    build_title = f"Build: {req_short}"
    design_title = f"Design: {req_short}"
    test_title = f"Test: {req_short}"
    fix_title = f"Fix: {req_short} issues"

    return [
        {
            "title": design_title,
            "description": f"Design spec and acceptance criteria for {requirement}.",
            "epic": epic_title,
            "feature": requirement,
            "agent_role": _pick_role(requirement, "design"),
            "priority": "high",
            "phase": "design",
            "estimated_minutes": 120,
            "depends_on": [],
            "task_type": "mini",
        },
        {
            "title": build_title,
            "description": f"Implement {requirement}.",
            "epic": epic_title,
            "feature": requirement,
            "agent_role": _pick_role(requirement, "build"),
            "priority": "high",
            "phase": "build",
            "estimated_minutes": 360,
            "depends_on": [design_title],
            "task_type": "build",
        },
        {
            "title": test_title,
            "description": f"Verify {requirement} meets acceptance criteria.",
            "epic": epic_title,
            "feature": requirement,
            "agent_role": _pick_role(requirement, "test"),
            "priority": "medium",
            "phase": "test",
            "estimated_minutes": 120,
            "depends_on": [build_title],
            "task_type": "mini",
        },
        {
            "title": fix_title,
            "description": f"Resolve defects found during testing of {requirement}.",
            "epic": epic_title,
            "feature": requirement,
            "agent_role": _pick_role(requirement, "fix"),
            "priority": "high",
            "phase": "fix",
            "estimated_minutes": 90,
            "depends_on": [test_title],
            "task_type": "fix",
        },
    ]


def generate_plan(
    name: str,
    description: str | None,
    goals: list[str],
    requirements: list[str],
    tech_stack: list[str],
) -> dict[str, Any]:
    """Return a draft plan stored in project.settings until auto-approval."""
    reqs = [r.strip() for r in requirements if r and r.strip()]
    if not reqs and description:
        # Split NL description into rough requirements
        parts = re.split(r"[.\n;]+", description)
        reqs = [p.strip() for p in parts if len(p.strip()) > 8][:8]
    if not reqs:
        reqs = ["Core MVP feature", "User authentication", "Admin dashboard"]

    epics_map: dict[str, str] = {}
    features: list[dict[str, str]] = []
    tasks: list[dict[str, Any]] = []

    # Foundation epic
    foundation = "Foundation & Setup"
    epics_map[foundation] = foundation
    features.append({"epic": foundation, "title": "Project scaffolding", "slug": "project-scaffolding"})
    tasks.extend([
        {
            "title": "Initialize project repository and workspace structure",
            "description": f"Scaffold {name} with {', '.join(tech_stack) or 'default stack'}.",
            "epic": foundation,
            "feature": "Project scaffolding",
            "agent_role": "Backend Developer",
            "priority": "high",
            "phase": "build",
            "estimated_minutes": 180,
            "depends_on": [],
            "task_type": "build",
        },
        {
            "title": "Configure CI/CD and deployment pipeline",
            "description": "Set up build, test, and deploy automation.",
            "epic": foundation,
            "feature": "Project scaffolding",
            "agent_role": "DevOps Engineer",
            "priority": "medium",
            "phase": "build",
            "estimated_minutes": 240,
            "depends_on": ["Initialize project repository and workspace structure"],
            "task_type": "build",
        },
    ])

    # One epic per requirement cluster (max 5 epics)
    for req in reqs[:6]:
        epic_title = req if len(req) < 40 else req[:37] + "..."
        if epic_title not in epics_map:
            epics_map[epic_title] = epic_title
        features.append({"epic": epic_title, "title": req, "slug": _slug(req)})
        tasks.extend(_feature_tasks(req, epic_title))

    # Goals epic
    if goals:
        goals_epic = "Project Goals"
        epics_map[goals_epic] = goals_epic
        for i, goal in enumerate(goals[:5]):
            feat = f"Goal {i + 1}"
            features.append({"epic": goals_epic, "title": feat, "slug": _slug(goal)})
            tasks.append({
                "title": f"Deliver goal: {goal}",
                "description": goal,
                "epic": goals_epic,
                "feature": feat,
                "agent_role": "Project Manager",
                "priority": "medium",
                "phase": "build",
                "estimated_minutes": 240,
                "depends_on": [],
                "task_type": "build",
            })

    # Final launch review (blocked until builds complete)
    launch_epic = "Launch & Deploy"
    epics_map[launch_epic] = launch_epic
    features.append({"epic": launch_epic, "title": "Launch review", "slug": "launch-review"})
    build_tasks = [t["title"] for t in tasks if t.get("phase") == "build"]
    tasks.append({
        "title": "Launch review — verify build & go live",
        "description": "Final check after build tasks are verified, before deploy goes live.",
        "epic": launch_epic,
        "feature": "Launch review",
        "agent_role": "Project Manager",
        "priority": "critical",
        "phase": "approval",
        "estimated_minutes": 30,
        "depends_on": build_tasks[:3] if build_tasks else [],
        "task_type": "approval",
    })

    epics = [{"title": t, "description": f"Epic: {t}"} for t in epics_map.values()]

    return {
        "summary": f"Auto-planned {len(tasks)} tasks across {len(epics)} epics for {name}.",
        "epics": epics,
        "features": features,
        "tasks": tasks,
        "manual_tasks": [],
    }
