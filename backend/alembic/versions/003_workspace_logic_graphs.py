"""Add workspace_path and logic_graph to projects, epics, features

Revision ID: 003
Revises: 002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("workspace_path", sa.String(1000), nullable=True))
    op.add_column("projects", sa.Column("logic_graph", sa.Text(), nullable=True))
    op.add_column("epics", sa.Column("logic_graph", sa.Text(), nullable=True))
    op.add_column("features", sa.Column("logic_graph", sa.Text(), nullable=True))
    op.add_column("features", sa.Column("slug", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("features", "slug")
    op.drop_column("features", "logic_graph")
    op.drop_column("epics", "logic_graph")
    op.drop_column("projects", "logic_graph")
    op.drop_column("projects", "workspace_path")
