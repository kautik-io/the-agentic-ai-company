"""Seed demo tasks for Customer Support Platform (run on existing DB)."""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models import Agent, Epic, Feature, Project, Task, TaskPriority, TaskStatus

DEMO_TASKS = [
    # Epic: Authentication
    {
        "epic": "Authentication",
        "feature": "User Login",
        "title": "Create database schema for users and sessions",
        "description": "Design PostgreSQL schema for customers, agents, roles, sessions.",
        "agent_role": "Database Engineer",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.READY,
        "estimated_minutes": 240,
        "depends_on": [],
    },
    {
        "epic": "Authentication",
        "feature": "User Login",
        "title": "Create authentication API",
        "description": "JWT login, logout, refresh tokens for customer and agent roles.",
        "agent_role": "Backend Developer",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 480,
        "depends_on": ["Create database schema for users and sessions"],
    },
    {
        "epic": "Authentication",
        "feature": "User Login",
        "title": "Create login UI",
        "description": "Customer and agent login pages with form validation.",
        "agent_role": "Frontend Developer",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 360,
        "depends_on": ["Create authentication API"],
    },
    {
        "epic": "Authentication",
        "feature": "User Login",
        "title": "Test authentication flow",
        "description": "Unit and integration tests for login, logout, token refresh.",
        "agent_role": "QA Engineer",
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 180,
        "depends_on": ["Create login UI"],
    },
    {
        "epic": "Authentication",
        "feature": "User Login",
        "title": "Fix token refresh regression",
        "description": "Refresh token endpoint returns 500 after schema migration.",
        "agent_role": "Backend Developer",
        "priority": TaskPriority.CRITICAL,
        "status": TaskStatus.FAILED,
        "estimated_minutes": 120,
        "depends_on": ["Create authentication API"],
        "failure_reason": "Migration V2 failed: column 'refresh_token_hash' already exists. Retry after rollback.",
    },
    # Epic: Ticket Management
    {
        "epic": "Ticket Management",
        "feature": "Ticket CRUD",
        "title": "Design ticket database schema",
        "description": "Tickets, statuses, priorities, assignments, comments.",
        "agent_role": "Database Engineer",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 180,
        "depends_on": ["Create database schema for users and sessions"],
    },
    {
        "epic": "Ticket Management",
        "feature": "Ticket CRUD",
        "title": "Implement ticket API",
        "description": "CRUD endpoints for tickets with filtering and pagination.",
        "agent_role": "Backend Developer",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 600,
        "depends_on": ["Design ticket database schema"],
    },
    {
        "epic": "Ticket Management",
        "feature": "Ticket CRUD",
        "title": "Build ticket dashboard UI",
        "description": "Agent ticket list, detail view, status updates.",
        "agent_role": "Frontend Developer",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.BLOCKED,
        "estimated_minutes": 480,
        "depends_on": ["Implement ticket API"],
        "blocked_reason": "API response format does not match UI specification. Waiting on Backend Developer.",
    },
    {
        "epic": "Ticket Management",
        "feature": "Ticket CRUD",
        "title": "QA ticket management",
        "description": "Test ticket creation, assignment, status transitions.",
        "agent_role": "QA Engineer",
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 240,
        "depends_on": ["Build ticket dashboard UI"],
    },
    # Epic: SLA & Notifications
    {
        "epic": "SLA & Notifications",
        "feature": "SLA Tracking",
        "title": "Implement SLA engine",
        "description": "SLA rules, breach detection, escalation timers.",
        "agent_role": "Backend Developer",
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 420,
        "depends_on": ["Implement ticket API"],
    },
    {
        "epic": "SLA & Notifications",
        "feature": "Notifications",
        "title": "Build notification service",
        "description": "Email and in-app notifications for ticket updates and SLA breaches.",
        "agent_role": "Backend Developer",
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 360,
        "depends_on": ["Implement SLA engine"],
    },
    # Design & Security
    {
        "epic": "Authentication",
        "feature": "User Login",
        "title": "Design login and dashboard wireframes",
        "description": "UI/UX specs for login, agent dashboard, customer portal.",
        "agent_role": "UI/UX Designer",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.IN_PROGRESS,
        "estimated_minutes": 300,
        "depends_on": [],
    },
    {
        "epic": "Authentication",
        "feature": "User Login",
        "title": "Security review — authentication",
        "description": "Review auth flow, JWT handling, password policies.",
        "agent_role": "Security Engineer",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.BACKLOG,
        "estimated_minutes": 120,
        "depends_on": ["Create authentication API"],
    },
]


async def seed_tasks():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Project).where(Project.slug == "customer-support-platform")
        )
        project = result.scalar_one_or_none()
        if not project:
            print("Customer Support Platform project not found. Run seed.py first.")
            return

        count_result = await db.execute(
            select(func.count(Task.id)).where(Task.project_id == project.id)
        )
        existing = count_result.scalar() or 0
        if existing >= len(DEMO_TASKS):
            print(f"Project already has {existing} tasks. Skipping.")
            return

        # Remove the single test task if it's the only one
        if existing == 1:
            old = await db.execute(
                select(Task).where(Task.project_id == project.id, Task.title == "Implement login page")
            )
            test_task = old.scalar_one_or_none()
            if test_task:
                await db.delete(test_task)
                await db.flush()
                print("Removed test task 'Implement login page'.")

        agents_result = await db.execute(
            select(Agent).where(Agent.organization_id == project.organization_id)
        )
        agents_by_role = {a.role: a.id for a in agents_result.scalars()}

        epic_cache: dict[str, uuid.UUID] = {}
        feature_cache: dict[str, uuid.UUID] = {}
        task_by_title: dict[str, uuid.UUID] = {}
        task_number = 0

        for spec in DEMO_TASKS:
            epic_title = spec["epic"]
            if epic_title not in epic_cache:
                epic = Epic(project_id=project.id, title=epic_title, description=f"Epic: {epic_title}")
                db.add(epic)
                await db.flush()
                epic_cache[epic_title] = epic.id

            feat_key = f"{epic_title}::{spec['feature']}"
            if feat_key not in feature_cache:
                feature = Feature(
                    epic_id=epic_cache[epic_title],
                    title=spec["feature"],
                    description=f"Feature: {spec['feature']}",
                )
                db.add(feature)
                await db.flush()
                feature_cache[feat_key] = feature.id

            task_number += 1
            agent_id = agents_by_role.get(spec["agent_role"])

            dep_ids: list[str] = []
            for dep_title in spec["depends_on"]:
                if dep_title in task_by_title:
                    dep_ids.append(str(task_by_title[dep_title]))

            task = Task(
                project_id=project.id,
                epic_id=epic_cache[epic_title],
                feature_id=feature_cache[feat_key],
                assigned_agent_id=agent_id,
                task_number=task_number,
                title=spec["title"],
                description=spec["description"],
                priority=spec["priority"],
                status=spec["status"],
                estimated_minutes=spec["estimated_minutes"],
                dependencies=dep_ids,
                blocked_reason=spec.get("blocked_reason"),
                failure_reason=spec.get("failure_reason"),
            )
            db.add(task)
            await db.flush()
            task_by_title[spec["title"]] = task.id

        await db.commit()
        print(f"Seeded {task_number} demo tasks for Customer Support Platform.")


if __name__ == "__main__":
    asyncio.run(seed_tasks())
