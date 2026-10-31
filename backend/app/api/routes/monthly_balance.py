from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.schemas.monthly_balance import (
    AnnualBalanceRead,
    BalanceMovementRead,
    BalanceMovementsRead,
    BalancePeriodsRead,
    BalanceRubroRead,
    MonthlyAllocationUpdate,
    MonthlyBalanceRead,
)
from app.db.models import ExpenseType
from app.db.session import get_db
from app.services.monthly_balance import (
    MonthlyBalance,
    MonthlyMovements,
    Movement,
    RubroBalance,
    get_annual_balance,
    get_available_periods,
    get_monthly_balance,
    upsert_monthly_allocation,
)

router = APIRouter(prefix="/balance-mensual", tags=["balance-mensual"])


def _rubro_read(rubro: RubroBalance) -> BalanceRubroRead:
    return BalanceRubroRead(
        porcentaje=rubro.percentage,
        asignado=rubro.assigned,
        gastado=rubro.spent,
        restante=rubro.remaining,
    )


def _movement_read(movement: Movement) -> BalanceMovementRead:
    return BalanceMovementRead(
        id=movement.id,
        fecha=movement.date,
        descripcion=movement.description,
        valor=movement.amount,
    )


def _movements_read(movements: MonthlyMovements) -> BalanceMovementsRead:
    return BalanceMovementsRead(
        INGRESOS=[_movement_read(movement) for movement in movements.incomes],
        NECESARIO=[_movement_read(movement) for movement in movements.necessary],
        NO_NECESARIO=[_movement_read(movement) for movement in movements.non_necessary],
        INVERSION=[_movement_read(movement) for movement in movements.investment],
    )


def _rubros_read(
    rubros: dict[ExpenseType, RubroBalance],
) -> dict[ExpenseType, BalanceRubroRead]:
    return {expense_type: _rubro_read(rubro) for expense_type, rubro in rubros.items()}


def _monthly_read(balance: MonthlyBalance) -> MonthlyBalanceRead:
    if balance.month is None or balance.movements is None:
        raise ValueError("El balance mensual debe incluir mes y movimientos.")
    return MonthlyBalanceRead(
        anio=balance.year,
        mes=balance.month,
        ingresos=balance.incomes,
        sin_asignar=balance.unassigned,
        rubros=_rubros_read(balance.rubros),
        movimientos=_movements_read(balance.movements),
    )


def _annual_read(balance: MonthlyBalance) -> AnnualBalanceRead:
    return AnnualBalanceRead(
        anio=balance.year,
        ingresos=balance.incomes,
        sin_asignar=balance.unassigned,
        rubros=_rubros_read(balance.rubros),
    )


@router.get("", response_model=MonthlyBalanceRead | AnnualBalanceRead)
def get_balance(
    db: Annotated[Session, Depends(get_db)],
    anio: Annotated[int | None, Query(ge=1900, le=2100)] = None,
    mes: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> MonthlyBalanceRead | AnnualBalanceRead:
    target_year = anio or date.today().year
    if mes is None:
        return _annual_read(get_annual_balance(db, target_year))
    return _monthly_read(get_monthly_balance(db, target_year, mes))


@router.get("/periodos", response_model=BalancePeriodsRead)
def get_periods(db: Annotated[Session, Depends(get_db)]) -> BalancePeriodsRead:
    periods = get_available_periods(db)
    return BalancePeriodsRead(
        anio_actual=periods.current_year,
        anios=list(periods.years),
    )


@router.put(
    "/asignaciones/{anio}/{mes}",
    response_model=MonthlyBalanceRead,
)
def update_allocation(
    anio: Annotated[int, Path(ge=1900, le=2100)],
    mes: Annotated[int, Path(ge=1, le=12)],
    payload: MonthlyAllocationUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> MonthlyBalanceRead:
    upsert_monthly_allocation(db, anio, mes, payload.porcentajes)
    return _monthly_read(get_monthly_balance(db, anio, mes))
