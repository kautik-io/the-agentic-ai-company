# AI Company OS

A production-ready web application where AI agents operate as employees in a virtual software development company. You act as CEO/CTO — hire agents, create projects, assign tasks, and monitor delivery in real time.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (optional, for local frontend dev)
- Python 3.12+ (optional, for local backend dev)

### Run with Docker (recommended script)

```bash
cp .env.example .env
./scripts/dev.sh full      # first time: build + migrate + seed
./scripts/dev.sh rebuild   # after code changes
./scripts/dev.sh restart   # quick restart
./scripts/dev.sh status    # check URLs + health
```

Or manually:

```bash
docker compose up --build
```

Services (ports may be 3001/8001 if 3000/8000 are in use):

| Service   | URL                        |
|-----------|----------------------------|
| Frontend  | http://localhost:3001      |
| Backend   | http://localhost:8001      |
| API Docs  | http://localhost:8001/api/docs |

### Seed Demo Data

```bash
./scripts/dev.sh seed
./scripts/dev.sh seed-tasks
```

Or:

```bash
docker compose exec backend python scripts/seed.py
docker compose exec backend python scripts/seed_tasks.py
```

Demo login: **ceo@demo.com** / **demo1234**

Includes 9 pre-configured AI employees (Alex PM, Sarah Designer, David Frontend, Michael Backend, etc.) and a sample project.

### Local Development (without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Start PostgreSQL and Redis locally, then:
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for system design, event-driven principles, and MVP phase plan.

## MVP Progress

| Phase | Feature                    | Status      |
|-------|----------------------------|-------------|
| 1     | Auth + Organizations       | ✅ Done     |
| 2     | Projects + Agents + Tasks  | ✅ Done     |
| 3     | Sprint + Kanban DnD        | 🔜 Next     |
| 4     | Agent Execution Engine     | 🔜 Planned  |
| 5     | Orchestrator               | 🔜 Scaffold |
| 6–13  | See ARCHITECTURE.md        | 🔜 Planned  |

## Key Features (Current)

- User registration and JWT authentication
- Multi-tenant organizations with RBAC
- AI employee hiring with full configuration (model, skills, permissions)
- Project creation (manual + natural language entry point)
- Task management with status workflow
- Executive dashboard with live stats
- Activity event logging
- WebSocket endpoint (Phase 7 will wire live updates)
- Demo company with 9 default agents

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — System design
- [API.md](./API.md) — REST API reference
- [DATABASE.md](./DATABASE.md) — Schema documentation
- [AGENTS.md](./AGENTS.md) — Agent runtime guide
- [WORKFLOWS.md](./WORKFLOWS.md) — Workflow engine
- [DEPLOYMENT.md](./DEPLOYMENT.md) — Production deployment
- [SECURITY.md](./SECURITY.md) — Security practices

## Project Structure

```
├── backend/          FastAPI + SQLAlchemy + Alembic
├── frontend/         Next.js 14 + TypeScript + Tailwind
├── docker-compose.yml
└── docs/
```

## License

MIT
