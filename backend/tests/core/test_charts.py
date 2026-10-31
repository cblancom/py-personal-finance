from decimal import Decimal

from app.db.models import ExpenseType
from app.services.charts import build_monthly_expense_series


def test_build_monthly_expense_series_fills_twelve_months():
    series = build_monthly_expense_series(
        2026,
        [
            (1, ExpenseType.NECESSARY, Decimal("100.00")),
            (1, ExpenseType.NON_NECESSARY, Decimal("50.00")),
            (2, "INVERSION", Decimal("20.00")),
        ],
    )

    assert series.year == 2026
    assert len(series.months) == 12
    assert series.months[0].month == 1
    assert series.months[0].expenses_by_type == {
        ExpenseType.NECESSARY: Decimal("100.00"),
        ExpenseType.NON_NECESSARY: Decimal("50.00"),
        ExpenseType.INVESTMENT: Decimal("0.00"),
    }
    assert series.months[1].expenses_by_type[ExpenseType.INVESTMENT] == Decimal("20.00")
    assert series.months[2].expenses_by_type == {
        ExpenseType.NECESSARY: Decimal("0.00"),
        ExpenseType.NON_NECESSARY: Decimal("0.00"),
        ExpenseType.INVESTMENT: Decimal("0.00"),
    }


def test_build_monthly_expense_series_ignores_months_out_of_range():
    series = build_monthly_expense_series(
        2026,
        [(13, ExpenseType.NECESSARY, Decimal("100.00"))],
    )

    assert all(
        amount == Decimal("0.00")
        for month in series.months
        for amount in month.expenses_by_type.values()
    )
