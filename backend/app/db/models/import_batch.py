from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.import_row import ImportRow


class ImportFileType(StrEnum):
    CSV = "CSV"
    XLSX = "XLSX"


class ImportMovementType(StrEnum):
    INCOME = "INGRESO"
    EXPENSE = "GASTO"


class ImportBatch(Base):
    __tablename__ = "lotes_importacion"
    __table_args__ = (
        CheckConstraint(
            "tipo_archivo IN ('CSV', 'XLSX')",
            name="ck_lotes_importacion_tipo_archivo_valido",
        ),
        CheckConstraint(
            "tipo_movimiento IN ('INGRESO', 'GASTO')",
            name="ck_lotes_importacion_tipo_movimiento_valido",
        ),
        CheckConstraint(
            "total_filas >= 0 AND filas_importadas >= 0 AND "
            "filas_pendientes >= 0 AND filas_descartadas >= 0",
            name="ck_lotes_importacion_contadores_no_negativos",
        ),
    )

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column("nombre_archivo", String(255), nullable=False)
    file_type: Mapped[str] = mapped_column("tipo_archivo", String(10), nullable=False)
    movement_type: Mapped[str] = mapped_column("tipo_movimiento", String(10), nullable=False)
    size_bytes: Mapped[int] = mapped_column("tamano_bytes", Integer, nullable=False)
    total_rows: Mapped[int] = mapped_column(
        "total_filas", Integer, nullable=False, default=0, server_default="0"
    )
    imported_rows: Mapped[int] = mapped_column(
        "filas_importadas", Integer, nullable=False, default=0, server_default="0"
    )
    pending_rows: Mapped[int] = mapped_column(
        "filas_pendientes", Integer, nullable=False, default=0, server_default="0"
    )
    discarded_rows: Mapped[int] = mapped_column(
        "filas_descartadas", Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    rows: Mapped[list["ImportRow"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
