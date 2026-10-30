"""create import tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-29 20:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "lotes_importacion",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre_archivo", sa.String(length=255), nullable=False),
        sa.Column("tipo_archivo", sa.String(length=10), nullable=False),
        sa.Column("tipo_movimiento", sa.String(length=10), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("total_filas", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("filas_importadas", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("filas_pendientes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("filas_descartadas", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "tipo_archivo IN ('CSV', 'XLSX')",
            name="ck_lotes_importacion_tipo_archivo_valido",
        ),
        sa.CheckConstraint(
            "tipo_movimiento IN ('INGRESO', 'GASTO')",
            name="ck_lotes_importacion_tipo_movimiento_valido",
        ),
        sa.CheckConstraint(
            "total_filas >= 0 AND filas_importadas >= 0 AND "
            "filas_pendientes >= 0 AND filas_descartadas >= 0",
            name="ck_lotes_importacion_contadores_no_negativos",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "filas_importacion",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lote_id", sa.Integer(), nullable=False),
        sa.Column("numero_fila", sa.Integer(), nullable=False),
        sa.Column("tipo_movimiento", sa.String(length=10), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("descripcion", sa.String(length=200), nullable=True),
        sa.Column("valor", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("categoria", sa.String(length=100), nullable=True),
        sa.Column("tipo_gasto", sa.String(length=20), nullable=True),
        sa.Column(
            "estado",
            sa.String(length=20),
            server_default=sa.text("'PENDIENTE'"),
            nullable=False,
        ),
        sa.Column(
            "errores",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "datos_originales",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("huella", sa.String(length=64), nullable=True),
        sa.Column(
            "posible_duplicado",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("duplicado_de_id", sa.Integer(), nullable=True),
        sa.Column("movimiento_ingreso_id", sa.Integer(), nullable=True),
        sa.Column("movimiento_gasto_id", sa.Integer(), nullable=True),
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
            "estado IN ('PENDIENTE', 'IMPORTADO', 'DESCARTADO')",
            name="ck_filas_importacion_estado_valido",
        ),
        sa.CheckConstraint(
            "tipo_movimiento IN ('INGRESO', 'GASTO')",
            name="ck_filas_importacion_tipo_movimiento_valido",
        ),
        sa.CheckConstraint(
            "tipo_gasto IS NULL OR tipo_gasto IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')",
            name="ck_filas_importacion_tipo_gasto_valido",
        ),
        sa.CheckConstraint(
            "tipo_movimiento = 'INGRESO' OR movimiento_ingreso_id IS NULL",
            name="ck_filas_importacion_ingreso_coherente",
        ),
        sa.CheckConstraint(
            "tipo_movimiento = 'GASTO' OR movimiento_gasto_id IS NULL",
            name="ck_filas_importacion_gasto_coherente",
        ),
        sa.CheckConstraint(
            "(estado = 'IMPORTADO' AND ((movimiento_ingreso_id IS NOT NULL) <> "
            "(movimiento_gasto_id IS NOT NULL))) OR "
            "(estado <> 'IMPORTADO' AND movimiento_ingreso_id IS NULL AND "
            "movimiento_gasto_id IS NULL)",
            name="ck_filas_importacion_referencia_movimiento",
        ),
        sa.ForeignKeyConstraint(
            ["duplicado_de_id"],
            ["filas_importacion.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["lote_id"],
            ["lotes_importacion.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["movimiento_gasto_id"],
            ["gastos.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["movimiento_ingreso_id"],
            ["ingresos.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lote_id", "numero_fila", name="uq_filas_importacion_lote_fila"),
    )
    op.create_index("ix_filas_importacion_estado", "filas_importacion", ["estado"])
    op.create_index("ix_filas_importacion_huella", "filas_importacion", ["huella"])
    op.create_index("ix_filas_importacion_lote_id", "filas_importacion", ["lote_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_filas_importacion_lote_id", table_name="filas_importacion")
    op.drop_index("ix_filas_importacion_huella", table_name="filas_importacion")
    op.drop_index("ix_filas_importacion_estado", table_name="filas_importacion")
    op.drop_table("filas_importacion")
    op.drop_table("lotes_importacion")
