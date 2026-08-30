from __future__ import annotations
import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models import (
    AuditLog,
    Organization,
    OrganizationMember,
    OrgRole,
    User,
)
from app.schemas.auth import OrganizationCreate, UserCreate


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug or "org"


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, data: UserCreate) -> User:
        existing = await db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")
        user = User(
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.hashed_password):
            return None
        return user


class OrganizationService:
    @staticmethod
    async def create(
        db: AsyncSession, user: User, data: OrganizationCreate
    ) -> Organization:
        base_slug = slugify(data.name)
        slug = base_slug
        counter = 1
        while True:
            existing = await db.execute(select(Organization).where(Organization.slug == slug))
            if existing.scalar_one_or_none() is None:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(name=data.name, slug=slug, description=data.description)
        db.add(org)
        await db.flush()

        membership = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=OrgRole.OWNER,
        )
        db.add(membership)

        audit = AuditLog(
            organization_id=org.id,
            user_id=user.id,
            action="organization.created",
            resource_type="organization",
            resource_id=str(org.id),
            new_value={"name": org.name, "slug": org.slug},
        )
        db.add(audit)
        await db.flush()
        return org

    @staticmethod
    async def list_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Organization]:
        result = await db.execute(
            select(Organization)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, org_id: uuid.UUID) -> Organization | None:
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_members(db: AsyncSession, org_id: uuid.UUID) -> list[OrganizationMember]:
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == org_id)
        )
        return list(result.scalars().all())
