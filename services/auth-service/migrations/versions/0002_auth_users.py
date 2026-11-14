"""Create Auth-owned users.

Revision ID: 0002_auth_users
Revises: 0001_auth_baseline
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_auth_users"
down_revision: Union[str, None] = "0001_auth_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="auth",
    )
    op.execute("GRANT SELECT, INSERT ON TABLE auth.users TO acadence_auth_runtime")


def downgrade() -> None:
    op.drop_table("users", schema="auth")
