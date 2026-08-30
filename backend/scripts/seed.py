"""Seed demo company with default AI employees."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models import (
    Agent,
    AgentStatus,
    Department,
    ExecutionTarget,
    ExecutionTargetStatus,
    ExecutionTargetType,
    Organization,
    OrganizationMember,
    OrgRole,
    Project,
    ProjectStatus,
    User,
)

DEMO_AGENTS = [
    {
        "name": "Alex",
        "role": "Project Manager",
        "department": "Management",
        "description": "Plans sprints, assigns work, monitors progress, escalates blockers.",
        "responsibilities": [
            "Understand project requirements",
            "Break requirements into tasks",
            "Create sprint plans",
            "Assign work and monitor progress",
            "Detect and escalate blockers",
        ],
        "skills": ["project management", "agile", "planning", "estimation"],
        "ai_provider": "openai",
        "ai_model": "gpt-4o",
        "system_prompt": "You are Alex, a senior Project Manager at an AI software company.",
    },
    {
        "name": "Sarah",
        "role": "UI/UX Designer",
        "department": "Design",
        "description": "Creates user flows, wireframes, and design specifications.",
        "responsibilities": ["User flows", "Wireframes", "UI specifications", "Design system"],
        "skills": ["figma", "ux", "ui design", "wireframing"],
        "ai_provider": "anthropic",
        "ai_model": "claude-sonnet-4-20250514",
        "system_prompt": "You are Sarah, a UI/UX Designer focused on clean, accessible interfaces.",
    },
    {
        "name": "David",
        "role": "Frontend Developer",
        "department": "Engineering",
        "description": "Builds React/Next.js components, pages, and frontend integrations.",
        "responsibilities": ["React/Next.js", "Components", "Pages", "Frontend integration"],
        "skills": ["react", "next.js", "typescript", "tailwind"],
        "ai_provider": "openai",
        "ai_model": "gpt-4o",
        "system_prompt": "You are David, a Frontend Developer specializing in React and Next.js.",
    },
    {
        "name": "Michael",
        "role": "Backend Developer",
        "department": "Engineering",
        "description": "Builds APIs, business logic, authentication, and backend services.",
        "responsibilities": ["APIs", "Business logic", "Authentication", "Backend services"],
        "skills": ["python", "fastapi", "postgresql", "rest apis"],
        "ai_provider": "openai",
        "ai_model": "gpt-4o",
        "system_prompt": "You are Michael, a Backend Developer specializing in Python and FastAPI.",
    },
    {
        "name": "Emma",
        "role": "Database Engineer",
        "department": "Engineering",
        "description": "Designs schemas, migrations, indexes, and ensures data integrity.",
        "responsibilities": ["Database schema", "Migrations", "Indexes", "Queries"],
        "skills": ["postgresql", "sql", "migrations", "indexing"],
        "ai_provider": "openai",
        "ai_model": "gpt-4o",
        "system_prompt": "You are Emma, a Database Engineer focused on PostgreSQL.",
    },
    {
        "name": "Daniel",
        "role": "QA Engineer",
        "department": "Quality",
        "description": "Creates test plans and runs unit, integration, and E2E tests.",
        "responsibilities": ["Test plans", "Unit tests", "Integration tests", "E2E tests"],
        "skills": ["pytest", "playwright", "testing", "qa"],
        "ai_provider": "anthropic",
        "ai_model": "claude-sonnet-4-20250514",
        "system_prompt": "You are Daniel, a QA Engineer ensuring software quality.",
    },
    {
        "name": "Olivia",
        "role": "Security Engineer",
        "department": "Security",
        "description": "Reviews security, authentication, authorization, and vulnerabilities.",
        "responsibilities": ["Security review", "Auth review", "Vulnerability detection"],
        "skills": ["security", "owasp", "authentication", "authorization"],
        "ai_provider": "anthropic",
        "ai_model": "claude-sonnet-4-20250514",
        "system_prompt": "You are Olivia, a Security Engineer focused on secure software.",
    },
    {
        "name": "James",
        "role": "DevOps Engineer",
        "department": "Operations",
        "description": "Manages Docker, CI/CD, infrastructure, and deployments.",
        "responsibilities": ["Docker", "CI/CD", "Infrastructure", "Deployment"],
        "skills": ["docker", "kubernetes", "github actions", "ci/cd"],
        "ai_provider": "openai",
        "ai_model": "gpt-4o",
        "system_prompt": "You are James, a DevOps Engineer focused on reliable deployments.",
    },
    {
        "name": "Code Review Agent",
        "role": "Code Reviewer",
        "department": "Engineering",
        "description": "Reviews pull requests for architecture, quality, security, and tests.",
        "responsibilities": ["Review PRs", "Check architecture", "Check quality and security"],
        "skills": ["code review", "architecture", "best practices"],
        "ai_provider": "anthropic",
        "ai_model": "claude-sonnet-4-20250514",
        "system_prompt": "You are a Code Review Agent ensuring high code quality.",
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "ceo@demo.com"))
        if result.scalar_one_or_none():
            print("Demo data already seeded.")
            return

        user = User(
            email="ceo@demo.com",
            hashed_password=get_password_hash("demo1234"),
            full_name="Demo CEO",
        )
        db.add(user)
        await db.flush()

        org = Organization(
            name="Demo AI Company",
            slug="demo-ai-company",
            description="Default demo organization with pre-configured AI employees.",
        )
        db.add(org)
        await db.flush()

        db.add(OrganizationMember(organization_id=org.id, user_id=user.id, role=OrgRole.OWNER))
        await db.flush()

        default_target = ExecutionTarget(
            organization_id=org.id,
            name="Raspberry Pi — Local Projects",
            target_type=ExecutionTargetType.LOCAL,
            workspace_path="/home/aividmini/PS",
            is_default=True,
            status=ExecutionTargetStatus.CONNECTED,
        )
        db.add(default_target)
        await db.flush()

        dept_map: dict[str, Department] = {}
        for agent_data in DEMO_AGENTS:
            dept_name = agent_data["department"]
            if dept_name not in dept_map:
                dept = Department(organization_id=org.id, name=dept_name)
                db.add(dept)
                await db.flush()
                dept_map[dept_name] = dept

        alex_id = None
        backend_agent_id = None
        for agent_data in DEMO_AGENTS:
            dept_name = agent_data["department"]
            dept = dept_map[dept_name]
            agent = Agent(
                organization_id=org.id,
                department_id=dept.id,
                name=agent_data["name"],
                role=agent_data["role"],
                description=agent_data["description"],
                responsibilities=agent_data["responsibilities"],
                skills=agent_data["skills"],
                ai_provider=agent_data["ai_provider"],
                ai_model=agent_data["ai_model"],
                system_prompt=agent_data["system_prompt"],
            )
            db.add(agent)
            await db.flush()
            if agent.name == "Alex":
                alex_id = agent.id
            if agent.role == "Backend Developer":
                backend_agent_id = agent.id

        if backend_agent_id:
            result = await db.execute(select(Agent).where(Agent.id == backend_agent_id))
            backend = result.scalar_one()
            backend.status = AgentStatus.FAILED
            backend.last_error = (
                "OpenAI API error 429: insufficient quota / billing balance exhausted. "
                "Add credits or switch provider before retrying."
            )
            backend.tokens_used = 95000
            backend.max_token_budget = 100000

        if alex_id:
            result = await db.execute(
                select(Agent).where(Agent.organization_id == org.id, Agent.name != "Alex")
            )
            for agent in result.scalars():
                agent.manager_id = alex_id

        project = Project(
            organization_id=org.id,
            name="Customer Support Platform",
            slug="customer-support-platform",
            description="Customer support platform with login, ticket management, SLA tracking, and admin controls.",
            goals=["Launch MVP customer support platform", "Achieve 99.9% uptime"],
            requirements=[
                "Customer login",
                "Agent login",
                "Ticket management",
                "SLA tracking",
                "Notifications",
                "Dashboard",
                "Reports",
                "Admin controls",
            ],
            tech_stack=["Next.js", "FastAPI", "PostgreSQL", "Redis", "Docker"],
            status=ProjectStatus.PLANNING,
        )
        db.add(project)
        await db.commit()
        print("Demo data seeded successfully.")
        print("  Login: ceo@demo.com / demo1234")


if __name__ == "__main__":
    asyncio.run(seed())
