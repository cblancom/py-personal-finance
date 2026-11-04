"""add income type

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-03 20:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _normalized_category_sql(column: str) -> str:
    return (
        "regexp_replace("
        f"translate(lower(trim({column})), 'áéíóúü_-', 'aeiouu  '), "
        "'\\s+', ' ', 'g'"
        ")"
    )


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("ingresos", sa.Column("tipo", sa.String(length=20), nullable=True))
    op.execute(
        f"""
        UPDATE ingresos
        SET tipo = CASE {_normalized_category_sql("categoria")}
            WHEN 'necesario' THEN 'NECESARIO'
            WHEN 'no necesario' THEN 'NO_NECESARIO'
            WHEN 'inversion' THEN 'INVERSION'
            ELSE NULL
        END
        WHERE categoria IS NOT NULL
        """
    )
    op.create_check_constraint(
        "ck_ingresos_tipo_valido",
        "ingresos",
        "tipo IS NULL OR tipo IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')",
    )
    op.drop_column("ingresos", "categoria")

    op.add_column(
        "filas_importacion",
        sa.Column("tipo", sa.String(length=20), nullable=True),
    )
    op.execute(
        f"""
        UPDATE filas_importacion
        SET tipo = CASE {_normalized_category_sql("categoria")}
            WHEN 'necesario' THEN 'NECESARIO'
            WHEN 'no necesario' THEN 'NO_NECESARIO'
            WHEN 'inversion' THEN 'INVERSION'
            ELSE NULL
        END
        WHERE tipo_movimiento = 'INGRESO' AND categoria IS NOT NULL
        """
    )
    op.create_check_constraint(
        "ck_filas_importacion_tipo_valido",
        "filas_importacion",
        "tipo IS NULL OR tipo IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_filas_importacion_tipo_valido",
        "filas_importacion",
        type_="check",
    )
    op.drop_column("filas_importacion", "tipo")

    op.drop_constraint("ck_ingresos_tipo_valido", "ingresos", type_="check")
    op.add_column("ingresos", sa.Column("categoria", sa.String(length=100), nullable=True))
    op.drop_column("ingresos", "tipo")
