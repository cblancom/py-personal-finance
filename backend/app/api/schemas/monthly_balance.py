from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.db.models.expense import ExpenseType

Percentage = Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]


class BalanceRubroRead(BaseModel):
    porcentaje: Decimal
    asignado: Decimal
    gastado: Decimal
    restante: Decimal


class BalanceMovementRead(BaseModel):
    id: int
    fecha: date
    descripcion: str
    valor: Decimal


class BalanceMovementsRead(BaseModel):
    INGRESOS: list[BalanceMovementRead]
    NECESARIO: list[BalanceMovementRead]
    NO_NECESARIO: list[BalanceMovementRead]
    INVERSION: list[BalanceMovementRead]


class BalanceBase(BaseModel):
    anio: int
    ingresos: Decimal
    sin_asignar: Decimal
    rubros: dict[ExpenseType, BalanceRubroRead]


class MonthlyBalanceRead(BalanceBase):
    mes: int
    movimientos: BalanceMovementsRead


class AnnualBalanceRead(BalanceBase):
    mes: None = None


class BalancePeriodsRead(BaseModel):
    anio_actual: int
    anios: list[int]


class MonthlyAllocationUpdate(BaseModel):
    porcentajes: dict[ExpenseType, Percentage]

    @field_validator("porcentajes")
    @classmethod
    def validate_percentages(
        cls,
        value: dict[ExpenseType, Decimal],
    ) -> dict[ExpenseType, Decimal]:
        if set(value) != set(ExpenseType):
            raise ValueError("Debes indicar los tres porcentajes.")

        total = sum(value.values(), Decimal("0.00"))
        if total > Decimal("100.00"):
            raise ValueError("La suma de los porcentajes no puede superar 100.")

        return {
            expense_type: percentage.quantize(Decimal("0.01"))
            for expense_type, percentage in value.items()
        }
