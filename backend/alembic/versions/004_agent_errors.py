"""Add agent error and token usage tracking

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("agents", sa.Column("tokens_used", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("agents", "tokens_used")
    op.drop_column("agents", "last_error")
