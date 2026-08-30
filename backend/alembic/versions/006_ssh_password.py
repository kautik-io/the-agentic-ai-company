"""Add optional SSH password for execution targets

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("execution_targets", sa.Column("ssh_password", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("execution_targets", "ssh_password")
