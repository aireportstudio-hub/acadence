"""Establish the initial Billing Service migration baseline.

Revision ID: 0001_billing_baseline
Revises:
"""

from typing import Sequence, Union

revision: str = "0001_billing_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
