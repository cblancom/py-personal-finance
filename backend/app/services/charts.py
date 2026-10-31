from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Expense, ExpenseType
from app.services.monthly_balance import ZERO, normalize_money


@dataclass(frozen=True)
class MonthlyExpensePoint:
    month: int
    expenses_by_type: dict[ExpenseType, Decimal]


@dataclass(frozen=True)
class MonthlyExpenseSeries:
    year: int
    months: tuple[MonthlyExpensePoint, ...]


def build_monthly_expense_series(
    year: int,
    rows: Iterable[tuple[int | Decimal, ExpenseType | str, Decimal | None]],
) -> MonthlyExpenseSeries:
    months = {month: {expense_type: ZERO for expense_type in ExpenseType} for month in range(1, 13)}

    for month, expense_type, total in rows:
        month_number = int(month)
        if month_number not in months:
            continue
        months[month_number][ExpenseType(expense_type)] = normalize_money(total)

    return MonthlyExpenseSeries(
        year=year,
        months=tuple(
            MonthlyExpensePoint(
                month=month,
                expenses_by_type=months[month],
            )
            for month in range(1, 13)
        ),
    )


def get_monthly_expense_series(db: Session, year: int) -> MonthlyExpenseSeries:
    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)
    month_expression = func.extract("month", Expense.date)
    rows = db.execute(
        select(
            month_expression,
            Expense.expense_type,
            func.sum(Expense.amount),
        )
        .where(Expense.date >= start, Expense.date < end)
        .group_by(month_expression, Expense.expense_type)
    ).all()
    return build_monthly_expense_series(year, rows)
