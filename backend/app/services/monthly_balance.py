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
    carryover: Decimal
    available: Decimal
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


@dataclass(frozen=True)
class MonthChain:
    month_start: date
    incomes: Decimal
    percentages: dict[ExpenseType, Decimal]
    assigned: dict[ExpenseType, Decimal]
    carryover: dict[ExpenseType, Decimal]
    available: dict[ExpenseType, Decimal]
    spent: dict[ExpenseType, Decimal]
    remaining: dict[ExpenseType, Decimal]
    unassigned: Decimal


def _empty_totals() -> dict[ExpenseType, Decimal]:
    return {expense_type: ZERO for expense_type in ExpenseType}


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
    carryover: Mapping[ExpenseType, Decimal] | None = None,
) -> dict[ExpenseType, RubroBalance]:
    assigned = calculate_assigned(incomes, percentages)
    carry = carryover or {}
    return {
        expense_type: RubroBalance(
            percentage=normalize_percentage(percentages[expense_type]),
            assigned=assigned[expense_type],
            carryover=normalize_money(carry.get(expense_type, ZERO)),
            available=normalize_money(assigned[expense_type] + carry.get(expense_type, ZERO)),
            spent=normalize_money(spent.get(expense_type, ZERO)),
            remaining=normalize_money(
                assigned[expense_type]
                + carry.get(expense_type, ZERO)
                - spent.get(expense_type, ZERO)
            ),
        )
        for expense_type in ExpenseType
    }


def _month_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def _year_range(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year + 1, 1, 1)


def _iter_months(start: date, end: date):
    current = start
    while current < end:
        yield current
        current = (
            date(current.year + 1, 1, 1)
            if current.month == 12
            else date(current.year, current.month + 1, 1)
        )


def _first_data_month(db: Session) -> date | None:
    dates: list[date] = []

    first_income = db.scalar(select(func.min(Income.date)))
    if first_income is not None:
        dates.append(date(first_income.year, first_income.month, 1))

    first_expense = db.scalar(select(func.min(Expense.date)))
    if first_expense is not None:
        dates.append(date(first_expense.year, first_expense.month, 1))

    first_allocation = db.execute(
        select(MonthlyAllocation.year, MonthlyAllocation.month)
        .order_by(MonthlyAllocation.year, MonthlyAllocation.month)
        .limit(1)
    ).first()
    if first_allocation is not None:
        dates.append(date(first_allocation[0], first_allocation[1], 1))

    return min(dates) if dates else None


def _monthly_income_totals(
    db: Session,
    start: date,
    end: date,
) -> dict[date, Decimal]:
    year_expression = func.extract("year", Income.date)
    month_expression = func.extract("month", Income.date)
    rows = db.execute(
        select(year_expression, month_expression, func.sum(Income.amount))
        .where(Income.date >= start, Income.date < end)
        .group_by(year_expression, month_expression)
    ).all()
    return {date(int(year), int(month), 1): normalize_money(total) for year, month, total in rows}


def _monthly_expense_totals(
    db: Session,
    start: date,
    end: date,
) -> dict[date, dict[ExpenseType, Decimal]]:
    year_expression = func.extract("year", Expense.date)
    month_expression = func.extract("month", Expense.date)
    rows = db.execute(
        select(
            year_expression,
            month_expression,
            Expense.expense_type,
            func.sum(Expense.amount),
        )
        .where(Expense.date >= start, Expense.date < end)
        .group_by(year_expression, month_expression, Expense.expense_type)
    ).all()

    totals: dict[date, dict[ExpenseType, Decimal]] = {}
    for year, month, expense_type, total in rows:
        month_start = date(int(year), int(month), 1)
        month_totals = totals.setdefault(month_start, _empty_totals())
        month_totals[ExpenseType(expense_type)] = normalize_money(total)
    return totals


def _allocations_by_month(
    db: Session,
    start: date,
    end: date,
) -> dict[tuple[int, int], MonthlyAllocation]:
    allocations = db.scalars(
        select(MonthlyAllocation).where(
            MonthlyAllocation.year >= start.year,
            MonthlyAllocation.year <= end.year,
        )
    ).all()
    return {(allocation.year, allocation.month): allocation for allocation in allocations}


def _allocation_percentages(allocation: MonthlyAllocation | None) -> dict[ExpenseType, Decimal]:
    if allocation is None:
        return _empty_totals()
    return {
        ExpenseType.NECESSARY: normalize_percentage(allocation.necessary_percentage),
        ExpenseType.NON_NECESSARY: normalize_percentage(allocation.non_necessary_percentage),
        ExpenseType.INVESTMENT: normalize_percentage(allocation.investment_percentage),
    }


def _build_chain(db: Session, start: date, end: date) -> list[MonthChain]:
    incomes = _monthly_income_totals(db, start, end)
    expenses = _monthly_expense_totals(db, start, end)
    allocations = _allocations_by_month(db, start, end)
    previous_remaining = _empty_totals()
    chain: list[MonthChain] = []

    for month_start in _iter_months(start, end):
        income = incomes.get(month_start, ZERO)
        spent = expenses.get(month_start, _empty_totals())
        percentages = _allocation_percentages(
            allocations.get((month_start.year, month_start.month))
        )
        assigned = calculate_assigned(income, percentages)
        carryover = {
            ExpenseType.NECESSARY: ZERO,
            ExpenseType.NON_NECESSARY: normalize_money(
                previous_remaining[ExpenseType.NECESSARY]
                + previous_remaining[ExpenseType.NON_NECESSARY]
            ),
            ExpenseType.INVESTMENT: previous_remaining[ExpenseType.INVESTMENT],
        }
        available = {
            expense_type: normalize_money(assigned[expense_type] + carryover[expense_type])
            for expense_type in ExpenseType
        }
        remaining = {
            expense_type: normalize_money(available[expense_type] - spent[expense_type])
            for expense_type in ExpenseType
        }
        chain.append(
            MonthChain(
                month_start=month_start,
                incomes=income,
                percentages=percentages,
                assigned=assigned,
                carryover=carryover,
                available=available,
                spent=spent,
                remaining=remaining,
                unassigned=calculate_unassigned(income, assigned),
            )
        )
        previous_remaining = remaining

    return chain


def _to_rubros(chain: MonthChain) -> dict[ExpenseType, RubroBalance]:
    return {
        expense_type: RubroBalance(
            percentage=chain.percentages[expense_type],
            assigned=chain.assigned[expense_type],
            carryover=chain.carryover[expense_type],
            available=chain.available[expense_type],
            spent=chain.spent[expense_type],
            remaining=chain.remaining[expense_type],
        )
        for expense_type in ExpenseType
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


def upsert_monthly_allocation(
    db: Session,
    year: int,
    month: int,
    percentages: Mapping[ExpenseType, Decimal],
) -> MonthlyAllocation:
    allocation = db.scalar(
        select(MonthlyAllocation).where(
            MonthlyAllocation.year == year,
            MonthlyAllocation.month == month,
        )
    )
    if allocation is None:
        allocation = MonthlyAllocation(year=year, month=month)
        db.add(allocation)

    allocation.necessary_percentage = normalize_percentage(percentages[ExpenseType.NECESSARY])
    allocation.non_necessary_percentage = normalize_percentage(
        percentages[ExpenseType.NON_NECESSARY]
    )
    allocation.investment_percentage = normalize_percentage(percentages[ExpenseType.INVESTMENT])

    try:
        db.commit()
        db.refresh(allocation)
        return allocation
    except Exception:
        db.rollback()
        raise


def get_monthly_balance(db: Session, year: int, month: int) -> MonthlyBalance:
    target_start, target_end = _month_range(year, month)
    first_data = _first_data_month(db)
    chain_start = (
        first_data if first_data is not None and first_data <= target_start else target_start
    )
    chain = _build_chain(db, chain_start, target_end)
    current = chain[-1]

    return MonthlyBalance(
        year=year,
        month=month,
        incomes=current.incomes,
        unassigned=current.unassigned,
        rubros=_to_rubros(current),
        movements=_monthly_movements(db, target_start, target_end),
    )


def get_annual_balance(db: Session, year: int) -> MonthlyBalance:
    year_start, year_end = _year_range(year)
    first_data = _first_data_month(db)
    chain_start = first_data if first_data is not None and first_data <= year_start else year_start
    chain = _build_chain(db, chain_start, year_end)
    year_months = [month for month in chain if year_start <= month.month_start < year_end]

    previous_remaining = _empty_totals()
    for month in chain:
        if month.month_start >= year_start:
            break
        previous_remaining = month.remaining

    base_assigned = {
        expense_type: normalize_money(
            sum((month.assigned[expense_type] for month in year_months), ZERO)
        )
        for expense_type in ExpenseType
    }
    spent = {
        expense_type: normalize_money(
            sum((month.spent[expense_type] for month in year_months), ZERO)
        )
        for expense_type in ExpenseType
    }
    incomes = normalize_money(sum((month.incomes for month in year_months), ZERO))
    unassigned = normalize_money(sum((month.unassigned for month in year_months), ZERO))
    necessary_transfers = normalize_money(
        sum((month.remaining[ExpenseType.NECESSARY] for month in year_months), ZERO)
    )
    carryover = {
        ExpenseType.NECESSARY: ZERO,
        ExpenseType.NON_NECESSARY: normalize_money(
            previous_remaining[ExpenseType.NECESSARY]
            + previous_remaining[ExpenseType.NON_NECESSARY]
            + necessary_transfers
        ),
        ExpenseType.INVESTMENT: previous_remaining[ExpenseType.INVESTMENT],
    }
    available = {
        expense_type: normalize_money(base_assigned[expense_type] + carryover[expense_type])
        for expense_type in ExpenseType
    }
    remaining = {
        ExpenseType.NECESSARY: normalize_money(
            base_assigned[ExpenseType.NECESSARY] - spent[ExpenseType.NECESSARY]
        ),
        ExpenseType.NON_NECESSARY: normalize_money(
            available[ExpenseType.NON_NECESSARY] - spent[ExpenseType.NON_NECESSARY]
        ),
        ExpenseType.INVESTMENT: normalize_money(
            available[ExpenseType.INVESTMENT] - spent[ExpenseType.INVESTMENT]
        ),
    }

    rubros = {
        expense_type: RubroBalance(
            percentage=calculate_weighted_percentage(
                base_assigned[expense_type],
                incomes,
            ),
            assigned=base_assigned[expense_type],
            carryover=carryover[expense_type],
            available=available[expense_type],
            spent=spent[expense_type],
            remaining=remaining[expense_type],
        )
        for expense_type in ExpenseType
    }

    return MonthlyBalance(
        year=year,
        month=None,
        incomes=incomes,
        unassigned=unassigned,
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
