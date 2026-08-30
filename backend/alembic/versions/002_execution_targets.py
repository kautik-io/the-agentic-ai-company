"""Add execution targets (VM/path/SSH)

Revision ID: 002
Revises: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "execution_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("target_type", sa.Enum("local", "ssh", "docker", name="executiontargettype"), nullable=False),
        sa.Column("workspace_path", sa.String(1000), nullable=False),
        sa.Column("host", sa.String(255), nullable=True),
        sa.Column("port", sa.Integer(), default=22),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("ssh_key_path", sa.String(1000), nullable=True),
        sa.Column("docker_image", sa.String(255), nullable=True),
        sa.Column("is_default", sa.Boolean(), default=False),
        sa.Column("status", sa.Enum("pending", "connected", "error", name="executiontargetstatus"), default="pending"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column(
        "agents",
        sa.Column("execution_target_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("execution_targets.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agents", "execution_target_id")
    op.drop_table("execution_targets")
    sa.Enum(name="executiontargettype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="executiontargetstatus").drop(op.get_bind(), checkfirst=True)
