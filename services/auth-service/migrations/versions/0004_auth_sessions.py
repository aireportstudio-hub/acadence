"""Add revocable server-managed authentication sessions.

Revision ID: 0004_auth_sessions
Revises: 0003_google_identity_bindings
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_auth_sessions"
down_revision: Union[str, None] = "0003_google_identity_bindings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_sessions_token_hash_sha256",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth.users.id"],
            name="fk_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("token_hash", name="pk_sessions"),
        schema="auth",
    )
    op.create_index(
        "ix_sessions_user_id_expires_at",
        "sessions",
        ["user_id", "expires_at"],
        schema="auth",
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON TABLE auth.sessions "
        "TO acadence_auth_runtime"
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sessions_user_id_expires_at",
        table_name="sessions",
        schema="auth",
    )
    op.drop_table("sessions", schema="auth")
