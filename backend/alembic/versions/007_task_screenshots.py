"""Task completion screenshots for feature-wise review

Revision ID: 007
Revises: 006
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task_screenshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("features.id", ondelete="SET NULL"), nullable=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_task_screenshots_task_id", "task_screenshots", ["task_id"])
    op.create_index("ix_task_screenshots_feature_id", "task_screenshots", ["feature_id"])


def downgrade() -> None:
    op.drop_index("ix_task_screenshots_feature_id", table_name="task_screenshots")
    op.drop_index("ix_task_screenshots_task_id", table_name="task_screenshots")
    op.drop_table("task_screenshots")
