"""Auto-generate output screenshots when AI completes tasks."""

from __future__ import annotations

import re
import textwrap
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.models import Project, Task
from app.services.browser_capture import screenshot_html, screenshot_url

WIDTH = 960
PADDING = 32
LINE_HEIGHT = 22
BG = (15, 23, 42)
PANEL = (30, 41, 59)
TEXT = (226, 232, 240)
MUTED = (148, 163, 184)
GREEN = (74, 222, 128)
ACCENT = (56, 189, 248)

UI_KEYWORDS = ("login", "page", "dashboard", "portal", "frontend", "ui", "screen", "form", "build:", "design:")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(text: str, width: int = 92) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=width) or [""])
    return lines


def _estimate_height(lines: list[str]) -> int:
    return PADDING * 2 + 120 + len(lines) * LINE_HEIGHT + 80


def is_ui_task(task: Task) -> bool:
    phase = (task.input_context or {}).get("phase", "build")
    title = task.title.lower()
    if phase in ("build", "design", "test", "fix"):
        return any(k in title for k in UI_KEYWORDS)
    return False


def _collect_preview_urls(
    project: Project,
    output: dict[str, Any],
    preview_host: str | None,
) -> list[str]:
    urls: list[str] = []
    for key in ("preview_url", "screenshot_url", "live_url", "app_url"):
        val = output.get(key)
        if val:
            urls.append(str(val).strip())

    env = project.environments or {}
    for key in ("preview_url", "url", "staging_url"):
        val = env.get(key)
        if val:
            urls.append(str(val).strip())

    if preview_host:
        text = f"{project.description or ''} {' '.join(project.requirements or [])}"
        ports = re.findall(r"(?:port\s+|[:\\s])(\d{4,5})\b", text, flags=re.I)
        if not ports:
            ports = ["6000", "3000", "8080"]
        seen_ports: set[str] = set()
        for port in ports:
            if port in seen_ports:
                continue
            seen_ports.add(port)
            urls.extend([
                f"http://{preview_host}:{port}/",
                f"http://{preview_host}:{port}/login",
                f"http://{preview_host}:{port}/index.html",
            ])

    deduped: list[str] = []
    for url in urls:
        if url not in deduped:
            deduped.append(url)
    return deduped


def _find_local_html_files(workspace_path: str | None) -> list[Path]:
    if not workspace_path:
        return []
    root = Path(workspace_path)
    if not root.is_absolute():
        root = Path(settings.workspaces_root) / workspace_path
    if not root.exists():
        return []

    patterns = (
        "index.html",
        "login.html",
        "public/index.html",
        "src/index.html",
        "frontend/index.html",
        "templates/project-login-page/index.html",
    )
    found: list[Path] = []
    for pattern in patterns:
        candidate = root / pattern
        if candidate.is_file():
            found.append(candidate)
    if not found:
        for path in root.rglob("*.html"):
            if path.name in ("index.html", "login.html") and len(found) < 3:
                found.append(path)
    return found


def generate_output_report_png(
    task: Task,
    project: Project,
    agent_name: str,
    output: dict[str, Any],
) -> bytes:
    summary = str(output.get("summary") or output.get("notes") or "Task completed successfully.")
    deliverables = output.get("deliverables") or output.get("files_changed") or []
    if isinstance(deliverables, str):
        deliverables = [deliverables]

    body_lines = [
        f"Project: {project.name}",
        f"Agent: {agent_name}",
        f"Phase: {(task.input_context or {}).get('phase', 'build')}",
        "",
        "Summary:",
        summary,
    ]
    if deliverables:
        body_lines.extend(["", "Deliverables:"])
        body_lines.extend(f"• {item}" for item in deliverables[:8])

    wrapped: list[str] = []
    for line in body_lines:
        wrapped.extend(_wrap(line) if line and not line.startswith("•") else [line])

    height = min(max(_estimate_height(wrapped), 480), 1400)
    image = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(image)
    title_font = _font(24, bold=True)
    label_font = _font(14, bold=True)
    body_font = _font(14)

    draw.rounded_rectangle((PADDING, PADDING, WIDTH - PADDING, height - PADDING), radius=16, fill=PANEL)
    y = PADDING + 24
    draw.text((PADDING + 24, y), "Task Summary", font=title_font, fill=ACCENT)
    y += 36
    draw.text((PADDING + 24, y), f"TASK-{task.task_number} — {task.title[:80]}", font=label_font, fill=TEXT)
    y += 28
    draw.text((PADDING + 24, y), datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), font=body_font, fill=MUTED)
    y += 44

    for line in wrapped:
        if y > height - PADDING - 40:
            break
        color = MUTED if line.endswith(":") else TEXT
        draw.text((PADDING + 24, y), line[:110], font=body_font, fill=color)
        y += LINE_HEIGHT

    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


async def fetch_preview_image(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            content_type = response.headers.get("content-type", "")
            if content_type.startswith("image/"):
                return response.content
    except Exception:
        return None
    return None


async def capture_task_outputs(
    task: Task,
    project: Project,
    agent_name: str,
    output: dict[str, Any],
    *,
    preview_host: str | None = None,
) -> list[tuple[bytes, str]]:
    """Return screenshot(s): working UI first, task summary second if needed."""
    captures: list[tuple[bytes, str]] = []
    ui_task = is_ui_task(task)

    # 1) Direct image URL
    for url in _collect_preview_urls(project, output, preview_host):
        image = await fetch_preview_image(url)
        if image:
            captures.append((image, f"Working output — {url}"))
            break

    # 2) Live page browser screenshot
    if not captures:
        for url in _collect_preview_urls(project, output, preview_host):
            if url.startswith("http"):
                image = await screenshot_url(url)
                if image:
                    captures.append((image, f"Working app preview — {url}"))
                    break

    # 3) HTML deliverable from agent
    if not captures:
        html = output.get("html_deliverable") or output.get("html_preview") or output.get("ui_html")
        if html and isinstance(html, str) and "<" in html:
            image = await screenshot_html(html)
            if image:
                captures.append((image, "Working UI — rendered from agent deliverable"))

    # 4) Local workspace HTML files
    if not captures and project.workspace_path:
        for html_path in _find_local_html_files(project.workspace_path):
            image = await screenshot_url(html_path.as_uri())
            if image:
                captures.append((image, f"Working UI — {html_path.name}"))
                break

    # 5) Bundled login template fallback for login build tasks
    if not captures and ui_task and "login" in task.title.lower():
        template = Path("/templates/project-login-page/index.html")
        if not template.is_file():
            template = Path(__file__).resolve().parents[3] / "templates" / "project-login-page" / "index.html"
        if template.is_file():
            html = template.read_text(encoding="utf-8")
            css_path = template.parent / "login.css"
            if css_path.is_file():
                css = css_path.read_text(encoding="utf-8")
                html = html.replace('href="login.css"', f"<style>{css}</style>")
            image = await screenshot_html(html, base_url=template.parent.as_uri() + "/")
            if image:
                captures.append((image, "Working UI — login page preview"))

    # Summary card — always add for context, but UI tasks get UI shot first
    if not captures or not ui_task:
        captures.append((
            generate_output_report_png(task, project, agent_name, output),
            "Task summary",
        ))

    return captures


async def capture_task_output(
    task: Task,
    project: Project,
    agent_name: str,
    output: dict[str, Any],
    *,
    preview_host: str | None = None,
) -> bytes:
    shots = await capture_task_outputs(
        task, project, agent_name, output, preview_host=preview_host
    )
    return shots[0][0]
