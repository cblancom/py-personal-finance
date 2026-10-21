from decimal import Decimal

from pydantic import BaseModel

from app.db.models.expense import ExpenseType


class SummaryResponse(BaseModel):
    total_ingresos: Decimal
    total_gastos: Decimal
    balance: Decimal
    gastos_por_tipo: dict[ExpenseType, Decimal]
