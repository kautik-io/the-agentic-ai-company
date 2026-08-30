#!/usr/bin/env bash
# Smart deploy — inspects git changes and runs only what's needed.
# Usage:
#   ./scripts/auto.sh           # deploy based on changes since last run
#   ./scripts/auto.sh --force   # full rebuild + migrate
#   ./scripts/auto.sh --dry-run # show plan only
#
# No arguments needed — it decides: restart / rebuild / migrate.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/common.sh
source "$ROOT_DIR/scripts/lib/common.sh"

cd "$ROOT_DIR"
setup_docker
ensure_env

FORCE=false
DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=true ;;
    --dry-run) DRY_RUN=true ;;
  esac
done

ACTIONS=()
NEED_MIGRATE=false
REBUILD_BACKEND=false
REBUILD_FRONTEND=false
REBUILD_ALL=false
RESTART_BACKEND=false
RESTART_FRONTEND=false
RESTART_ALL=false

add_action() {
  local a="$1"
  [[ " ${ACTIONS[*]} " == *" $a "* ]] || ACTIONS+=("$a")
}

analyze_changes() {
  local files
  if [[ "$FORCE" == true ]]; then
    REBUILD_ALL=true
    NEED_MIGRATE=true
    add_action "full-rebuild"
    add_action "migrate"
    return
  fi

  local last=""
  [[ -f "$LAST_COMMIT_FILE" ]] && last=$(cat "$LAST_COMMIT_FILE")

  if ! git rev-parse HEAD &>/dev/null; then
    log_action "Not a git repo — checking if containers need start"
    if ! containers_running; then
      REBUILD_ALL=true
      NEED_MIGRATE=true
      add_action "start-all"
      add_action "migrate"
    else
      add_action "noop (no git, containers running)"
    fi
    return
  fi

  local current
  current=$(git rev-parse HEAD)

  if [[ "$last" == "$current" ]]; then
    add_action "noop (no new commits)"
    return
  fi

  files=$(get_changed_files "$last" "$current")
  if [[ -z "$files" ]]; then
    if ! containers_running; then
      REBUILD_ALL=true
      NEED_MIGRATE=true
      add_action "start-all"
      add_action "migrate"
    else
      add_action "noop"
    fi
    return
  fi

  log_action "Changed files since last deploy:"
  echo "$files" | sed 's/^/  /'

  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    case "$f" in
      docker-compose.yml|.env.example)
        REBUILD_ALL=true
        add_action "rebuild-all (infra)"
        ;;
      backend/Dockerfile|backend/requirements.txt)
        REBUILD_BACKEND=true
        add_action "rebuild-backend"
        ;;
      backend/alembic/versions/*|backend/alembic/env.py)
        NEED_MIGRATE=true
        add_action "migrate"
        ;;
      backend/*)
        RESTART_BACKEND=true
        add_action "restart-backend"
        ;;
      frontend/Dockerfile|frontend/package.json|frontend/package-lock.json)
        REBUILD_FRONTEND=true
        add_action "rebuild-frontend"
        ;;
      frontend/*)
        RESTART_FRONTEND=true
        add_action "restart-frontend"
        ;;
      scripts/auto.sh|scripts/dev.sh|scripts/lib/*)
        ;; # no container action
    esac
  done <<< "$files"

  # Rebuild implies migrate for safety on backend rebuild
  if [[ "$REBUILD_ALL" == true || "$REBUILD_BACKEND" == true ]]; then
    NEED_MIGRATE=true
    add_action "migrate"
  fi

  if [[ ${#ACTIONS[@]} -eq 0 ]]; then
    add_action "noop (changes outside services)"
  fi
}

execute_plan() {
  if [[ "$DRY_RUN" == true ]]; then
    log_action "DRY RUN — would execute: ${ACTIONS[*]}"
    return 0
  fi

  if [[ "$REBUILD_ALL" == true ]]; then
    log_action "Rebuilding all services..."
    $COMPOSE up -d --build
    wait_healthy
  else
    if [[ "$REBUILD_BACKEND" == true ]]; then
      log_action "Rebuilding backend..."
      $COMPOSE up -d --build backend
      wait_healthy
    fi
    if [[ "$REBUILD_FRONTEND" == true ]]; then
      log_action "Rebuilding frontend..."
      $COMPOSE up -d --build frontend
    fi
    if [[ "$RESTART_ALL" == true ]]; then
      log_action "Restarting all..."
      $COMPOSE restart
    else
      if [[ "$RESTART_BACKEND" == true && "$REBUILD_BACKEND" == false ]]; then
        log_action "Restarting backend..."
        $COMPOSE restart backend
      fi
      if [[ "$RESTART_FRONTEND" == true && "$REBUILD_FRONTEND" == false ]]; then
        log_action "Restarting frontend..."
        $COMPOSE restart frontend
      fi
    fi
  fi

  # Start if nothing running
  if ! containers_running; then
    log_action "Starting services..."
    $COMPOSE up -d
    wait_healthy
    NEED_MIGRATE=true
  fi

  if [[ "$NEED_MIGRATE" == true ]]; then
    log_action "Running migrations..."
    $COMPOSE exec -T backend alembic upgrade head || log_action "Migrate skipped (backend not ready)"
  fi

  save_deploy_state
  log_action "Done: ${ACTIONS[*]}"
}

echo "=== AI Company OS — Auto Deploy ==="
analyze_changes

if [[ "$DRY_RUN" == false && " ${ACTIONS[*]} " == *" noop"* ]]; then
  log_action "Nothing to do."
  exit 0
fi

execute_plan

# Health check
if curl -sf "${BACKEND_URL:-http://localhost:8001}/api/health" &>/dev/null; then
  log_action "Health OK — ${FRONTEND_URL:-http://localhost:3001}"
else
  log_action "Warning: backend health check failed (may still be starting)"
fi
