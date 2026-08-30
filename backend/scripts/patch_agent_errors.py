"""Patch demo agents with API/balance error state on existing DB."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models import Agent, AgentStatus


async def patch():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Agent).where(Agent.role == "Backend Developer").limit(1)
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            print("No Backend Developer agent found — skip.")
            return
        agent.status = AgentStatus.FAILED
        agent.last_error = (
            "OpenAI API error 429: insufficient quota / billing balance exhausted. "
            "Add credits or switch provider before retrying."
        )
        agent.tokens_used = 95000
        agent.max_token_budget = 100000
        await db.commit()
        print(f"Patched agent: {agent.name}")


if __name__ == "__main__":
    asyncio.run(patch())
