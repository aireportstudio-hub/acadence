"""Create the first Project-owned persistence table.

Revision ID: 0002_project_projects
Revises: 0001_project_baseline
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_project_projects"
down_revision: Union[str, None] = "0001_project_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        schema="project",
    )
    op.execute(
        "GRANT SELECT, INSERT ON TABLE project.projects TO acadence_project_runtime"
    )


def downgrade() -> None:
    op.drop_table("projects", schema="project")
