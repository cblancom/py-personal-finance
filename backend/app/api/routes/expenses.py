from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.db.models import Expense, ExpenseType
from app.db.session import get_db

router = APIRouter(prefix="/gastos", tags=["gastos"])


def to_expense_read(expense: Expense) -> ExpenseRead:
    return ExpenseRead(
        id=expense.id,
        fecha=expense.date,
        descripcion=expense.description,
        tipo=ExpenseType(expense.expense_type),
        valor=expense.amount,
    )


def get_expense_or_404(db: Session, expense_id: int) -> Expense:
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado",
        )
    return expense


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    expense = Expense(
        date=payload.fecha,
        description=payload.descripcion,
        expense_type=payload.tipo.value,
        amount=payload.valor,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return to_expense_read(expense)


@router.get("", response_model=list[ExpenseRead])
def list_expenses(db: Annotated[Session, Depends(get_db)]) -> list[ExpenseRead]:
    expenses = db.scalars(select(Expense).order_by(Expense.date.desc(), Expense.id.desc())).all()
    return [to_expense_read(expense) for expense in expenses]


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(
    expense_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    return to_expense_read(get_expense_or_404(db, expense_id))


@router.put("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseRead:
    expense = get_expense_or_404(db, expense_id)
    expense.date = payload.fecha
    expense.description = payload.descripcion
    expense.expense_type = payload.tipo.value
    expense.amount = payload.valor
    db.commit()
    db.refresh(expense)
    return to_expense_read(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    expense = get_expense_or_404(db, expense_id)
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
