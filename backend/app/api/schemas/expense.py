from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.db.models.expense import ExpenseType

Description = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class ExpenseWrite(BaseModel):
    fecha: date
    descripcion: Description
    tipo: ExpenseType
    valor: Amount


class ExpenseCreate(ExpenseWrite):
    pass


class ExpenseUpdate(ExpenseWrite):
    pass


class ExpenseRead(ExpenseWrite):
    id: int
