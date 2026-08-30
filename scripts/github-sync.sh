#!/usr/bin/env bash
# Pull from GitHub and auto-deploy. Zero manual steps.
#
# Setup once:
#   cp deploy/github.env.example deploy/github.env
#   edit deploy/github.env  (branch, remote)
#   ./scripts/github-sync.sh init
#
# Then either:
#   ./scripts/github-sync.sh          # manual pull + auto deploy
#   ./scripts/github-sync.sh watch    # poll GitHub every 60s
#   sudo ./scripts/github-sync.sh install-cron   # every 5 min via cron

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=lib/common.sh
source "$ROOT_DIR/scripts/lib/common.sh"

CONFIG="$ROOT_DIR/deploy/github.env"
DEFAULT_BRANCH="main"
DEFAULT_REMOTE="origin"
POLL_INTERVAL="${POLL_INTERVAL:-60}"

load_config() {
  BRANCH="$DEFAULT_BRANCH"
  REMOTE="$DEFAULT_REMOTE"
  GITHUB_REPO=""
  if [[ -f "$CONFIG" ]]; then
    # shellcheck disable=SC1090
    source "$CONFIG"
  fi
  BRANCH="${DEPLOY_BRANCH:-$BRANCH}"
  REMOTE="${GIT_REMOTE:-$REMOTE}"
}

cmd_init() {
  load_config
  cd "$ROOT_DIR"
  if [[ ! -d .git ]]; then
    git init
    log_action "Initialized git repository"
  fi
  if [[ -n "${GITHUB_REPO:-}" ]]; then
    if git remote get-url "$REMOTE" &>/dev/null; then
      git remote set-url "$REMOTE" "$GITHUB_REPO"
    else
      git remote add "$REMOTE" "$GITHUB_REPO"
    fi
    log_action "Remote $REMOTE → $GITHUB_REPO"
  fi
  git fetch "$REMOTE" 2>/dev/null || log_action "Could not fetch yet — set GITHUB_REPO in deploy/github.env"
  echo ""
  echo "Next: ./scripts/github-sync.sh"
}

cmd_pull_and_deploy() {
  load_config
  cd "$ROOT_DIR"
  setup_docker
  ensure_env

  if ! git rev-parse HEAD &>/dev/null; then
    cmd_init
  fi

  log_action "Fetching $REMOTE/$BRANCH ..."
  git fetch "$REMOTE" "$BRANCH" 2>/dev/null || {
    log_action "Fetch failed — check GITHUB_REPO and network"
    exit 1
  }

  LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "")
  REMOTE_SHA=$(git rev-parse "$REMOTE/$BRANCH" 2>/dev/null || echo "")

  if [[ "$LOCAL" == "$REMOTE_SHA" ]]; then
    log_action "Already up to date ($BRANCH)"
    "$ROOT_DIR/scripts/auto.sh"
    exit 0
  fi

  log_action "Updating $LOCAL → $REMOTE_SHA"
  git merge "$REMOTE/$BRANCH" --ff-only || git pull "$REMOTE" "$BRANCH"

  log_action "Running auto deploy..."
  "$ROOT_DIR/scripts/auto.sh"
}

cmd_watch() {
  load_config
  log_action "Watching $REMOTE/$BRANCH every ${POLL_INTERVAL}s (Ctrl+C to stop)"
  while true; do
    cmd_pull_and_deploy 2>&1 || true
    sleep "$POLL_INTERVAL"
  done
}

cmd_install_cron() {
  load_config
  local script="$ROOT_DIR/scripts/github-sync.sh"
  local cron_line="*/5 * * * * cd $ROOT_DIR && $script >> $ROOT_DIR/.deploy/sync.log 2>&1"
  (crontab -l 2>/dev/null | grep -v "github-sync.sh" || true; echo "$cron_line") | crontab -
  log_action "Cron installed — sync every 5 minutes"
  log_action "Log: $ROOT_DIR/.deploy/sync.log"
}

cmd_webhook() {
  # Simple GitHub webhook receiver (POST /webhook)
  load_config
  local port="${WEBHOOK_PORT:-9000}"
  local secret="${GITHUB_WEBHOOK_SECRET:-}"
  log_action "Starting webhook on port $port ..."
  exec python3 "$ROOT_DIR/scripts/github_webhook.py" --port "$port" --secret "$secret" --root "$ROOT_DIR"
}

SUB="${1:-sync}"
shift || true

case "$SUB" in
  init)           cmd_init ;;
  sync|pull|"")   cmd_pull_and_deploy ;;
  watch)          cmd_watch ;;
  install-cron)   cmd_install_cron ;;
  webhook)        cmd_webhook "$@" ;;
  *)
    echo "Usage: $0 {init|sync|watch|install-cron|webhook}"
    exit 1
    ;;
esac
