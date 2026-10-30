"""add income category

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-29 20:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("ingresos", sa.Column("categoria", sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ingresos", "categoria")
