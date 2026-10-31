from decimal import Decimal

from pydantic import BaseModel

from app.db.models.expense import ExpenseType


class ExpenseChartMonthRead(BaseModel):
    mes: int
    gastos_por_tipo: dict[ExpenseType, Decimal]


class ExpenseChartRead(BaseModel):
    anio: int
    meses: list[ExpenseChartMonthRead]
