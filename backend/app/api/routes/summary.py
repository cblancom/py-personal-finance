from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas.summary import SummaryResponse
from app.db.models import Expense, ExpenseType, Income
from app.db.session import get_db

router = APIRouter(tags=["resumen"])


def _as_money(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return value.quantize(Decimal("0.01"))


@router.get("/resumen", response_model=SummaryResponse)
def get_summary(db: Annotated[Session, Depends(get_db)]) -> SummaryResponse:
    total_incomes = _as_money(db.scalar(select(func.sum(Income.amount))))

    expense_rows = db.execute(
        select(Expense.expense_type, func.sum(Expense.amount)).group_by(Expense.expense_type)
    ).all()

    breakdown = {expense_type: Decimal("0.00") for expense_type in ExpenseType}
    for expense_type, total in expense_rows:
        breakdown[ExpenseType(expense_type)] = _as_money(total)

    total_expenses = sum(breakdown.values(), Decimal("0.00"))
    balance = _as_money(total_incomes - total_expenses)

    return SummaryResponse(
        total_ingresos=total_incomes,
        total_gastos=total_expenses,
        balance=balance,
        gastos_por_tipo=breakdown,
    )
