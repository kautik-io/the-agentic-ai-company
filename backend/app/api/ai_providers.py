from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_org_membership
from app.schemas.ai_provider import (
    AiProviderCreate,
    AiProviderResponse,
    AiProviderUpdate,
    FetchModelsRequest,
    FetchModelsResponse,
    ProviderModelCatalog,
)
from app.services.ai_provider import AiProviderService, mask_api_key
from app.services.provider_models_fetch import default_selected_models, fetch_models_from_provider

router = APIRouter(prefix="/organizations/{org_id}/ai-providers", tags=["ai-providers"])


def _to_response(config) -> AiProviderResponse:
    return AiProviderResponse(
        id=config.id,
        organization_id=config.organization_id,
        provider=config.provider,
        api_key_masked=mask_api_key(config.api_key),
        enabled_models=config.enabled_models,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("/catalog", response_model=list[ProviderModelCatalog])
async def get_model_catalog(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
):
    return AiProviderService.catalog()


@router.post("/fetch-models", response_model=FetchModelsResponse)
async def fetch_models(
    org_id: uuid.UUID,
    data: FetchModelsRequest,
    membership: Annotated[object, Depends(get_org_membership)],
):
    models, message = await fetch_models_from_provider(data.provider, data.api_key)
    if not models:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message or "No models returned")
    recommended = default_selected_models(data.provider, models)
    return FetchModelsResponse(
        provider=data.provider,
        models=models,
        recommended=recommended,
        message=message,
    )


@router.get("", response_model=list[AiProviderResponse])
async def list_providers(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    configs = await AiProviderService.list(db, org_id)
    return [_to_response(c) for c in configs]


@router.post("", response_model=AiProviderResponse, status_code=status.HTTP_201_CREATED)
async def save_provider(
    org_id: uuid.UUID,
    data: AiProviderCreate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        config = await AiProviderService.create(db, org_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_response(config)


@router.patch("/{config_id}", response_model=AiProviderResponse)
async def update_provider(
    org_id: uuid.UUID,
    config_id: uuid.UUID,
    data: AiProviderUpdate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        config = await AiProviderService.update(db, org_id, config_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if config is None:
        raise HTTPException(status_code=404, detail="Provider config not found")
    return _to_response(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    org_id: uuid.UUID,
    config_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    deleted = await AiProviderService.delete(db, org_id, config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider config not found")
