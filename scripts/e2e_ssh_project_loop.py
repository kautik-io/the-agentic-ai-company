#!/usr/bin/env python3
"""E2E loop: create a small project on SSH execution target until live without errors."""

from __future__ import annotations

import getpass
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "http://localhost:8001"
MAX_ATTEMPTS = 5
PROJECT_PREFIX = "SSH Demo"


def api(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
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


def ssh_verify(target: dict, remote_path: str, password: str | None = None) -> tuple[bool, str]:
    args = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=10",
    ]
    key = target.get("ssh_key_path")
    use_password = password or target.get("ssh_password_set")
    if not use_password:
        args.extend(["-o", "BatchMode=yes"])
    if key:
        args.extend(["-i", key])
    args.extend(["-p", str(target.get("port", 22)), f"{target['username']}@{target['host']}"])
    cmd = f"test -f {remote_path}/README.md && test -f {remote_path}/docs/LOGIC_GRAPH.md && echo OK"
    args.append(cmd)
    run_cmd = args
    if use_password and not key and password:
        run_cmd = ["sshpass", "-p", password, *args]
    result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0 and "OK" in (result.stdout or ""):
        return True, "Remote README.md and LOGIC_GRAPH.md exist"
    err = (result.stderr or result.stdout or "SSH verify failed").strip()
    return False, err


def ensure_ssh_password(org_id: str, target_id: str, token: str) -> str | None:
    password = os.environ.get("AICOS_SSH_PASSWORD")
    if not password and sys.stdin.isatty():
        password = getpass.getpass(f"SSH password for target {target_id}: ")
    if password:
        code, body = api(
            "PATCH",
            f"/api/organizations/{org_id}/execution-targets/{target_id}",
            {"ssh_password": password},
            token=token,
        )
        if code != 200:
            print(f"Failed to save SSH password: {body}")
            return None
    return password


def delete_test_projects(org_id: str, token: str) -> None:
    code, projects = api("GET", f"/api/organizations/{org_id}/projects", token=token)
    if code != 200:
        return
    for p in projects or []:
        if p.get("name", "").startswith(PROJECT_PREFIX):
            api("DELETE", f"/api/organizations/{org_id}/projects/{p['id']}", token=token)


def main() -> int:
    print("\n=== SSH Project E2E Loop ===\n")

    code, body = api("POST", "/api/auth/login", {"email": "ceo@demo.com", "password": "demo1234"})
    if code != 200:
        print(f"Login failed: {body}")
        return 1
    token = body["access_token"]

    code, orgs = api("GET", "/api/organizations", token=token)
    if code != 200 or not orgs:
        print(f"No organizations: {body}")
        return 1
    org_id = orgs[0]["id"]

    code, targets = api("GET", f"/api/organizations/{org_id}/execution-targets", token=token)
    if code != 200:
        print(f"Cannot list execution targets: {targets}")
        return 1

    ssh_targets = [t for t in (targets or []) if t.get("target_type") == "ssh"]
    if not ssh_targets:
        print("No SSH execution target configured. Add one in Settings → Run Environments.")
        return 1

    target = next((t for t in ssh_targets if t.get("is_default")), ssh_targets[0])
    target_id = target["id"]
    print(f"Using SSH target: {target['name']} ({target['username']}@{target['host']}:{target.get('port', 22)})")
    print(f"Remote workspace root: {target['workspace_path']}\n")

    password = ensure_ssh_password(org_id, target_id, token)

    code, tested = api("POST", f"/api/organizations/{org_id}/execution-targets/{target_id}/test", token=token)
    if code != 200:
        print(f"SSH test API failed: {tested}")
        return 1
    if tested.get("status") != "connected":
        print(f"SSH target not connected: {tested.get('last_error') or tested.get('status')}")
        return 1
    print("SSH target test: PASS\n")

    delete_test_projects(org_id, token)

    project_id = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        name = f"{PROJECT_PREFIX} {int(time.time())}"
        print(f"[Attempt {attempt}/{MAX_ATTEMPTS}] Creating project '{name}'...")

        payload = {
            "name": name,
            "description": "Small E2E test project provisioned on SSH host",
            "goals": ["Verify SSH workspace provisioning"],
            "requirements": ["README.md", "LOGIC_GRAPH.md"],
            "tech_stack": ["python"],
            "execution_target_id": target_id,
        }
        code, project = api("POST", f"/api/organizations/{org_id}/projects", payload, token=token)
        if code != 201:
            detail = project.get("detail") if isinstance(project, dict) else project
            print(f"  FAIL create project ({code}): {detail}")
            time.sleep(2)
            continue

        project_id = project["id"]
        workspace_path = project.get("workspace_path", "")
        print(f"  Created id={project_id}")
        print(f"  workspace_path={workspace_path}")

        if not workspace_path:
            print("  FAIL: missing workspace_path")
            api("DELETE", f"/api/organizations/{org_id}/projects/{project_id}", token=token)
            project_id = None
            continue

        code, graph = api("GET", f"/api/organizations/{org_id}/projects/{project_id}/graph", token=token)
        if code != 200 or not graph.get("epics"):
            print(f"  FAIL graph endpoint ({code}): {graph}")
            api("DELETE", f"/api/organizations/{org_id}/projects/{project_id}", token=token)
            project_id = None
            continue
        print("  Graph API: PASS")

        ok, msg = ssh_verify(target, workspace_path, password=password)
        if not ok:
            print(f"  FAIL remote verify: {msg}")
            api("DELETE", f"/api/organizations/{org_id}/projects/{project_id}", token=token)
            project_id = None
            time.sleep(2)
            continue
        print(f"  Remote verify: PASS — {msg}")

        code, detail = api("GET", f"/api/organizations/{org_id}/projects/{project_id}", token=token)
        if code != 200:
            print(f"  FAIL get project ({code})")
            api("DELETE", f"/api/organizations/{org_id}/projects/{project_id}", token=token)
            project_id = None
            continue

        print("\n=== SUCCESS ===")
        print(f"Project '{name}' is live on SSH at {workspace_path}")
        print(f"Project ID: {project_id}")
        print(f"View: http://localhost:3001/projects/{project_id}")
        return 0

    if project_id:
        api("DELETE", f"/api/organizations/{org_id}/projects/{project_id}", token=token)
    print(f"\n=== FAILED after {MAX_ATTEMPTS} attempts ===")
    return 1


if __name__ == "__main__":
    sys.exit(main())
