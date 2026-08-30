from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_org_membership
from app.schemas.execution_target import (
    ConnectionTestResult,
    ExecutionTargetCreate,
    ExecutionTargetResponse,
    ExecutionTargetUpdate,
)
from app.services.execution_target import ExecutionTargetService

router = APIRouter(prefix="/organizations/{org_id}/execution-targets", tags=["execution-targets"])


@router.get("", response_model=list[ExecutionTargetResponse])
async def list_targets(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ExecutionTargetService.list(db, org_id)


@router.post("", response_model=ExecutionTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    org_id: uuid.UUID,
    data: ExecutionTargetCreate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ExecutionTargetService.create(db, org_id, data)


@router.get("/{target_id}", response_model=ExecutionTargetResponse)
async def get_target(
    org_id: uuid.UUID,
    target_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    target = await ExecutionTargetService.get(db, org_id, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Execution target not found")
    return target


@router.patch("/{target_id}", response_model=ExecutionTargetResponse)
async def update_target(
    org_id: uuid.UUID,
    target_id: uuid.UUID,
    data: ExecutionTargetUpdate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    target = await ExecutionTargetService.update(db, org_id, target_id, data)
    if target is None:
        raise HTTPException(status_code=404, detail="Execution target not found")
    return target


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    org_id: uuid.UUID,
    target_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    deleted = await ExecutionTargetService.delete(db, org_id, target_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Execution target not found")


@router.post("/{target_id}/test", response_model=ConnectionTestResult)
async def test_target(
    org_id: uuid.UUID,
    target_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    target = await ExecutionTargetService.get(db, org_id, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Execution target not found")
    target = await ExecutionTargetService.run_test(db, target)
    ok = target.status.value == "connected"
    return ConnectionTestResult(
        success=ok,
        message=target.last_error or f"Target verified at {target.last_verified_at}",
        status=target.status.value,
    )
