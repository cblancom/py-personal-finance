from datetime import date as DateType
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.import_batch import ImportBatch


class ImportRowStatus(StrEnum):
    PENDING = "PENDIENTE"
    IMPORTED = "IMPORTADO"
    DISCARDED = "DESCARTADO"


class ImportRow(Base):
    __tablename__ = "filas_importacion"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('PENDIENTE', 'IMPORTADO', 'DESCARTADO')",
            name="ck_filas_importacion_estado_valido",
        ),
        CheckConstraint(
            "tipo_movimiento IN ('INGRESO', 'GASTO')",
            name="ck_filas_importacion_tipo_movimiento_valido",
        ),
        CheckConstraint(
            "tipo_gasto IS NULL OR tipo_gasto IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')",
            name="ck_filas_importacion_tipo_gasto_valido",
        ),
        CheckConstraint(
            "tipo_movimiento = 'INGRESO' OR movimiento_ingreso_id IS NULL",
            name="ck_filas_importacion_ingreso_coherente",
        ),
        CheckConstraint(
            "tipo_movimiento = 'GASTO' OR movimiento_gasto_id IS NULL",
            name="ck_filas_importacion_gasto_coherente",
        ),
        CheckConstraint(
            "(movimiento_ingreso_id IS NULL OR movimiento_gasto_id IS NULL) AND "
            "(estado = 'IMPORTADO' OR "
            "(movimiento_ingreso_id IS NULL AND movimiento_gasto_id IS NULL))",
            name="ck_filas_importacion_referencia_movimiento",
        ),
        UniqueConstraint(
            "lote_id",
            "numero_fila",
            name="uq_filas_importacion_lote_fila",
        ),
        Index("ix_filas_importacion_lote_id", "lote_id"),
        Index("ix_filas_importacion_estado", "estado"),
        Index("ix_filas_importacion_huella", "huella"),
    )

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        "lote_id",
        ForeignKey("lotes_importacion.id", ondelete="CASCADE"),
        nullable=False,
    )
    row_number: Mapped[int] = mapped_column("numero_fila", Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column("tipo_movimiento", String(10), nullable=False)
    date: Mapped[DateType | None] = mapped_column("fecha", Date, nullable=True)
    description: Mapped[str | None] = mapped_column("descripcion", String(200), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column("valor", Numeric(12, 2), nullable=True)
    category: Mapped[str | None] = mapped_column("categoria", String(100), nullable=True)
    expense_type: Mapped[str | None] = mapped_column("tipo_gasto", String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        "estado",
        String(20),
        nullable=False,
        default=ImportRowStatus.PENDING.value,
        server_default=text("'PENDIENTE'"),
    )
    errors: Mapped[list[dict[str, str]]] = mapped_column(
        "errores",
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    raw_data: Mapped[dict[str, object]] = mapped_column(
        "datos_originales",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    fingerprint: Mapped[str | None] = mapped_column("huella", String(64), nullable=True)
    possible_duplicate: Mapped[bool] = mapped_column(
        "posible_duplicado",
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    duplicate_of_id: Mapped[int | None] = mapped_column(
        "duplicado_de_id",
        ForeignKey("filas_importacion.id", ondelete="SET NULL"),
        nullable=True,
    )
    income_id: Mapped[int | None] = mapped_column(
        "movimiento_ingreso_id",
        ForeignKey("ingresos.id", ondelete="SET NULL"),
        nullable=True,
    )
    expense_id: Mapped[int | None] = mapped_column(
        "movimiento_gasto_id",
        ForeignKey("gastos.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    batch: Mapped["ImportBatch"] = relationship(back_populates="rows")
