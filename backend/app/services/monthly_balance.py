from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Expense, ExpenseType, Income, MonthlyAllocation

ZERO = Decimal("0.00")
HUNDRED = Decimal("100")


@dataclass(frozen=True)
class RubroBalance:
    percentage: Decimal
    assigned: Decimal
    spent: Decimal
    remaining: Decimal


@dataclass(frozen=True)
class Movement:
    id: int
    date: date
    description: str
    amount: Decimal


@dataclass(frozen=True)
class MonthlyMovements:
    incomes: tuple[Movement, ...]
    necessary: tuple[Movement, ...]
    non_necessary: tuple[Movement, ...]
    investment: tuple[Movement, ...]


@dataclass(frozen=True)
class MonthlyBalance:
    year: int
    month: int | None
    incomes: Decimal
    unassigned: Decimal
    rubros: dict[ExpenseType, RubroBalance]
    movements: MonthlyMovements | None


@dataclass(frozen=True)
class AvailablePeriods:
    current_year: int
    years: tuple[int, ...]


def normalize_money(value: Decimal | None) -> Decimal:
    if value is None:
        return ZERO
    return value.quantize(Decimal("0.01"))


def normalize_percentage(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def calculate_assigned(
    incomes: Decimal,
    percentages: Mapping[ExpenseType, Decimal],
) -> dict[ExpenseType, Decimal]:
    return {
        expense_type: normalize_money(incomes * percentage / HUNDRED)
        for expense_type, percentage in percentages.items()
    }


def calculate_unassigned(
    incomes: Decimal,
    assigned: Mapping[ExpenseType, Decimal],
) -> Decimal:
    remaining = normalize_money(incomes - sum(assigned.values(), ZERO))
    return max(remaining, ZERO)


def calculate_weighted_percentage(assigned: Decimal, incomes: Decimal) -> Decimal:
    if incomes <= ZERO:
        return ZERO
    return normalize_money(assigned / incomes * HUNDRED)


def calculate_rubros(
    incomes: Decimal,
    spent: Mapping[ExpenseType, Decimal],
    percentages: Mapping[ExpenseType, Decimal],
) -> dict[ExpenseType, RubroBalance]:
    assigned = calculate_assigned(incomes, percentages)
    return {
        expense_type: RubroBalance(
            percentage=normalize_percentage(percentages[expense_type]),
            assigned=assigned[expense_type],
            spent=normalize_money(spent.get(expense_type, ZERO)),
            remaining=normalize_money(assigned[expense_type] - spent.get(expense_type, ZERO)),
        )
        for expense_type in ExpenseType
    }


def _month_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def _year_range(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year + 1, 1, 1)


def _sum_incomes(db: Session, start: date, end: date) -> Decimal:
    total = db.scalar(
        select(func.sum(Income.amount)).where(Income.date >= start, Income.date < end)
    )
    return normalize_money(total)


def _expense_totals(
    db: Session,
    start: date,
    end: date,
) -> dict[ExpenseType, Decimal]:
    rows = db.execute(
        select(Expense.expense_type, func.sum(Expense.amount))
        .where(Expense.date >= start, Expense.date < end)
        .group_by(Expense.expense_type)
    ).all()
    totals = {expense_type: ZERO for expense_type in ExpenseType}
    for expense_type, total in rows:
        totals[ExpenseType(expense_type)] = normalize_money(total)
    return totals


def _allocation_percentages(allocation: MonthlyAllocation | None) -> dict[ExpenseType, Decimal]:
    if allocation is None:
        return {expense_type: ZERO for expense_type in ExpenseType}
    return {
        ExpenseType.NECESSARY: normalize_percentage(allocation.necessary_percentage),
        ExpenseType.NON_NECESSARY: normalize_percentage(allocation.non_necessary_percentage),
        ExpenseType.INVESTMENT: normalize_percentage(allocation.investment_percentage),
    }


def _movement(
    *,
    id_: int,
    movement_date: date,
    description: str,
    amount: Decimal,
) -> Movement:
    return Movement(
        id=id_,
        date=movement_date,
        description=description,
        amount=normalize_money(amount),
    )


def _monthly_movements(
    db: Session,
    start: date,
    end: date,
) -> MonthlyMovements:
    incomes = db.scalars(
        select(Income)
        .where(Income.date >= start, Income.date < end)
        .order_by(Income.date, Income.id)
    ).all()
    expenses = db.scalars(
        select(Expense)
        .where(Expense.date >= start, Expense.date < end)
        .order_by(Expense.date, Expense.id)
    ).all()

    grouped: dict[ExpenseType, list[Movement]] = {expense_type: [] for expense_type in ExpenseType}
    for expense in expenses:
        grouped[ExpenseType(expense.expense_type)].append(
            _movement(
                id_=expense.id,
                movement_date=expense.date,
                description=expense.description,
                amount=expense.amount,
            )
        )

    return MonthlyMovements(
        incomes=tuple(
            _movement(
                id_=income.id,
                movement_date=income.date,
                description=income.description,
                amount=income.amount,
            )
            for income in incomes
        ),
        necessary=tuple(grouped[ExpenseType.NECESSARY]),
        non_necessary=tuple(grouped[ExpenseType.NON_NECESSARY]),
        investment=tuple(grouped[ExpenseType.INVESTMENT]),
    )


def get_monthly_balance(db: Session, year: int, month: int) -> MonthlyBalance:
    start, end = _month_range(year, month)
    incomes = _sum_incomes(db, start, end)
    spent = _expense_totals(db, start, end)
    allocation = db.scalar(
        select(MonthlyAllocation).where(
            MonthlyAllocation.year == year,
            MonthlyAllocation.month == month,
        )
    )
    percentages = _allocation_percentages(allocation)
    rubros = calculate_rubros(incomes, spent, percentages)
    assigned = {expense_type: rubro.assigned for expense_type, rubro in rubros.items()}

    return MonthlyBalance(
        year=year,
        month=month,
        incomes=incomes,
        unassigned=calculate_unassigned(incomes, assigned),
        rubros=rubros,
        movements=_monthly_movements(db, start, end),
    )


def _monthly_income_totals(
    db: Session,
    start: date,
    end: date,
) -> dict[int, Decimal]:
    month_expression = func.extract("month", Income.date)
    rows = db.execute(
        select(month_expression, func.sum(Income.amount))
        .where(Income.date >= start, Income.date < end)
        .group_by(month_expression)
    ).all()
    return {int(month): normalize_money(total) for month, total in rows if month is not None}


def get_annual_balance(db: Session, year: int) -> MonthlyBalance:
    start, end = _year_range(year)
    monthly_incomes = _monthly_income_totals(db, start, end)
    allocations = {
        allocation.month: allocation
        for allocation in db.scalars(
            select(MonthlyAllocation).where(MonthlyAllocation.year == year)
        ).all()
    }
    assigned_by_type = {expense_type: ZERO for expense_type in ExpenseType}

    for month in range(1, 13):
        percentages = _allocation_percentages(allocations.get(month))
        monthly_assigned = calculate_assigned(
            monthly_incomes.get(month, ZERO),
            percentages,
        )
        for expense_type, amount in monthly_assigned.items():
            assigned_by_type[expense_type] += amount

    incomes = normalize_money(sum(monthly_incomes.values(), ZERO))
    spent = _expense_totals(db, start, end)
    rubros = {
        expense_type: RubroBalance(
            percentage=calculate_weighted_percentage(
                assigned_by_type[expense_type],
                incomes,
            ),
            assigned=normalize_money(assigned_by_type[expense_type]),
            spent=normalize_money(spent[expense_type]),
            remaining=normalize_money(assigned_by_type[expense_type] - spent[expense_type]),
        )
        for expense_type in ExpenseType
    }

    return MonthlyBalance(
        year=year,
        month=None,
        incomes=incomes,
        unassigned=calculate_unassigned(incomes, assigned_by_type),
        rubros=rubros,
        movements=None,
    )


def _years_from_date_column(db: Session, column: object) -> set[int]:
    years = db.scalars(select(func.extract("year", column)).distinct()).all()
    return {int(year) for year in years if year is not None}


def get_available_periods(
    db: Session,
    today: date | None = None,
) -> AvailablePeriods:
    current_date = today or date.today()
    years = _years_from_date_column(db, Income.date)
    years.update(_years_from_date_column(db, Expense.date))
    years.update(db.scalars(select(MonthlyAllocation.year).distinct()).all())
    years.add(current_date.year)
    return AvailablePeriods(
        current_year=current_date.year,
        years=tuple(sorted(years, reverse=True)),
    )
