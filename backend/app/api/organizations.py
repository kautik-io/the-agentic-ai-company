import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_org_membership
from app.models import User
from app.schemas.auth import (
    DepartmentCreate,
    DepartmentResponse,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.auth import OrganizationService
from app.services.project import DepartmentService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org = await OrganizationService.create(db, current_user, data)
    return org


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await OrganizationService.list_for_user(db, current_user.id)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org = await OrganizationService.get_by_id(db, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    data: OrganizationUpdate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org = await OrganizationService.get_by_id(db, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(org, key, value)
    await db.flush()
    return org


@router.get("/{org_id}/members", response_model=list[OrganizationMemberResponse])
async def list_members(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await OrganizationService.list_members(db, org_id)


@router.post("/{org_id}/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    org_id: uuid.UUID,
    data: DepartmentCreate,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await DepartmentService.create(db, org_id, data.name, data.description)


@router.get("/{org_id}/departments", response_model=list[DepartmentResponse])
async def list_departments(
    org_id: uuid.UUID,
    membership: Annotated[object, Depends(get_org_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await DepartmentService.list(db, org_id)
