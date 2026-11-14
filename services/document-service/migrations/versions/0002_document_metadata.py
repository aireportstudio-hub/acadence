"""Persist private document object metadata, immutable versions, and access history.

Revision ID: 0002_doc_metadata
Revises: 0001_document_baseline
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_doc_metadata"
down_revision: Union[str, None] = "0001_document_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_objects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Text(), nullable=True),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "report_id IS NULL OR length(btrim(report_id)) > 0",
            name="ck_document_objects_report_id",
        ),
        schema="document",
    )
    op.create_index(
        "ix_document_objects_project_created",
        "document_objects",
        ["project_id", "created_at"],
        schema="document",
    )

    op.create_table(
        "document_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "document_object_id",
            sa.Uuid(),
            sa.ForeignKey("document.document_objects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("r2_bucket", sa.Text(), nullable=False),
        sa.Column("r2_object_key", sa.Text(), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "version_number > 0", name="ck_document_versions_number_positive"
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_document_versions_size"),
        sa.CheckConstraint(
            "checksum_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_document_versions_checksum",
        ),
        sa.CheckConstraint(
            "length(btrim(r2_bucket)) > 0 AND length(btrim(r2_object_key)) > 0 "
            "AND r2_object_key !~ '^[A-Za-z][A-Za-z0-9+.-]*://'",
            name="ck_document_versions_private_object_key",
        ),
        sa.UniqueConstraint(
            "document_object_id",
            "version_number",
            name="uq_document_versions_number",
        ),
        sa.UniqueConstraint("r2_bucket", "r2_object_key", name="uq_document_versions_r2_ref"),
        schema="document",
    )
    op.create_index(
        "ix_document_versions_object_created",
        "document_versions",
        ["document_object_id", "created_at"],
        schema="document",
    )

    op.create_table(
        "document_access_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "document_version_id",
            sa.Uuid(),
            sa.ForeignKey("document.document_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("access_action", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column(
            "accessed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "access_action IN ('upload', 'download', 'preview', 'metadata_read', 'delete')",
            name="ck_document_access_action",
        ),
        sa.CheckConstraint(
            "result IN ('success', 'denied', 'failed')",
            name="ck_document_access_result",
        ),
        schema="document",
    )
    op.create_index(
        "ix_document_access_history_version_time",
        "document_access_history",
        ["document_version_id", "accessed_at"],
        schema="document",
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
        schema="document",
    )
    op.create_index(
        "ix_document_audit_object",
        "audit_events",
        ["object_type", "object_id", "occurred_at"],
        schema="document",
    )

    op.execute(
        "GRANT SELECT, INSERT ON TABLE document.document_objects, "
        "document.document_versions, document.document_access_history, "
        "document.audit_events TO acadence_document_runtime"
    )


def downgrade() -> None:
    op.drop_table("audit_events", schema="document")
    op.drop_index(
        "ix_document_access_history_version_time",
        table_name="document_access_history",
        schema="document",
    )
    op.drop_table("document_access_history", schema="document")
    op.drop_index(
        "ix_document_versions_object_created",
        table_name="document_versions",
        schema="document",
    )
    op.drop_table("document_versions", schema="document")
    op.drop_index(
        "ix_document_objects_project_created",
        table_name="document_objects",
        schema="document",
    )
    op.drop_table("document_objects", schema="document")
