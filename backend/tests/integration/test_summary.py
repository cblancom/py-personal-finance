from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

EMPTY_BREAKDOWN = {
    "NECESARIO": "0.00",
    "NO_NECESARIO": "0.00",
    "INVERSION": "0.00",
}


def create_income(
    client: TestClient,
    valor: str,
    fecha: str = "2026-10-21",
    descripcion: str = "Ingreso",
):
    response = client.post(
        "/api/ingresos",
        json={"fecha": fecha, "descripcion": descripcion, "valor": valor},
    )
    assert response.status_code == 201
    return response.json()


def create_expense(
    client: TestClient,
    valor: str,
    tipo: str,
    fecha: str = "2026-10-21",
    descripcion: str = "Gasto",
):
    response = client.post(
        "/api/gastos",
        json={
            "fecha": fecha,
            "descripcion": descripcion,
            "tipo": tipo,
            "valor": valor,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_empty_summary(client: TestClient):
    response = client.get("/api/resumen")

    assert response.status_code == 200
    assert response.json() == {
        "total_ingresos": "0.00",
        "total_gastos": "0.00",
        "balance": "0.00",
        "gastos_por_tipo": EMPTY_BREAKDOWN,
    }


def test_summary_with_only_incomes(client: TestClient):
    create_income(client, "1000.00")
    create_income(client, "500.25")

    response = client.get("/api/resumen")

    assert response.status_code == 200
    assert response.json() == {
        "total_ingresos": "1500.25",
        "total_gastos": "0.00",
        "balance": "1500.25",
        "gastos_por_tipo": EMPTY_BREAKDOWN,
    }


def test_summary_with_only_expenses(client: TestClient):
    create_expense(client, "300.00", "NECESARIO")
    create_expense(client, "200.00", "NECESARIO")
    create_expense(client, "100.50", "NO_NECESARIO")
    create_expense(client, "50.00", "INVERSION")

    response = client.get("/api/resumen")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "total_ingresos": "0.00",
        "total_gastos": "650.50",
        "balance": "-650.50",
        "gastos_por_tipo": {
            "NECESARIO": "500.00",
            "NO_NECESARIO": "100.50",
            "INVERSION": "50.00",
        },
    }

    breakdown_total = sum(
        (Decimal(value) for value in data["gastos_por_tipo"].values()),
        Decimal("0.00"),
    )
    assert breakdown_total == Decimal(data["total_gastos"])


def test_summary_with_mixed_movements(client: TestClient):
    create_income(client, "2000.00")
    create_income(client, "500.50")
    create_expense(client, "300.00", "NECESARIO")
    create_expense(client, "200.25", "NO_NECESARIO")
    create_expense(client, "1000.00", "INVERSION")

    response = client.get("/api/resumen")

    assert response.status_code == 200
    assert response.json() == {
        "total_ingresos": "2500.50",
        "total_gastos": "1500.25",
        "balance": "1000.25",
        "gastos_por_tipo": {
            "NECESARIO": "300.00",
            "NO_NECESARIO": "200.25",
            "INVERSION": "1000.00",
        },
    }


def test_summary_includes_missing_types_as_zero(client: TestClient):
    create_expense(client, "100.00", "NECESARIO")

    response = client.get("/api/resumen")

    assert response.status_code == 200
    assert response.json()["gastos_por_tipo"] == {
        "NECESARIO": "100.00",
        "NO_NECESARIO": "0.00",
        "INVERSION": "0.00",
    }
