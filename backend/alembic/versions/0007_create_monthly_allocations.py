"""create monthly allocations

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-31 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "asignaciones_mensuales",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column(
            "porcentaje_necesario",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "porcentaje_no_necesario",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "porcentaje_inversion",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0.00"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "anio BETWEEN 1900 AND 2100",
            name="ck_asignaciones_mensuales_anio_valido",
        ),
        sa.CheckConstraint(
            "mes BETWEEN 1 AND 12",
            name="ck_asignaciones_mensuales_mes_valido",
        ),
        sa.CheckConstraint(
            "porcentaje_necesario BETWEEN 0 AND 100",
            name="ck_asignaciones_mensuales_porcentaje_necesario_valido",
        ),
        sa.CheckConstraint(
            "porcentaje_no_necesario BETWEEN 0 AND 100",
            name="ck_asignaciones_mensuales_porcentaje_no_necesario_valido",
        ),
        sa.CheckConstraint(
            "porcentaje_inversion BETWEEN 0 AND 100",
            name="ck_asignaciones_mensuales_porcentaje_inversion_valido",
        ),
        sa.CheckConstraint(
            "porcentaje_necesario + porcentaje_no_necesario + porcentaje_inversion <= 100",
            name="ck_asignaciones_mensuales_suma_valida",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "anio",
            "mes",
            name="uq_asignaciones_mensuales_anio_mes",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("asignaciones_mensuales")
