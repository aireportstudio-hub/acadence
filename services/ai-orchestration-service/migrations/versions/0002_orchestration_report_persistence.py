"""Persist report jobs, resume inputs, progress, sections, checkpoints, and events.

Revision ID: 0002_orch_persistence
Revises: 0001_orchestration_baseline
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_orch_persistence"
down_revision: Union[str, None] = "0001_orchestration_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("report_id", sa.Text(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("reservation_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("graph_thread_id", sa.Text(), nullable=False),
        sa.Column("execution_id", sa.Text(), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'awaiting_answer', 'completed', "
            "'failed', 'canceled')",
            name="ck_report_jobs_status",
        ),
        sa.CheckConstraint(
            "length(btrim(report_id)) > 0", name="ck_report_jobs_report_id"
        ),
        sa.UniqueConstraint("id", "project_id", name="uq_report_jobs_id_project"),
        sa.UniqueConstraint("graph_thread_id", name="uq_report_jobs_graph_thread"),
        schema="orchestration",
    )
    op.create_index(
        "ix_report_jobs_project_created",
        "report_jobs",
        ["project_id", "created_at"],
        schema="orchestration",
    )

    op.create_table(
        "job_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("orchestration.report_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("execution_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("retryable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failure_code", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("attempt_number > 0", name="ck_job_attempts_number_positive"),
        sa.CheckConstraint(
            "status IN ('running', 'succeeded', 'retrying', 'failed', 'canceled')",
            name="ck_job_attempts_status",
        ),
        sa.UniqueConstraint("job_id", "attempt_number", name="uq_job_attempts_number"),
        schema="orchestration",
    )

    op.create_table(
        "section_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("orchestration.report_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("output_sha256", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "version_number > 0", name="ck_section_versions_number_positive"
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'revision_needed')",
            name="ck_section_versions_status",
        ),
        sa.CheckConstraint(
            "output_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_section_versions_sha256",
        ),
        sa.UniqueConstraint(
            "job_id", "section_id", "version_number", name="uq_section_versions_number"
        ),
        sa.UniqueConstraint("job_id", "id", name="uq_section_versions_job_id"),
        schema="orchestration",
    )

    op.create_table(
        "input_version_refs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("orchestration.report_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "section_version_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("source_service", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "(scope = 'job' AND section_version_id IS NULL) OR "
            "(scope = 'section' AND section_version_id IS NOT NULL)",
            name="ck_input_version_refs_scope",
        ),
        sa.ForeignKeyConstraint(
            ["job_id", "section_version_id"],
            ["orchestration.section_versions.job_id", "orchestration.section_versions.id"],
            ondelete="CASCADE",
            name="fk_input_version_refs_section_version",
        ),
        schema="orchestration",
    )
    op.create_index(
        "uq_input_version_refs_job_snapshot",
        "input_version_refs",
        ["job_id", "source_service", "resource_type", "resource_id", "version"],
        unique=True,
        schema="orchestration",
        postgresql_where=sa.text("section_version_id IS NULL"),
    )
    op.create_index(
        "uq_input_version_refs_section_snapshot",
        "input_version_refs",
        [
            "job_id",
            "section_version_id",
            "source_service",
            "resource_type",
            "resource_id",
            "version",
        ],
        unique=True,
        schema="orchestration",
        postgresql_where=sa.text("section_version_id IS NOT NULL"),
    )
    op.create_index(
        "ix_input_version_refs_job",
        "input_version_refs",
        ["job_id", "captured_at"],
        schema="orchestration",
    )

    op.create_table(
        "progress_events",
        sa.Column(
            "event_id",
            sa.BigInteger(),
            sa.Identity(always=False),
            primary_key=True,
        ),
        sa.Column(
            "job_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("event_version", sa.SmallInteger(), nullable=False),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=True),
        sa.Column("artifact_version_id", sa.Uuid(), nullable=True),
        sa.Column("safe_message", sa.Text(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("event_version > 0", name="ck_progress_events_version"),
        sa.ForeignKeyConstraint(
            ["job_id", "project_id"],
            ["orchestration.report_jobs.id", "orchestration.report_jobs.project_id"],
            ondelete="CASCADE",
            name="fk_progress_events_job_project",
        ),
        sa.UniqueConstraint("job_id", "event_id", name="uq_progress_events_job_event"),
        schema="orchestration",
    )
    op.create_index(
        "ix_progress_events_job_cursor",
        "progress_events",
        ["job_id", "event_id"],
        schema="orchestration",
    )

    op.create_table(
        "checkpoint_references",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("orchestration.report_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("thread_id", sa.Text(), nullable=False),
        sa.Column("checkpoint_namespace", sa.Text(), nullable=False),
        sa.Column("checkpoint_id", sa.Text(), nullable=False),
        sa.Column(
            "checkpoint_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "job_id",
            "thread_id",
            "checkpoint_namespace",
            "checkpoint_id",
            name="uq_checkpoint_references_checkpoint",
        ),
        schema="orchestration",
    )

    op.create_table(
        "inbox_deduplication",
        sa.Column("producer_service", sa.Text(), primary_key=True),
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("event_version", sa.SmallInteger(), nullable=False),
        sa.Column("processing_status", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("event_version > 0", name="ck_inbox_event_version"),
        sa.CheckConstraint(
            "processing_status IN ('received', 'processed', 'failed')",
            name="ck_inbox_processing_status",
        ),
        schema="orchestration",
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
        schema="orchestration",
    )
    op.create_index(
        "ix_orchestration_audit_object",
        "audit_events",
        ["object_type", "object_id", "occurred_at"],
        schema="orchestration",
    )

    op.execute(
        "GRANT SELECT, INSERT ON TABLE orchestration.report_jobs, "
        "orchestration.job_attempts TO acadence_orchestration_runtime"
    )
    op.execute(
        "GRANT UPDATE (status, execution_id, heartbeat_at, updated_at) "
        "ON TABLE orchestration.report_jobs TO acadence_orchestration_runtime"
    )
    op.execute(
        "GRANT UPDATE (status, execution_id, retryable, failure_code, finished_at) "
        "ON TABLE orchestration.job_attempts TO acadence_orchestration_runtime"
    )
    op.execute(
        "GRANT SELECT, INSERT ON TABLE orchestration.section_versions, "
        "orchestration.input_version_refs, orchestration.progress_events, "
        "orchestration.checkpoint_references, orchestration.audit_events "
        "TO acadence_orchestration_runtime"
    )
    op.execute(
        "GRANT SELECT, INSERT ON TABLE orchestration.inbox_deduplication "
        "TO acadence_orchestration_runtime"
    )
    op.execute(
        "GRANT UPDATE (processing_status, processed_at) "
        "ON TABLE orchestration.inbox_deduplication "
        "TO acadence_orchestration_runtime"
    )
    op.execute(
        "GRANT USAGE, SELECT ON SEQUENCE orchestration.progress_events_event_id_seq "
        "TO acadence_orchestration_runtime"
    )


def downgrade() -> None:
    op.drop_table("audit_events", schema="orchestration")
    op.drop_table("inbox_deduplication", schema="orchestration")
    op.drop_table("checkpoint_references", schema="orchestration")
    op.drop_index(
        "ix_progress_events_job_cursor", table_name="progress_events", schema="orchestration"
    )
    op.drop_table("progress_events", schema="orchestration")
    op.drop_index(
        "uq_input_version_refs_section_snapshot",
        table_name="input_version_refs",
        schema="orchestration",
    )
    op.drop_index(
        "uq_input_version_refs_job_snapshot",
        table_name="input_version_refs",
        schema="orchestration",
    )
    op.drop_index(
        "ix_input_version_refs_job",
        table_name="input_version_refs",
        schema="orchestration",
    )
    op.drop_table("input_version_refs", schema="orchestration")
    op.drop_table("section_versions", schema="orchestration")
    op.drop_table("job_attempts", schema="orchestration")
    op.drop_index(
        "ix_report_jobs_project_created",
        table_name="report_jobs",
        schema="orchestration",
    )
    op.drop_table("report_jobs", schema="orchestration")
