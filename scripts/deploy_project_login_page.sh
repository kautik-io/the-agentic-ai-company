#!/usr/bin/env bash
# Deploy page 1 (login) into an SSH project workspace for E2E testing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE="${1:-/opt/Kautik/demo-ai-company/ssh-demo-1788111087}"
HOST="${SSH_HOST:-192.168.222.213}"
USER="${SSH_USER:-aivid34}"
PASS="${AICOS_SSH_PASSWORD:-1234}"

SSH=(sshpass -p "$PASS" ssh -o StrictHostKeyChecking=accept-new "$USER@$HOST")
SCP=(sshpass -p "$PASS" scp -o StrictHostKeyChecking=accept-new)

SRC="$ROOT/templates/project-login-page"
REMOTE_LOGIN="$REMOTE/src/login"

"${SSH[@]}" "mkdir -p '$REMOTE_LOGIN' '$REMOTE/tests'"

for f in index.html login.css login.js; do
  "${SCP[@]}" "$SRC/$f" "$USER@$HOST:$REMOTE_LOGIN/"
done
"${SCP[@]}" "$SRC/test_login_page.py" "$USER@$HOST:$REMOTE/tests/"

echo "Deployed login page to $USER@$HOST:$REMOTE_LOGIN"
