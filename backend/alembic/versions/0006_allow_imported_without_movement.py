"""allow imported rows without movement

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-31 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT_NAME = "ck_filas_importacion_referencia_movimiento"

NEW_CHECK = (
    "(movimiento_ingreso_id IS NULL OR movimiento_gasto_id IS NULL) AND "
    "(estado = 'IMPORTADO' OR "
    "(movimiento_ingreso_id IS NULL AND movimiento_gasto_id IS NULL))"
)

OLD_CHECK = (
    "(estado = 'IMPORTADO' AND ((movimiento_ingreso_id IS NOT NULL) <> "
    "(movimiento_gasto_id IS NOT NULL))) OR "
    "(estado <> 'IMPORTADO' AND movimiento_ingreso_id IS NULL AND "
    "movimiento_gasto_id IS NULL)"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(CONSTRAINT_NAME, "filas_importacion", type_="check")
    op.create_check_constraint(CONSTRAINT_NAME, "filas_importacion", NEW_CHECK)


def downgrade() -> None:
    """Downgrade schema."""
    orphans = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT count(*) FROM filas_importacion "
                "WHERE estado = 'IMPORTADO' "
                "AND movimiento_ingreso_id IS NULL "
                "AND movimiento_gasto_id IS NULL"
            )
        )
        .scalar_one()
    )
    if orphans:
        raise RuntimeError(
            "No se puede revertir 0006: existen filas importadas sin movimiento. "
            "Resuelve esas filas antes de ejecutar el downgrade."
        )

    op.drop_constraint(CONSTRAINT_NAME, "filas_importacion", type_="check")
    op.create_check_constraint(CONSTRAINT_NAME, "filas_importacion", OLD_CHECK)
