from datetime import date as DateType
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Income(Base):
    __tablename__ = "ingresos"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_ingresos_valor_positivo"),
        CheckConstraint(
            "length(trim(descripcion)) > 0",
            name="ck_ingresos_descripcion_no_vacia",
        ),
        Index("ix_ingresos_fecha", "fecha"),
    )

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    date: Mapped[DateType] = mapped_column("fecha", Date, nullable=False)
    description: Mapped[str] = mapped_column("descripcion", String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column("valor", Numeric(12, 2), nullable=False)
