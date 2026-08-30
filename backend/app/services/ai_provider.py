from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AiProviderConfig
from app.schemas.ai_provider import AiProviderCreate, AiProviderUpdate

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google AI",
}

PROVIDER_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini", "o1"],
    "anthropic": [
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ],
    "google": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
}


def mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


class AiProviderService:
    @staticmethod
    def catalog() -> list[dict]:
        return [
            {"provider": p, "label": PROVIDER_LABELS[p], "models": models}
            for p, models in PROVIDER_MODELS.items()
        ]

    @staticmethod
    async def list(db: AsyncSession, org_id: uuid.UUID, active_only: bool = False) -> list[AiProviderConfig]:
        query = select(AiProviderConfig).where(AiProviderConfig.organization_id == org_id)
        if active_only:
            query = query.where(AiProviderConfig.is_active.is_(True))
        query = query.order_by(AiProviderConfig.provider)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, config_id: uuid.UUID) -> AiProviderConfig | None:
        result = await db.execute(
            select(AiProviderConfig).where(
                AiProviderConfig.id == config_id,
                AiProviderConfig.organization_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_provider(db: AsyncSession, org_id: uuid.UUID, provider: str) -> AiProviderConfig | None:
        result = await db.execute(
            select(AiProviderConfig).where(
                AiProviderConfig.organization_id == org_id,
                AiProviderConfig.provider == provider,
                AiProviderConfig.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def configured_providers(db: AsyncSession, org_id: uuid.UUID) -> set[str]:
        configs = await AiProviderService.list(db, org_id, active_only=True)
        return {c.provider for c in configs if c.api_key}

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: AiProviderCreate) -> AiProviderConfig:
        enabled = [m.strip() for m in data.enabled_models if m.strip()]
        if not enabled:
            raise ValueError("Select at least one model")

        existing = await db.execute(
            select(AiProviderConfig).where(
                AiProviderConfig.organization_id == org_id,
                AiProviderConfig.provider == data.provider,
            )
        )
        config = existing.scalar_one_or_none()
        if config:
            config.api_key = data.api_key
            config.enabled_models = enabled
            config.is_active = True
            await db.flush()
            return config

        config = AiProviderConfig(
            organization_id=org_id,
            provider=data.provider,
            api_key=data.api_key,
            enabled_models=enabled,
        )
        db.add(config)
        await db.flush()
        return config

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, config_id: uuid.UUID, data: AiProviderUpdate
    ) -> AiProviderConfig | None:
        config = await AiProviderService.get(db, org_id, config_id)
        if config is None:
            return None
        payload = data.model_dump(exclude_unset=True)
        if "enabled_models" in payload:
            payload["enabled_models"] = [m.strip() for m in payload["enabled_models"] if m.strip()]
            if not payload["enabled_models"]:
                raise ValueError("At least one model required")
        if "api_key" in payload:
            if payload["api_key"]:
                config.api_key = payload.pop("api_key")
            else:
                payload.pop("api_key")
        for key, value in payload.items():
            setattr(config, key, value)
        await db.flush()
        return config

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, config_id: uuid.UUID) -> bool:
        config = await AiProviderService.get(db, org_id, config_id)
        if config is None:
            return False
        await db.delete(config)
        await db.flush()
        return True

    @staticmethod
    async def validate_agent_provider(
        db: AsyncSession, org_id: uuid.UUID, provider: str, model: str
    ) -> None:
        config = await AiProviderService.get_by_provider(db, org_id, provider)
        if config is None:
            raise ValueError(
                f"No API key configured for {PROVIDER_LABELS.get(provider, provider)}. "
                "Add it in Settings → AI Provider Keys."
            )
        if model not in config.enabled_models:
            raise ValueError(
                f"Model '{model}' is not enabled for this provider. Enable it in Settings → AI Provider Keys."
            )
