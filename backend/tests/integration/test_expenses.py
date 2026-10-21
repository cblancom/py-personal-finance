from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Expense

pytestmark = pytest.mark.integration

PAYLOAD = {
    "fecha": "2026-10-21",
    "descripcion": "Mercado",
    "tipo": "NECESARIO",
    "valor": "120.50",
}

UPDATED_PAYLOAD = {
    "fecha": "2026-11-01",
    "descripcion": "Curso",
    "tipo": "INVERSION",
    "valor": "300.75",
}


def test_create_expense(client: TestClient):
    response = client.post("/api/gastos", json=PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "fecha": "2026-10-21",
        "descripcion": "Mercado",
        "tipo": "NECESARIO",
        "valor": "120.50",
    }


def test_list_expenses_returns_empty_list(client: TestClient):
    response = client.get("/api/gastos")

    assert response.status_code == 200
    assert response.json() == []


def test_list_expenses_orders_by_date_and_id_desc(client: TestClient):
    payloads = [
        {
            "fecha": "2026-10-20",
            "descripcion": "Primero",
            "tipo": "NECESARIO",
            "valor": "100.00",
        },
        {
            "fecha": "2026-10-21",
            "descripcion": "Segundo",
            "tipo": "NO_NECESARIO",
            "valor": "200.00",
        },
        {
            "fecha": "2026-10-21",
            "descripcion": "Tercero",
            "tipo": "INVERSION",
            "valor": "300.00",
        },
    ]

    for payload in payloads:
        assert client.post("/api/gastos", json=payload).status_code == 201

    response = client.get("/api/gastos")

    assert response.status_code == 200
    assert [expense["descripcion"] for expense in response.json()] == [
        "Tercero",
        "Segundo",
        "Primero",
    ]


def test_get_expense_by_id(client: TestClient):
    created = client.post("/api/gastos", json=PAYLOAD).json()

    response = client.get(f"/api/gastos/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_expense_returns_404(client: TestClient):
    response = client.get("/api/gastos/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Gasto no encontrado"}


def test_update_expense_updates_all_fields(client: TestClient):
    created = client.post("/api/gastos", json=PAYLOAD).json()

    response = client.put(f"/api/gastos/{created['id']}", json=UPDATED_PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {"id": created["id"], **UPDATED_PAYLOAD}

    fetched = client.get(f"/api/gastos/{created['id']}")
    assert fetched.json() == response.json()


def test_update_expense_returns_404(client: TestClient):
    response = client.put("/api/gastos/999", json=UPDATED_PAYLOAD)

    assert response.status_code == 404
    assert response.json() == {"detail": "Gasto no encontrado"}


def test_update_expense_rejects_invalid_type(client: TestClient):
    created = client.post("/api/gastos", json=PAYLOAD).json()

    response = client.put(
        f"/api/gastos/{created['id']}",
        json={**UPDATED_PAYLOAD, "tipo": "DESCONOCIDO"},
    )

    assert response.status_code == 422


def test_delete_expense_removes_record(client: TestClient):
    created = client.post("/api/gastos", json=PAYLOAD).json()

    response = client.delete(f"/api/gastos/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""

    missing = client.get(f"/api/gastos/{created['id']}")
    assert missing.status_code == 404


def test_delete_expense_returns_404(client: TestClient):
    response = client.delete("/api/gastos/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Gasto no encontrado"}


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        ("1500.5", "1500.50"),
        ("9999999999.99", "9999999999.99"),
    ],
)
def test_amount_round_trip_normalizes_two_decimals(
    client: TestClient, input_value: str, expected: str
):
    response = client.post("/api/gastos", json={**PAYLOAD, "valor": input_value})

    assert response.status_code == 201
    assert response.json()["valor"] == expected


def test_create_trims_description(client: TestClient):
    response = client.post(
        "/api/gastos",
        json={**PAYLOAD, "descripcion": "  Mercado  "},
    )

    assert response.status_code == 201
    assert response.json()["descripcion"] == "Mercado"


def test_create_accepts_200_character_description(client: TestClient):
    response = client.post(
        "/api/gastos",
        json={**PAYLOAD, "descripcion": "x" * 200},
    )

    assert response.status_code == 201
    assert len(response.json()["descripcion"]) == 200


@pytest.mark.parametrize("valor", ["0", "-1", "1.234", "10000000000.00", None])
def test_create_rejects_invalid_amount(client: TestClient, valor: str | None):
    response = client.post("/api/gastos", json={**PAYLOAD, "valor": valor})

    assert response.status_code == 422


@pytest.mark.parametrize("descripcion", ["", "   ", "x" * 201])
def test_create_rejects_invalid_description(client: TestClient, descripcion: str):
    response = client.post(
        "/api/gastos",
        json={**PAYLOAD, "descripcion": descripcion},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("fecha", ["", "21/10/2026", "not-a-date"])
def test_create_rejects_invalid_date(client: TestClient, fecha: str):
    response = client.post("/api/gastos", json={**PAYLOAD, "fecha": fecha})

    assert response.status_code == 422


@pytest.mark.parametrize("tipo", ["DESCONOCIDO", "necesario", " NECESARIO ", None])
def test_create_rejects_invalid_type(client: TestClient, tipo: str | None):
    response = client.post("/api/gastos", json={**PAYLOAD, "tipo": tipo})

    assert response.status_code == 422


def test_create_rejects_missing_fields(client: TestClient):
    response = client.post("/api/gastos", json={})

    assert response.status_code == 422


@pytest.mark.parametrize("valor", [Decimal("0"), Decimal("-1")])
def test_database_rejects_non_positive_amount(
    test_session_factory: sessionmaker[Session], valor: Decimal
):
    session = test_session_factory()
    try:
        session.add(
            Expense(
                date=date(2026, 10, 21),
                description="Mercado",
                expense_type="NECESARIO",
                amount=valor,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


@pytest.mark.parametrize("descripcion", ["", "   "])
def test_database_rejects_blank_description(
    test_session_factory: sessionmaker[Session], descripcion: str
):
    session = test_session_factory()
    try:
        session.add(
            Expense(
                date=date(2026, 10, 21),
                description=descripcion,
                expense_type="NECESARIO",
                amount=Decimal("100.00"),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


@pytest.mark.parametrize("tipo", ["OTRO", "necesario"])
def test_database_rejects_invalid_type(test_session_factory: sessionmaker[Session], tipo: str):
    session = test_session_factory()
    try:
        session.add(
            Expense(
                date=date(2026, 10, 21),
                description="Mercado",
                expense_type=tipo,
                amount=Decimal("100.00"),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()
