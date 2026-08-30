#!/usr/bin/env bash
# AI Company OS — Docker dev helper
# Usage: ./scripts/dev.sh [command]
#
# Commands:
#   start      Start all services (detached)
#   stop       Stop all services
#   restart    Restart all services (no rebuild)
#   rebuild    Rebuild images and restart
#   full       Rebuild + migrate + seed demo data
#   logs       Follow logs (all services)
#   status     Show container status + URLs
#   migrate    Run database migrations
#   seed       Seed demo company + agents
#   seed-tasks Seed demo tasks for Customer Support Platform
#   backend    Restart backend only
#   frontend   Restart frontend only
#   clean      Stop and remove volumes (⚠ deletes DB)
#   auto       Smart deploy based on git changes (no args needed)
#   sync       GitHub pull + auto deploy
#   watch      Poll GitHub every 60s + auto deploy

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Use sudo for docker if needed (common on Raspberry Pi)
DOCKER="docker"
COMPOSE="docker compose"
if ! docker info &>/dev/null; then
  if sudo docker info &>/dev/null; then
    DOCKER="sudo docker"
    COMPOSE="sudo docker compose"
  else
    echo "Error: Docker is not running or not accessible."
    exit 1
  fi
fi

FRONTEND_URL="${FRONTEND_URL:-http://localhost:3001}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8001}"

ensure_env() {
  if [[ ! -f .env ]]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
  fi
}

wait_healthy() {
  echo "Waiting for postgres and redis..."
  local i=0
  while [[ $i -lt 60 ]]; do
    if $COMPOSE ps postgres 2>/dev/null | grep -q "healthy"; then
      if $COMPOSE ps redis 2>/dev/null | grep -q "healthy"; then
        echo "Database services ready."
        return 0
      fi
    fi
    sleep 2
    i=$((i + 1))
  done
  echo "Warning: services may not be fully healthy yet."
}

cmd_start() {
  ensure_env
  echo "Starting AI Company OS..."
  $COMPOSE up -d
  wait_healthy
  cmd_status
}

cmd_stop() {
  echo "Stopping AI Company OS..."
  $COMPOSE down
  echo "Stopped."
}

cmd_restart() {
  ensure_env
  echo "Restarting services..."
  $COMPOSE restart
  wait_healthy
  cmd_status
}

cmd_rebuild() {
  ensure_env
  echo "Rebuilding images and starting..."
  $COMPOSE up -d --build
  wait_healthy
  echo "Running migrations..."
  $COMPOSE exec -T backend alembic upgrade head
  cmd_status
}

cmd_migrate() {
  ensure_env
  $COMPOSE exec -T backend alembic upgrade head
  echo "Migrations complete."
}

cmd_seed() {
  ensure_env
  $COMPOSE exec -T backend python scripts/seed.py
}

cmd_seed_tasks() {
  ensure_env
  $COMPOSE exec -T backend python scripts/seed_tasks.py
}

cmd_full() {
  cmd_rebuild
  echo "Seeding demo data..."
  $COMPOSE exec -T backend python scripts/seed.py || true
  $COMPOSE exec -T backend python scripts/seed_tasks.py || true
  echo ""
  echo "Full setup complete."
  cmd_status
}

cmd_logs() {
  local service="${1:-}"
  if [[ -n "$service" ]]; then
    $COMPOSE logs -f "$service"
  else
    $COMPOSE logs -f
  fi
}

cmd_status() {
  echo ""
  echo "=== AI Company OS — Status ==="
  $COMPOSE ps
  echo ""
  echo "  Frontend:  $FRONTEND_URL"
  echo "  Backend:   $BACKEND_URL"
  echo "  API docs:  $BACKEND_URL/api/docs"
  echo "  Demo login: ceo@demo.com / demo1234"
  echo ""
  if curl -sf "$BACKEND_URL/api/health" &>/dev/null; then
    echo "  Health:    OK"
  else
    echo "  Health:    backend not responding yet (may still be starting)"
  fi
  echo ""
}

cmd_backend() {
  $COMPOSE restart backend
  echo "Backend restarted."
}

cmd_frontend() {
  $COMPOSE restart frontend
  echo "Frontend restarted."
}

cmd_clean() {
  read -r -p "This deletes ALL database data. Continue? [y/N] " confirm
  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    $COMPOSE down -v
    echo "Cleaned. Run: ./scripts/dev.sh full"
  else
    echo "Cancelled."
  fi
}

cmd_help() {
  sed -n '2,20p' "$0" | sed 's/^# \?//'
  echo ""
  echo "Examples:"
  echo "  ./scripts/dev.sh start          # first time / after boot"
  echo "  ./scripts/dev.sh rebuild        # after code changes"
  echo "  ./scripts/dev.sh restart        # quick restart, no rebuild"
  echo "  ./scripts/dev.sh logs backend   # tail backend logs"
  echo "  ./scripts/dev.sh full           # rebuild + migrate + seed everything"
}

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
  start)       cmd_start ;;
  stop)        cmd_stop ;;
  restart)     cmd_restart ;;
  rebuild)     cmd_rebuild ;;
  full)        cmd_full ;;
  logs)        cmd_logs "$@" ;;
  status)      cmd_status ;;
  migrate)     cmd_migrate ;;
  seed)        cmd_seed ;;
  seed-tasks)  cmd_seed_tasks ;;
  backend)     cmd_backend ;;
  frontend)    cmd_frontend ;;
  clean)       cmd_clean ;;
  auto)        "$ROOT_DIR/scripts/auto.sh" "$@" ;;
  sync)        "$ROOT_DIR/scripts/github-sync.sh" sync ;;
  watch)       "$ROOT_DIR/scripts/github-sync.sh" watch ;;
  help|-h|--help) cmd_help ;;
  *)
    echo "Unknown command: $COMMAND"
    cmd_help
    exit 1
    ;;
esac
