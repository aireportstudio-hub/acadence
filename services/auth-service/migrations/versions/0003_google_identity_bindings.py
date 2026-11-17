"""Add verified provider identity bindings.

Revision ID: 0003_google_identity_bindings
Revises: 0002_auth_users
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_google_identity_bindings"
down_revision: Union[str, None] = "0002_auth_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "identity_bindings",
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth.users.id"],
            name="fk_identity_bindings_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "provider",
            "subject",
            name="pk_identity_bindings",
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            name="uq_identity_bindings_user_provider",
        ),
        schema="auth",
    )
    op.execute(
        "GRANT SELECT, INSERT ON TABLE auth.identity_bindings "
        "TO acadence_auth_runtime"
    )


def downgrade() -> None:
    op.drop_table("identity_bindings", schema="auth")
