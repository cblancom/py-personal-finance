from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.api.schemas.monthly_balance import (
    AnnualBalanceRead,
    BalancePeriodsRead,
    MonthlyAllocationUpdate,
    MonthlyBalanceRead,
)
from app.db.models import ExpenseType


def rubros() -> dict[ExpenseType, dict[str, Decimal]]:
    return {
        ExpenseType.NECESSARY: {
            "porcentaje": Decimal("50.00"),
            "asignado": Decimal("2500.00"),
            "gastado": Decimal("1000.00"),
            "restante": Decimal("1500.00"),
        },
        ExpenseType.NON_NECESSARY: {
            "porcentaje": Decimal("30.00"),
            "asignado": Decimal("1500.00"),
            "gastado": Decimal("300.00"),
            "restante": Decimal("1200.00"),
        },
        ExpenseType.INVESTMENT: {
            "porcentaje": Decimal("20.00"),
            "asignado": Decimal("1000.00"),
            "gastado": Decimal("200.00"),
            "restante": Decimal("800.00"),
        },
    }


def movements() -> dict[str, list[dict[str, object]]]:
    return {
        "INGRESOS": [
            {
                "id": 1,
                "fecha": date(2026, 10, 1),
                "descripcion": "Salario",
                "valor": Decimal("5000.00"),
            }
        ],
        "NECESARIO": [
            {
                "id": 2,
                "fecha": date(2026, 10, 2),
                "descripcion": "Mercado",
                "valor": Decimal("1000.00"),
            }
        ],
        "NO_NECESARIO": [
            {
                "id": 3,
                "fecha": date(2026, 10, 3),
                "descripcion": "Cine",
                "valor": Decimal("300.00"),
            }
        ],
        "INVERSION": [
            {
                "id": 4,
                "fecha": date(2026, 10, 4),
                "descripcion": "Fondo indexado",
                "valor": Decimal("200.00"),
            }
        ],
    }


def test_monthly_balance_serializes_contract():
    balance = MonthlyBalanceRead(
        anio=2026,
        mes=10,
        ingresos=Decimal("5000.00"),
        sin_asignar=Decimal("0.00"),
        rubros=rubros(),
        movimientos=movements(),
    )

    assert balance.model_dump(mode="json") == {
        "anio": 2026,
        "mes": 10,
        "ingresos": "5000.00",
        "sin_asignar": "0.00",
        "rubros": {
            "NECESARIO": {
                "porcentaje": "50.00",
                "asignado": "2500.00",
                "gastado": "1000.00",
                "restante": "1500.00",
            },
            "NO_NECESARIO": {
                "porcentaje": "30.00",
                "asignado": "1500.00",
                "gastado": "300.00",
                "restante": "1200.00",
            },
            "INVERSION": {
                "porcentaje": "20.00",
                "asignado": "1000.00",
                "gastado": "200.00",
                "restante": "800.00",
            },
        },
        "movimientos": {
            "INGRESOS": [
                {
                    "id": 1,
                    "fecha": "2026-10-01",
                    "descripcion": "Salario",
                    "valor": "5000.00",
                }
            ],
            "NECESARIO": [
                {
                    "id": 2,
                    "fecha": "2026-10-02",
                    "descripcion": "Mercado",
                    "valor": "1000.00",
                }
            ],
            "NO_NECESARIO": [
                {
                    "id": 3,
                    "fecha": "2026-10-03",
                    "descripcion": "Cine",
                    "valor": "300.00",
                }
            ],
            "INVERSION": [
                {
                    "id": 4,
                    "fecha": "2026-10-04",
                    "descripcion": "Fondo indexado",
                    "valor": "200.00",
                }
            ],
        },
    }


def test_annual_balance_has_no_movements():
    balance = AnnualBalanceRead(
        anio=2026,
        ingresos=Decimal("5000.00"),
        sin_asignar=Decimal("0.00"),
        rubros=rubros(),
    )

    data = balance.model_dump(mode="json")

    assert data["mes"] is None
    assert "movimientos" not in data


def test_periods_serialize_years():
    periods = BalancePeriodsRead(anio_actual=2026, anios=[2026, 2025])

    assert periods.model_dump(mode="json") == {
        "anio_actual": 2026,
        "anios": [2026, 2025],
    }


def test_allocation_update_accepts_valid_percentages():
    payload = MonthlyAllocationUpdate.model_validate(
        {
            "porcentajes": {
                "NECESARIO": "50",
                "NO_NECESARIO": "30.00",
                "INVERSION": "20.00",
            }
        }
    )

    assert payload.porcentajes == {
        ExpenseType.NECESSARY: Decimal("50.00"),
        ExpenseType.NON_NECESSARY: Decimal("30.00"),
        ExpenseType.INVESTMENT: Decimal("20.00"),
    }


@pytest.mark.parametrize(
    "porcentajes",
    [
        {
            "NECESARIO": "50.00",
            "NO_NECESARIO": "30.00",
        },
        {
            "NECESARIO": "50.00",
            "NO_NECESARIO": "30.00",
            "INVERSION": "20.01",
        },
        {
            "NECESARIO": "-1.00",
            "NO_NECESARIO": "30.00",
            "INVERSION": "20.00",
        },
        {
            "NECESARIO": "101.00",
            "NO_NECESARIO": "0.00",
            "INVERSION": "0.00",
        },
        {
            "NECESARIO": "50.001",
            "NO_NECESARIO": "30.00",
            "INVERSION": "20.00",
        },
    ],
)
def test_allocation_update_rejects_invalid_percentages(porcentajes):
    with pytest.raises(ValidationError):
        MonthlyAllocationUpdate.model_validate({"porcentajes": porcentajes})
