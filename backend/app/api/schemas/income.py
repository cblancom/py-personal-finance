from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Description = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class IncomeWrite(BaseModel):
    fecha: date
    descripcion: Description
    valor: Amount


class IncomeCreate(IncomeWrite):
    pass


class IncomeUpdate(IncomeWrite):
    pass


class IncomeRead(IncomeWrite):
    id: int
