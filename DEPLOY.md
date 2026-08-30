# Auto Deploy

Zero-command deploy: scripts detect what changed and restart/rebuild only what's needed.

## Smart auto (local changes / after git pull)

```bash
./scripts/auto.sh
```

| If this changed | Action |
|-----------------|--------|
| `backend/app/*` | Restart backend |
| `backend/requirements.txt` or `Dockerfile` | Rebuild backend |
| `backend/alembic/versions/*` | Run migrations |
| `frontend/src/*` | Restart frontend |
| `frontend/package.json` | Rebuild frontend |
| `docker-compose.yml` | Rebuild everything |

Preview without applying:

```bash
./scripts/auto.sh --dry-run
```

Force full rebuild:

```bash
./scripts/auto.sh --force
```

---

## GitHub — set once, then forget

### 1. Configure

```bash
cp deploy/github.env.example deploy/github.env
nano deploy/github.env   # set GITHUB_REPO and branch
./scripts/github-sync.sh init
```

### 2. Choose how updates arrive

**Option A — Poll every 60s (simplest on Pi)**

```bash
./scripts/github-sync.sh watch
```

**Option B — Cron every 5 minutes**

```bash
sudo ./scripts/github-sync.sh install-cron
```

**Option C — Instant on git push (webhook)**

```bash
# On Pi — expose port 9000 or use reverse proxy
./scripts/github-sync.sh webhook
```

In GitHub: **Settings → Webhooks → Add**
- URL: `http://YOUR_PI_IP:9000/webhook`
- Secret: same as `GITHUB_WEBHOOK_SECRET` in `deploy/github.env`
- Events: **Push**

**Option D — GitHub Actions SSH deploy**

Add repo secrets:

| Secret | Example |
|--------|---------|
| `DEPLOY_HOST` | `192.168.1.10` |
| `DEPLOY_USER` | `aividmini` |
| `DEPLOY_SSH_KEY` | private key contents |
| `DEPLOY_PATH` | `/home/aividmini/PS/the-agentic-ai-company` |

Push to `main` → CI runs → SSH → `./scripts/github-sync.sh sync`

---

## One-liner aliases (via dev.sh)

```bash
./scripts/dev.sh auto    # same as auto.sh
./scripts/dev.sh sync    # pull GitHub + auto
./scripts/dev.sh watch   # continuous poll
```

State is stored in `.deploy/last-commit` so only new commits trigger work.
