"""Generate Mermaid logic graphs for projects, epics, and features.

AI agents read these graphs instead of full code to understand structure and flow.
"""

from __future__ import annotations

import re


def _safe_id(label: str) -> str:
    return re.sub(r"[^\w]", "_", label.lower())[:40] or "node"


def project_graph(
    project_name: str,
    description: str | None = None,
    epics: list[tuple[str, str]] | None = None,
) -> str:
    """Project-level architecture graph."""
    epics = epics or []
    lines = [
        "flowchart TD",
        f'  PROJ["{project_name}"]',
    ]
    if description:
        short = description[:80].replace('"', "'")
        lines.append(f'  PROJ --> DESC["{short}..."]')
    if not epics:
        lines.extend([
            "  PROJ --> EP1[Epic: Planning]",
            "  EP1 --> F1[Feature backlog]",
            "  F1 --> T1[Tasks]",
        ])
    else:
        for title, epic_id in epics:
            nid = _safe_id(title)
            lines.append(f'  PROJ --> {nid}["Epic: {title}"]')
            lines.append(f'  {nid} --> {nid}_f[Features & tasks]')
    lines.extend([
        "  classDef project fill:#1e3a5f,stroke:#3b82f6,color:#fff",
        "  class PROJ project",
    ])
    return "\n".join(lines)


def epic_graph(epic_title: str, description: str | None, features: list[str] | None = None) -> str:
    features = features or ["Core feature"]
    eid = _safe_id(epic_title)
    lines = [
        "flowchart LR",
        f'  {eid}["Epic: {epic_title}"]',
    ]
    prev = eid
    for i, feat in enumerate(features):
        fid = f"{eid}_f{i}"
        lines.append(f'  {prev} --> {fid}["{feat}"]')
        prev = fid
    if description:
        short = description[:60].replace('"', "'")
        lines.append(f'  {eid} -.-> NOTE["{short}"]')
    return "\n".join(lines)


def feature_graph(
    feature_title: str,
    description: str | None,
    steps: list[str] | None = None,
) -> str:
    steps = steps or ["Input", "Process", "Output"]
    fid = _safe_id(feature_title)
    lines = [
        "flowchart TD",
        f'  START([Start: {feature_title}])',
    ]
    prev = "START"
    for i, step in enumerate(steps):
        sid = f"{fid}_s{i}"
        lines.append(f'  {prev} --> {sid}["{step}"]')
        prev = sid
    lines.append(f"  {prev} --> END([Done])")
    if description:
        short = description[:60].replace('"', "'")
        lines.append(f'  START -.-> DESC["{short}"]')
    return "\n".join(lines)


def dependency_graph(tasks: list[tuple[int, str, list[str]]]) -> str:
    """Build task dependency graph. tasks = [(task_number, title, dependency_ids)]."""
    lines = ["flowchart TD"]
    for num, title, deps in tasks:
        nid = f"T{num}"
        short = title[:40].replace('"', "'")
        lines.append(f'  {nid}["TASK-{num}: {short}"]')
        for dep in deps:
            dep_nid = f"T{dep.replace('TASK-', '').replace('task-', '')}"
            lines.append(f"  {dep_nid} --> {nid}")
    return "\n".join(lines)
