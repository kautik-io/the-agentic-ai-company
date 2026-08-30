#!/usr/bin/env python3
"""Small E2E API smoke tests for AI Engineering OS (AIOS)."""

import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8001"
PASS = 0
FAIL = 0
WARN = 0


def api(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            if resp.status == 204:
                return resp.status, None
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = raw
        return e.code, detail


def ok(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


def warn(name, detail=""):
    global WARN
    WARN += 1
    print(f"  WARN  {name}" + (f" — {detail}" if detail else ""))


def main():
    print("\n=== AI Engineering OS (AIOS) E2E Smoke Tests ===\n")

    # 1. Health
    print("[1] Health")
    code, body = api("GET", "/api/health")
    ok("GET /api/health → 200", code == 200 and body.get("status") == "ok", str(body))

    # 2. Auth
    print("\n[2] Authentication")
    code, body = api("POST", "/api/auth/login", {"email": "ceo@demo.com", "password": "demo1234"})
    ok("Login demo user", code == 200 and "access_token" in (body or {}), str(body))
    if code != 200:
        print("\nAborting — cannot login")
        sys.exit(1)
    token = body["access_token"]

    code, _ = api("GET", "/api/auth/me", token=token)
    ok("GET /api/auth/me", code == 200)

    # 3. Organization
    print("\n[3] Organization")
    code, orgs = api("GET", "/api/organizations", token=token)
    ok("List organizations", code == 200 and len(orgs) > 0)
    org_id = orgs[0]["id"]

    # 4. Dashboard
    print("\n[4] Dashboard")
    code, stats = api("GET", f"/api/organizations/{org_id}/dashboard", token=token)
    ok("Dashboard stats", code == 200 and "total_agents" in (stats or {}))
    if stats:
        print(f"       agents={stats.get('total_agents')} tasks={stats.get('total_tasks')} blocked={stats.get('blocked_tasks')}")

    # 5. AI Providers
    print("\n[5] AI Provider Settings")
    code, catalog = api("GET", f"/api/organizations/{org_id}/ai-providers/catalog", token=token)
    ok("Provider catalog", code == 200 and len(catalog) >= 3)

    code, providers = api("GET", f"/api/organizations/{org_id}/ai-providers", token=token)
    ok("List saved providers", code == 200)
    configured = {p["provider"] for p in (providers or [])}
    print(f"       configured providers: {configured or '(none)'}")

    code, fetch = api(
        "POST",
        f"/api/organizations/{org_id}/ai-providers/fetch-models",
        {"provider": "openai", "api_key": "sk-invalid-test-key-12345"},
        token=token,
    )
    ok("Fetch models rejects bad key", code in (400, 401, 403), str(fetch))

    # 6. Agents (configured_only filter)
    print("\n[6] AI Employees")
    code, agents_all = api("GET", f"/api/organizations/{org_id}/agents?configured_only=false", token=token)
    code2, agents_filtered = api("GET", f"/api/organizations/{org_id}/agents?configured_only=true", token=token)
    ok("List all agents", code == 200)
    ok("List configured-only agents", code2 == 200)
    n_all = len(agents_all or [])
    n_cfg = len(agents_filtered or [])
    print(f"       all={n_all} configured-only={n_cfg}")
    if not configured and n_cfg > 0:
        warn("Agents visible without provider keys", f"expected 0, got {n_cfg}")
    elif configured and n_cfg == 0 and n_all > 0:
        warn("No agents match configured providers", f"providers={configured}")
    else:
        ok("Agent filter logic", True)

    # 7. Projects
    print("\n[7] Projects")
    code, projects = api("GET", f"/api/organizations/{org_id}/projects", token=token)
    ok("List projects", code == 200)
    print(f"       count={len(projects or [])}")

    if projects:
        pid = projects[0]["id"]
        code, proj = api("GET", f"/api/organizations/{org_id}/projects/{pid}", token=token)
        ok("Get project detail", code == 200 and proj.get("id") == pid)
        has_ws = bool(proj.get("workspace_path"))
        has_graph = bool(proj.get("logic_graph"))
        ok("Project has workspace_path", has_ws, proj.get("workspace_path", "missing"))
        ok("Project has logic_graph", has_graph)

        code, graph = api("GET", f"/api/organizations/{org_id}/projects/{pid}/graph", token=token)
        ok("Get project graph", code == 200 and "epics" in (graph or {}))

        code, tasks = api("GET", f"/api/organizations/{org_id}/projects/{pid}/tasks", token=token)
        ok("List tasks", code == 200)
        stuck = [t for t in (tasks or []) if t["status"] in ("blocked", "failed", "waiting")]
        print(f"       tasks={len(tasks or [])} stuck={len(stuck)}")
        if stuck:
            t = stuck[0]
            has_reason = bool(t.get("blocked_reason") or t.get("failure_reason"))
            ok("Stuck task has reason field", has_reason or t["status"] == "waiting")

    # 8. Execution targets
    print("\n[8] Run Environments")
    code, targets = api("GET", f"/api/organizations/{org_id}/execution-targets", token=token)
    ok("List execution targets", code == 200)

    # 9. Activities
    print("\n[9] Activity feed")
    code, acts = api("GET", f"/api/organizations/{org_id}/activities?limit=5", token=token)
    ok("List activities", code == 200)

    # 10. Frontend routes
    print("\n[10] Frontend pages (HTTP 200)")
    for path in ["/login", "/dashboard", "/agents", "/projects", "/tasks", "/settings"]:
        try:
            req = urllib.request.Request(f"http://localhost:3001{path}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                ok(f"GET {path}", resp.status == 200)
        except Exception as e:
            ok(f"GET {path}", False, str(e))

    # Summary
    print("\n=== Summary ===")
    print(f"  Passed: {PASS}")
    print(f"  Failed: {FAIL}")
    print(f"  Warnings: {WARN}")
    print()
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
