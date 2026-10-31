from datetime import date

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

EMPTY_MONTH = {
    "NECESARIO": "0.00",
    "NO_NECESARIO": "0.00",
    "INVERSION": "0.00",
}


def iso_date(year: int, month: int, day: int = 1) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}"


def create_expense(
    client: TestClient,
    *,
    amount: str,
    movement_date: str,
    expense_type: str,
):
    response = client.post(
        "/api/gastos",
        json={
            "fecha": movement_date,
            "descripcion": "Gasto",
            "tipo": expense_type,
            "valor": amount,
        },
    )
    assert response.status_code == 201


def create_income(client: TestClient, *, amount: str, movement_date: str):
    response = client.post(
        "/api/ingresos",
        json={
            "fecha": movement_date,
            "descripcion": "Ingreso",
            "valor": amount,
        },
    )
    assert response.status_code == 201


def test_monthly_expense_series_fills_all_months(client: TestClient):
    year = date.today().year
    create_expense(
        client,
        amount="100.00",
        movement_date=iso_date(year, 1),
        expense_type="NECESARIO",
    )
    create_expense(
        client,
        amount="50.00",
        movement_date=iso_date(year, 1),
        expense_type="NO_NECESARIO",
    )
    create_expense(
        client,
        amount="20.00",
        movement_date=iso_date(year, 2),
        expense_type="INVERSION",
    )

    response = client.get(f"/api/graficos/gastos-mensuales?anio={year}")

    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == year
    assert len(body["meses"]) == 12
    assert body["meses"][0] == {
        "mes": 1,
        "gastos_por_tipo": {
            "NECESARIO": "100.00",
            "NO_NECESARIO": "50.00",
            "INVERSION": "0.00",
        },
    }
    assert body["meses"][1]["gastos_por_tipo"] == {
        "NECESARIO": "0.00",
        "NO_NECESARIO": "0.00",
        "INVERSION": "20.00",
    }
    assert body["meses"][2] == {"mes": 3, "gastos_por_tipo": EMPTY_MONTH}


def test_monthly_expense_series_uses_current_year_and_excludes_incomes(
    client: TestClient,
):
    year = date.today().year
    create_income(client, amount="1000.00", movement_date=iso_date(year, 1))
    create_expense(
        client,
        amount="75.00",
        movement_date=iso_date(year, 1),
        expense_type="NECESARIO",
    )

    response = client.get("/api/graficos/gastos-mensuales")

    assert response.status_code == 200
    body = response.json()
    assert body["anio"] == year
    assert body["meses"][0]["gastos_por_tipo"]["NECESARIO"] == "75.00"
    assert body["meses"][0]["gastos_por_tipo"]["INVERSION"] == "0.00"


def test_monthly_expense_series_filters_by_year(client: TestClient):
    current_year = date.today().year
    previous_year = current_year - 1
    create_expense(
        client,
        amount="999.00",
        movement_date=iso_date(previous_year, 12),
        expense_type="NECESARIO",
    )

    current_response = client.get(f"/api/graficos/gastos-mensuales?anio={current_year}")
    previous_response = client.get(f"/api/graficos/gastos-mensuales?anio={previous_year}")

    assert current_response.status_code == 200
    assert all(
        month["gastos_por_tipo"] == EMPTY_MONTH for month in current_response.json()["meses"]
    )
    assert previous_response.status_code == 200
    assert previous_response.json()["meses"][11]["gastos_por_tipo"]["NECESARIO"] == "999.00"


def test_monthly_expense_series_rejects_invalid_year(client: TestClient):
    response = client.get("/api/graficos/gastos-mensuales?anio=1800")

    assert response.status_code == 422
