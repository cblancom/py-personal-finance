from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

Description = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]
Amount = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
Category = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]


class IncomeWrite(BaseModel):
    fecha: date
    descripcion: Description
    categoria: Category | None = None
    valor: Amount

    @field_validator("categoria", mode="before")
    @classmethod
    def normalize_category(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class IncomeCreate(IncomeWrite):
    pass


class IncomeUpdate(IncomeWrite):
    pass


class IncomeRead(IncomeWrite):
    id: int
