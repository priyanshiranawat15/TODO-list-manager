"""enable multi agent sessions

Revision ID: 0a91f4b92311
Revises: fa0dcef53831
Create Date: 2026-03-20 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a91f4b92311"
down_revision: Union[str, None] = "fa0dcef53831"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx.get("name") == index_name for idx in indexes)


def _find_user_id_unique_name() -> str | None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    constraints = inspector.get_unique_constraints("agent_sessions")
    for constraint in constraints:
        if constraint.get("column_names") == ["user_id"]:
            return constraint.get("name")
    return None


def upgrade() -> None:
    user_unique_name = _find_user_id_unique_name()
    if user_unique_name:
        op.drop_constraint(user_unique_name, "agent_sessions", type_="unique")

    if not _index_exists("agent_sessions", "ix_agent_sessions_user_id"):
        op.create_index("ix_agent_sessions_user_id", "agent_sessions", ["user_id"], unique=False)

    if not _index_exists("messages", "ix_messages_session_id"):
        op.create_index("ix_messages_session_id", "messages", ["session_id"], unique=False)


def downgrade() -> None:
    if _index_exists("messages", "ix_messages_session_id"):
        op.drop_index("ix_messages_session_id", table_name="messages")

    if _index_exists("agent_sessions", "ix_agent_sessions_user_id"):
        op.drop_index("ix_agent_sessions_user_id", table_name="agent_sessions")

    user_unique_name = _find_user_id_unique_name()
    if not user_unique_name:
        op.create_unique_constraint("agent_sessions_user_id_key", "agent_sessions", ["user_id"])
