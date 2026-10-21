import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

PAYLOAD = {
    "fecha": "2026-10-21",
    "descripcion": "Salario",
    "valor": "1500.50",
}

UPDATED_PAYLOAD = {
    "fecha": "2026-11-01",
    "descripcion": "Salario ajustado",
    "valor": "1750.75",
}


def test_create_income(client: TestClient):
    response = client.post("/api/ingresos", json=PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "fecha": "2026-10-21",
        "descripcion": "Salario",
        "valor": "1500.50",
    }


def test_list_incomes_returns_empty_list(client: TestClient):
    response = client.get("/api/ingresos")

    assert response.status_code == 200
    assert response.json() == []


def test_list_incomes_orders_by_date_and_id_desc(client: TestClient):
    payloads = [
        {"fecha": "2026-10-20", "descripcion": "Primero", "valor": "100.00"},
        {"fecha": "2026-10-21", "descripcion": "Segundo", "valor": "200.00"},
        {"fecha": "2026-10-21", "descripcion": "Tercero", "valor": "300.00"},
    ]

    for payload in payloads:
        assert client.post("/api/ingresos", json=payload).status_code == 201

    response = client.get("/api/ingresos")

    assert response.status_code == 200
    assert [income["descripcion"] for income in response.json()] == [
        "Tercero",
        "Segundo",
        "Primero",
    ]


def test_get_income_by_id(client: TestClient):
    created = client.post("/api/ingresos", json=PAYLOAD).json()

    response = client.get(f"/api/ingresos/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_income_returns_404(client: TestClient):
    response = client.get("/api/ingresos/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ingreso no encontrado"}


def test_update_income_updates_all_fields(client: TestClient):
    created = client.post("/api/ingresos", json=PAYLOAD).json()

    response = client.put(f"/api/ingresos/{created['id']}", json=UPDATED_PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {"id": created["id"], **UPDATED_PAYLOAD}

    fetched = client.get(f"/api/ingresos/{created['id']}")
    assert fetched.json() == response.json()


def test_update_income_returns_404(client: TestClient):
    response = client.put("/api/ingresos/999", json=UPDATED_PAYLOAD)

    assert response.status_code == 404
    assert response.json() == {"detail": "Ingreso no encontrado"}


def test_update_income_rejects_invalid_payload(client: TestClient):
    created = client.post("/api/ingresos", json=PAYLOAD).json()

    response = client.put(
        f"/api/ingresos/{created['id']}",
        json={**UPDATED_PAYLOAD, "valor": "0"},
    )

    assert response.status_code == 422


def test_delete_income_removes_record(client: TestClient):
    created = client.post("/api/ingresos", json=PAYLOAD).json()

    response = client.delete(f"/api/ingresos/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""

    missing = client.get(f"/api/ingresos/{created['id']}")
    assert missing.status_code == 404


def test_delete_income_returns_404(client: TestClient):
    response = client.delete("/api/ingresos/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ingreso no encontrado"}
