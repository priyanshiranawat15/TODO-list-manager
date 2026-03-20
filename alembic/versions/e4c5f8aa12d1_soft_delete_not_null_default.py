"""soft delete set default not null

Revision ID: e4c5f8aa12d1
Revises: d3bc9a626301
Create Date: 2026-03-19 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4c5f8aa12d1"
down_revision: Union[str, None] = "d3bc9a626301"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Backfill existing rows before making the column non-null.
    op.execute('UPDATE tasks SET "isDeleted" = false WHERE "isDeleted" IS NULL')
    op.alter_column(
        "tasks",
        "isDeleted",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    )


def downgrade() -> None:
    op.alter_column(
        "tasks",
        "isDeleted",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
