"""Persist Project fact-update outbox events and related audit records.

Revision ID: 0003_project_events
Revises: 0002_project_projects
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_project_events"
down_revision: Union[str, None] = "0002_project_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        sa.Column("aggregate_id", sa.Uuid(), nullable=False),
        sa.Column("aggregate_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("event_version", sa.SmallInteger(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "event_type = 'project.facts.updated'",
            name="ck_project_outbox_event_type",
        ),
        sa.CheckConstraint(
            "payload ->> 'event_id' = event_id::text AND "
            "payload ->> 'event_type' = event_type AND "
            "payload ->> 'event_version' = event_version::text AND "
            "payload ->> 'aggregate_id' = aggregate_id::text AND "
            "payload ->> 'aggregate_version' = aggregate_version::text AND "
            "payload -> 'data' ->> 'fact_snapshot_version' = aggregate_version::text "
            "AND CASE "
            "WHEN jsonb_typeof(payload -> 'data' -> 'changed_fact_ids') = 'array' "
            "THEN jsonb_array_length(payload -> 'data' -> 'changed_fact_ids') > 0 "
            "ELSE false END",
            name="ck_project_outbox_payload_envelope",
        ),
        sa.CheckConstraint("event_version > 0", name="ck_project_outbox_event_version"),
        sa.CheckConstraint(
            "aggregate_version > 0", name="ck_project_outbox_aggregate_version"
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_project_outbox_attempt_count"),
        sa.UniqueConstraint(
            "aggregate_id",
            "aggregate_version",
            "event_type",
            name="uq_project_outbox_aggregate_event",
        ),
        schema="project",
    )
    op.create_index(
        "ix_project_outbox_pending",
        "outbox_events",
        ["next_attempt_at", "created_at"],
        schema="project",
        postgresql_where=sa.text("published_at IS NULL"),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("service_identity", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("object_type", sa.Text(), nullable=False),
        sa.Column("object_id", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="project",
    )
    op.create_index(
        "ix_project_audit_object",
        "audit_events",
        ["object_type", "object_id", "occurred_at"],
        schema="project",
    )

    op.execute(
        "GRANT SELECT, INSERT ON TABLE project.outbox_events "
        "TO acadence_project_runtime"
    )
    op.execute(
        "GRANT UPDATE (published_at, attempt_count, next_attempt_at) "
        "ON TABLE project.outbox_events TO acadence_project_runtime"
    )
    op.execute(
        "GRANT SELECT, INSERT ON TABLE project.audit_events "
        "TO acadence_project_runtime"
    )


def downgrade() -> None:
    op.drop_table("audit_events", schema="project")
    op.drop_index(
        "ix_project_outbox_pending",
        table_name="outbox_events",
        schema="project",
    )
    op.drop_table("outbox_events", schema="project")
