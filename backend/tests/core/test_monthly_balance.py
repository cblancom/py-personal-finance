from decimal import Decimal

from app.db.models import ExpenseType
from app.services.monthly_balance import (
    calculate_assigned,
    calculate_rubros,
    calculate_unassigned,
    calculate_weighted_percentage,
    normalize_money,
)


def percentages(
    necessary: str = "50.00",
    non_necessary: str = "30.00",
    investment: str = "20.00",
) -> dict[ExpenseType, Decimal]:
    return {
        ExpenseType.NECESSARY: Decimal(necessary),
        ExpenseType.NON_NECESSARY: Decimal(non_necessary),
        ExpenseType.INVESTMENT: Decimal(investment),
    }


def test_normalize_money_handles_none_and_rounds_to_cents():
    assert normalize_money(None) == Decimal("0.00")
    assert normalize_money(Decimal("10.006")) == Decimal("10.01")


def test_calculate_assigned_uses_monthly_income_and_percentages():
    assigned = calculate_assigned(Decimal("5000.00"), percentages())

    assert assigned == {
        ExpenseType.NECESSARY: Decimal("2500.00"),
        ExpenseType.NON_NECESSARY: Decimal("1500.00"),
        ExpenseType.INVESTMENT: Decimal("1000.00"),
    }


def test_calculate_unassigned_returns_remainder_and_rounds_to_zero():
    assigned = {
        ExpenseType.NECESSARY: Decimal("2500.00"),
        ExpenseType.NON_NECESSARY: Decimal("1500.00"),
        ExpenseType.INVESTMENT: Decimal("0.00"),
    }

    assert calculate_unassigned(Decimal("5000.00"), assigned) == Decimal("1000.00")
    assert calculate_unassigned(
        Decimal("5000.00"), {**assigned, ExpenseType.INVESTMENT: Decimal("1001.00")}
    ) == Decimal("0.00")


def test_calculate_rubros_keeps_negative_remaining():
    rubros = calculate_rubros(
        Decimal("5000.00"),
        {
            ExpenseType.NECESSARY: Decimal("3000.00"),
            ExpenseType.NON_NECESSARY: Decimal("100.00"),
            ExpenseType.INVESTMENT: Decimal("2000.00"),
        },
        percentages(),
    )

    assert rubros[ExpenseType.NECESSARY].assigned == Decimal("2500.00")
    assert rubros[ExpenseType.NECESSARY].remaining == Decimal("-500.00")
    assert rubros[ExpenseType.NON_NECESSARY].remaining == Decimal("1400.00")
    assert rubros[ExpenseType.INVESTMENT].remaining == Decimal("-1000.00")


def test_calculate_weighted_percentage_uses_income_weight():
    assert calculate_weighted_percentage(Decimal("4000.00"), Decimal("5000.00")) == Decimal("80.00")
    assert calculate_weighted_percentage(Decimal("0.00"), Decimal("0.00")) == Decimal("0.00")


def test_calculate_rubros_adds_carryover_to_available_and_remaining():
    rubros = calculate_rubros(
        Decimal("1000.00"),
        {ExpenseType.NON_NECESSARY: Decimal("200.00")},
        percentages(necessary="0.00", non_necessary="100.00", investment="0.00"),
        carryover={ExpenseType.NON_NECESSARY: Decimal("500.00")},
    )

    assert rubros[ExpenseType.NON_NECESSARY].assigned == Decimal("1000.00")
    assert rubros[ExpenseType.NON_NECESSARY].carryover == Decimal("500.00")
    assert rubros[ExpenseType.NON_NECESSARY].available == Decimal("1500.00")
    assert rubros[ExpenseType.NON_NECESSARY].remaining == Decimal("1300.00")
