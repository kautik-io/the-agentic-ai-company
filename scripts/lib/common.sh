#!/usr/bin/env bash
# Shared helpers for deploy scripts
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY_STATE_DIR="$ROOT_DIR/.deploy"
LAST_COMMIT_FILE="$DEPLOY_STATE_DIR/last-commit"
LAST_CHECK_FILE="$DEPLOY_STATE_DIR/last-check"

setup_docker() {
  DOCKER="docker"
  COMPOSE="docker compose"
  if ! docker info &>/dev/null; then
    if sudo docker info &>/dev/null; then
      DOCKER="sudo docker"
      COMPOSE="sudo docker compose"
    else
      echo "Error: Docker not available."
      return 1
    fi
  fi
}

ensure_env() {
  if [[ ! -f "$ROOT_DIR/.env" ]]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  fi
}

wait_healthy() {
  local i=0
  while [[ $i -lt 45 ]]; do
    if $COMPOSE ps postgres 2>/dev/null | grep -q "healthy" && \
       $COMPOSE ps redis 2>/dev/null | grep -q "healthy"; then
      return 0
    fi
    sleep 2
    i=$((i + 1))
  done
  return 0
}

containers_running() {
  $COMPOSE ps --status running 2>/dev/null | grep -q backend
}

save_deploy_state() {
  mkdir -p "$DEPLOY_STATE_DIR"
  if git -C "$ROOT_DIR" rev-parse HEAD &>/dev/null; then
    git -C "$ROOT_DIR" rev-parse HEAD > "$LAST_COMMIT_FILE"
  fi
  date -Iseconds > "$LAST_CHECK_FILE"
}

get_changed_files() {
  local from="${1:-}"
  local to="${2:-HEAD}"
  if [[ -n "$from" ]] && git -C "$ROOT_DIR" cat-file -e "$from" 2>/dev/null; then
    git -C "$ROOT_DIR" diff --name-only "$from" "$to" 2>/dev/null || true
  else
    # First run: all tracked files
    git -C "$ROOT_DIR" ls-files 2>/dev/null || true
  fi
}

log_action() {
  echo "[auto] $(date '+%H:%M:%S') $*"
}
