from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import MonthlyAllocation

pytestmark = pytest.mark.integration


def iso_date(year: int, month: int, day: int) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}"


def create_income(
    client: TestClient,
    *,
    amount: str,
    movement_date: str,
    description: str = "Ingreso",
) -> None:
    response = client.post(
        "/api/ingresos",
        json={"fecha": movement_date, "descripcion": description, "valor": amount},
    )
    assert response.status_code == 201


def create_expense(
    client: TestClient,
    *,
    amount: str,
    movement_date: str,
    expense_type: str,
    description: str = "Gasto",
) -> None:
    response = client.post(
        "/api/gastos",
        json={
            "fecha": movement_date,
            "descripcion": description,
            "tipo": expense_type,
            "valor": amount,
        },
    )
    assert response.status_code == 201


def update_allocation(
    client: TestClient,
    *,
    year: int,
    month: int,
    necessary: str = "50.00",
    non_necessary: str = "30.00",
    investment: str = "20.00",
):
    return client.put(
        f"/api/balance-mensual/asignaciones/{year}/{month}",
        json={
            "porcentajes": {
                "NECESARIO": necessary,
                "NO_NECESARIO": non_necessary,
                "INVERSION": investment,
            }
        },
    )


def test_default_balance_is_annual_for_current_year(client: TestClient):
    response = client.get("/api/balance-mensual")

    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == date.today().year
    assert body["mes"] is None
    assert "movimientos" not in body


def test_monthly_balance_returns_movements_and_remaining(client: TestClient):
    year = date.today().year
    create_income(
        client,
        amount="5000.00",
        movement_date=iso_date(year, 10, 1),
        description="Salario",
    )
    create_expense(
        client,
        amount="1000.00",
        movement_date=iso_date(year, 10, 2),
        expense_type="NECESARIO",
        description="Mercado",
    )
    create_expense(
        client,
        amount="300.00",
        movement_date=iso_date(year, 10, 3),
        expense_type="NO_NECESARIO",
        description="Cine",
    )
    create_expense(
        client,
        amount="200.00",
        movement_date=iso_date(year, 10, 4),
        expense_type="INVERSION",
        description="Fondo indexado",
    )

    response = update_allocation(client, year=year, month=10)

    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == year
    assert body["mes"] == 10
    assert body["ingresos"] == "5000.00"
    assert body["sin_asignar"] == "0.00"
    assert body["rubros"]["NECESARIO"] == {
        "porcentaje": "50.00",
        "asignado": "2500.00",
        "gastado": "1000.00",
        "restante": "1500.00",
    }
    assert body["rubros"]["NO_NECESARIO"]["restante"] == "1200.00"
    assert body["rubros"]["INVERSION"]["restante"] == "800.00"
    assert body["movimientos"]["INGRESOS"][0]["descripcion"] == "Salario"
    assert body["movimientos"]["NECESARIO"][0]["fecha"] == iso_date(year, 10, 2)
    assert body["movimientos"]["NO_NECESARIO"][0]["descripcion"] == "Cine"
    assert body["movimientos"]["INVERSION"][0]["valor"] == "200.00"


def test_annual_balance_uses_weighted_percentages(client: TestClient):
    year = date.today().year
    create_income(client, amount="1000.00", movement_date=iso_date(year, 1, 10))
    create_income(client, amount="2000.00", movement_date=iso_date(year, 2, 10))
    create_expense(
        client,
        amount="100.00",
        movement_date=iso_date(year, 1, 11),
        expense_type="NECESARIO",
    )
    create_expense(
        client,
        amount="200.00",
        movement_date=iso_date(year, 2, 11),
        expense_type="NECESARIO",
    )

    assert (
        update_allocation(
            client,
            year=year,
            month=1,
            necessary="100.00",
            non_necessary="0.00",
            investment="0.00",
        ).status_code
        == 200
    )
    assert (
        update_allocation(
            client,
            year=year,
            month=2,
            necessary="0.00",
            non_necessary="100.00",
            investment="0.00",
        ).status_code
        == 200
    )

    response = client.get(f"/api/balance-mensual?anio={year}")

    assert response.status_code == 200
    body = response.json()
    assert body["mes"] is None
    assert body["ingresos"] == "3000.00"
    assert body["sin_asignar"] == "0.00"
    assert body["rubros"]["NECESARIO"] == {
        "porcentaje": "33.33",
        "asignado": "1000.00",
        "gastado": "300.00",
        "restante": "700.00",
    }
    assert body["rubros"]["NO_NECESARIO"]["porcentaje"] == "66.67"
    assert body["rubros"]["NO_NECESARIO"]["asignado"] == "2000.00"
    assert "movimientos" not in body


def test_periods_include_data_years_and_current_year(client: TestClient):
    current_year = date.today().year
    create_income(
        client,
        amount="100.00",
        movement_date=iso_date(current_year - 1, 12, 31),
    )

    response = client.get("/api/balance-mensual/periodos")

    assert response.status_code == 200
    body = response.json()
    assert body["anio_actual"] == current_year
    assert current_year in body["anios"]
    assert current_year - 1 in body["anios"]
    assert body["anios"] == sorted(body["anios"], reverse=True)


def test_allocation_is_upserted(
    client: TestClient,
    test_session_factory: sessionmaker[Session],
):
    year = date.today().year
    assert update_allocation(client, year=year, month=3).status_code == 200
    assert (
        update_allocation(
            client,
            year=year,
            month=3,
            necessary="40.00",
            non_necessary="40.00",
            investment="20.00",
        ).status_code
        == 200
    )

    with test_session_factory() as session:
        allocations = session.scalars(select(MonthlyAllocation)).all()
        assert len(allocations) == 1
        assert allocations[0].necessary_percentage == 40
        assert allocations[0].non_necessary_percentage == 40
        assert allocations[0].investment_percentage == 20


def test_allocation_sum_over_100_returns_422(client: TestClient):
    year = date.today().year

    response = update_allocation(
        client,
        year=year,
        month=4,
        necessary="50.00",
        non_necessary="30.00",
        investment="20.01",
    )

    assert response.status_code == 422


def test_invalid_month_query_returns_422(client: TestClient):
    response = client.get("/api/balance-mensual?mes=13")

    assert response.status_code == 422
