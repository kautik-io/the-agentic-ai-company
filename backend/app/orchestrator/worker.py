from __future__ import annotations

import asyncio
import logging
import threading

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.services.task_executor import TaskExecutorService

logger = logging.getLogger(__name__)

_worker_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
WorkerSessionLocal = async_sessionmaker(_worker_engine, class_=AsyncSession, expire_on_commit=False)


async def orchestrator_loop() -> None:
    """Poll for ready tasks and dispatch them to idle agents."""
    await asyncio.sleep(5)
    logger.info("Orchestrator worker started (interval=%ss)", settings.orchestrator_poll_seconds)
    while True:
        try:
            async with WorkerSessionLocal() as db:
                results = await TaskExecutorService.run_all_organizations(db, limit_per_org=1)
                await db.commit()
                if results:
                    logger.info("Orchestrator executed %s task(s): %s", len(results), results)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Orchestrator loop error")
        await asyncio.sleep(settings.orchestrator_poll_seconds)


def _run_orchestrator_in_thread() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(orchestrator_loop())
    finally:
        loop.run_until_complete(_worker_engine.dispose())
        loop.close()


def start_orchestrator_thread() -> threading.Thread:
    """Run orchestrator on its own event loop and DB pool so API stays responsive."""
    thread = threading.Thread(target=_run_orchestrator_in_thread, name="orchestrator-worker", daemon=True)
    thread.start()
    return thread
