from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, ai_providers, auth, dashboard, execution_targets, organizations, projects, uploads
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_thread = None
    if settings.orchestrator_enabled:
        from app.orchestrator.worker import start_orchestrator_thread

        worker_thread = start_orchestrator_thread()
        logger.info("Orchestrator background worker enabled (isolated thread)")
    yield
    if worker_thread and worker_thread.is_alive():
        logger.info("Orchestrator worker shutting down with process")


app = FastAPI(
    title="AI Engineering OS (AIOS)",
    description="Virtual software development company powered by AI agents",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(execution_targets.router, prefix="/api")
app.include_router(ai_providers.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ai-company-os", "version": "0.1.0"}
