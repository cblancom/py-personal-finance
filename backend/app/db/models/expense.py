from datetime import date as DateType
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExpenseType(StrEnum):
    NECESSARY = "NECESARIO"
    NON_NECESSARY = "NO_NECESARIO"
    INVESTMENT = "INVERSION"


class Expense(Base):
    __tablename__ = "gastos"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_gastos_valor_positivo"),
        CheckConstraint(
            "length(trim(descripcion)) > 0",
            name="ck_gastos_descripcion_no_vacia",
        ),
        CheckConstraint(
            "tipo IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')",
            name="ck_gastos_tipo_valido",
        ),
        Index("ix_gastos_fecha", "fecha"),
    )

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    date: Mapped[DateType] = mapped_column("fecha", Date, nullable=False)
    description: Mapped[str] = mapped_column("descripcion", String(200), nullable=False)
    expense_type: Mapped[str] = mapped_column("tipo", String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column("valor", Numeric(12, 2), nullable=False)
