"""add experience to staging jobs

Revision ID: 5f1af0533f44
Revises: 0001
Create Date: 2026-06-06 16:10:53.417347

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f1af0533f44"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "jobs", sa.Column("experience_min", sa.SmallInteger(), nullable=True), schema="staging"
    )
    op.add_column(
        "jobs", sa.Column("experience_max", sa.SmallInteger(), nullable=True), schema="staging"
    )


def downgrade() -> None:
    op.drop_column("jobs", "experience_max", schema="staging")
    op.drop_column("jobs", "experience_min", schema="staging")
