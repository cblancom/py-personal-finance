"""create ingresos

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-21 18:52:32.011893

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ingresos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=False),
        sa.Column("valor", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint(
            "length(trim(descripcion)) > 0", name="ck_ingresos_descripcion_no_vacia"
        ),
        sa.CheckConstraint("valor > 0", name="ck_ingresos_valor_positivo"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingresos_fecha", "ingresos", ["fecha"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ingresos_fecha", table_name="ingresos")
    op.drop_table("ingresos")
