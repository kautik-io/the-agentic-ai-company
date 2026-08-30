"""Fetch available models from AI provider APIs using the user's API key."""

from __future__ import annotations

import httpx

from app.services.ai_provider import PROVIDER_MODELS

OPENAI_CHAT_PREFIXES = ("gpt-", "o1", "o3", "chatgpt")
ANTHROPIC_PREFIX = "claude"
GOOGLE_PREFIX = "gemini"


async def fetch_models_from_provider(provider: str, api_key: str) -> tuple[list[str], str | None]:
    """Returns (models, error_message). error_message is set on partial failure with fallback."""
    try:
        if provider == "openai":
            return await _fetch_openai(api_key)
        if provider == "anthropic":
            return await _fetch_anthropic(api_key)
        if provider == "google":
            return await _fetch_google(api_key)
        return [], f"Unknown provider: {provider}"
    except httpx.HTTPStatusError as e:
        detail = _http_error_detail(e)
        fallback = PROVIDER_MODELS.get(provider, [])
        if fallback:
            return fallback, f"Could not reach {provider} API ({detail}). Showing default model list."
        return [], detail
    except httpx.RequestError as e:
        fallback = PROVIDER_MODELS.get(provider, [])
        if fallback:
            return fallback, f"Network error: {e}. Showing default model list."
        return [], str(e)


def _http_error_detail(e: httpx.HTTPStatusError) -> str:
    try:
        body = e.response.json()
        if isinstance(body, dict):
            err = body.get("error", body)
            if isinstance(err, dict):
                return err.get("message", str(err))
            return str(err)
    except Exception:
        pass
    return e.response.text[:200] or f"HTTP {e.response.status_code}"


async def _fetch_openai(api_key: str) -> tuple[list[str], str | None]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()

    models = []
    for item in data.get("data", []):
        model_id = item.get("id", "")
        if any(model_id.startswith(p) for p in OPENAI_CHAT_PREFIXES):
            if "instruct" not in model_id and "realtime" not in model_id:
                models.append(model_id)

    models = _sort_models(models, preferred=PROVIDER_MODELS["openai"])
    if not models:
        return PROVIDER_MODELS["openai"], "No chat models found — using defaults."
    return models, None


async def _fetch_anthropic(api_key: str) -> tuple[list[str], str | None]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    models = []
    for item in data.get("data", []):
        model_id = item.get("id", "")
        if ANTHROPIC_PREFIX in model_id:
            models.append(model_id)

    models = _sort_models(models, preferred=PROVIDER_MODELS["anthropic"])
    if not models:
        return PROVIDER_MODELS["anthropic"], "No Claude models found — using defaults."
    return models, None


async def _fetch_google(api_key: str) -> tuple[list[str], str | None]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    models = []
    for item in data.get("models", []):
        name = item.get("name", "")
        model_id = name.replace("models/", "") if name.startswith("models/") else name
        methods = item.get("supportedGenerationMethods", [])
        if GOOGLE_PREFIX in model_id.lower() and ("generateContent" in methods or not methods):
            models.append(model_id)

    models = _sort_models(models, preferred=PROVIDER_MODELS["google"])
    if not models:
        return PROVIDER_MODELS["google"], "No Gemini models found — using defaults."
    return models, None


def _sort_models(models: list[str], preferred: list[str]) -> list[str]:
    preferred_set = set(preferred)
    ranked = sorted(
        models,
        key=lambda m: (0 if m in preferred_set else 1, preferred.index(m) if m in preferred_set else m),
    )
    return ranked


def default_selected_models(provider: str, models: list[str]) -> list[str]:
    """Auto-select recommended models after fetch."""
    preferred = PROVIDER_MODELS.get(provider, [])
    selected = [m for m in preferred if m in models]
    if selected:
        return selected[:3]
    return models[:2] if len(models) >= 2 else models[:1]
