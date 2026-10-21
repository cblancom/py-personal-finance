"""create gastos

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-21 20:33:10.622672

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "gastos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("valor", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint(
            "tipo IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')", name="ck_gastos_tipo_valido"
        ),
        sa.CheckConstraint("length(trim(descripcion)) > 0", name="ck_gastos_descripcion_no_vacia"),
        sa.CheckConstraint("valor > 0", name="ck_gastos_valor_positivo"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gastos_fecha", "gastos", ["fecha"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_gastos_fecha", table_name="gastos")
    op.drop_table("gastos")
