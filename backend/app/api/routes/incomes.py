from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.income import IncomeCreate, IncomeRead, IncomeUpdate
from app.db.models import Income
from app.db.session import get_db

router = APIRouter(prefix="/ingresos", tags=["ingresos"])


def to_income_read(income: Income) -> IncomeRead:
    return IncomeRead(
        id=income.id,
        fecha=income.date,
        descripcion=income.description,
        categoria=income.category,
        valor=income.amount,
    )


def get_income_or_404(db: Session, income_id: int) -> Income:
    income = db.get(Income, income_id)
    if income is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingreso no encontrado",
        )
    return income


@router.post("", response_model=IncomeRead, status_code=status.HTTP_201_CREATED)
def create_income(
    payload: IncomeCreate,
    db: Annotated[Session, Depends(get_db)],
) -> IncomeRead:
    income = Income(
        date=payload.fecha,
        description=payload.descripcion,
        category=payload.categoria,
        amount=payload.valor,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return to_income_read(income)


@router.get("", response_model=list[IncomeRead])
def list_incomes(db: Annotated[Session, Depends(get_db)]) -> list[IncomeRead]:
    incomes = db.scalars(select(Income).order_by(Income.date.desc(), Income.id.desc())).all()
    return [to_income_read(income) for income in incomes]


@router.get("/{income_id}", response_model=IncomeRead)
def get_income(
    income_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> IncomeRead:
    return to_income_read(get_income_or_404(db, income_id))


@router.put("/{income_id}", response_model=IncomeRead)
def update_income(
    income_id: int,
    payload: IncomeUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> IncomeRead:
    income = get_income_or_404(db, income_id)
    income.date = payload.fecha
    income.description = payload.descripcion
    income.category = payload.categoria
    income.amount = payload.valor
    db.commit()
    db.refresh(income)
    return to_income_read(income)


@router.delete("/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_income(
    income_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    income = get_income_or_404(db, income_id)
    db.delete(income)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
