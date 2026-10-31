from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonthlyAllocation(Base):
    __tablename__ = "asignaciones_mensuales"
    __table_args__ = (
        CheckConstraint(
            "anio BETWEEN 1900 AND 2100",
            name="ck_asignaciones_mensuales_anio_valido",
        ),
        CheckConstraint(
            "mes BETWEEN 1 AND 12",
            name="ck_asignaciones_mensuales_mes_valido",
        ),
        CheckConstraint(
            "porcentaje_necesario BETWEEN 0 AND 100",
            name="ck_asignaciones_mensuales_porcentaje_necesario_valido",
        ),
        CheckConstraint(
            "porcentaje_no_necesario BETWEEN 0 AND 100",
            name="ck_asignaciones_mensuales_porcentaje_no_necesario_valido",
        ),
        CheckConstraint(
            "porcentaje_inversion BETWEEN 0 AND 100",
            name="ck_asignaciones_mensuales_porcentaje_inversion_valido",
        ),
        CheckConstraint(
            "porcentaje_necesario + porcentaje_no_necesario + porcentaje_inversion <= 100",
            name="ck_asignaciones_mensuales_suma_valida",
        ),
        UniqueConstraint(
            "anio",
            "mes",
            name="uq_asignaciones_mensuales_anio_mes",
        ),
    )

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column("anio", Integer, nullable=False)
    month: Mapped[int] = mapped_column("mes", Integer, nullable=False)
    necessary_percentage: Mapped[Decimal] = mapped_column(
        "porcentaje_necesario",
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
    non_necessary_percentage: Mapped[Decimal] = mapped_column(
        "porcentaje_no_necesario",
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )
    investment_percentage: Mapped[Decimal] = mapped_column(
        "porcentaje_inversion",
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
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
