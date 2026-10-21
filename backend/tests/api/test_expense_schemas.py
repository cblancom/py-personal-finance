from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.api.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.db.models.expense import ExpenseType

VALID_PAYLOAD = {
    "fecha": "2026-10-21",
    "descripcion": "Mercado",
    "tipo": "NECESARIO",
    "valor": "120.50",
}


def payload(**overrides):
    return {**VALID_PAYLOAD, **overrides}


@pytest.mark.parametrize("tipo", ["NECESARIO", "NO_NECESARIO", "INVERSION"])
def test_create_accepts_all_expense_types(tipo):
    expense = ExpenseCreate.model_validate(payload(tipo=tipo))

    assert expense.tipo == ExpenseType(tipo)


def test_create_trims_description():
    expense = ExpenseCreate.model_validate(payload(descripcion="  Mercado  "))

    assert expense.descripcion == "Mercado"


def test_create_accepts_numeric_amount():
    expense = ExpenseCreate.model_validate(payload(valor=120.5))

    assert expense.valor == Decimal("120.5")


def test_create_accepts_boundary_amount():
    expense = ExpenseCreate.model_validate(payload(valor="9999999999.99"))

    assert expense.valor == Decimal("9999999999.99")


def test_create_accepts_future_date():
    expense = ExpenseCreate.model_validate(payload(fecha="2099-01-01"))

    assert expense.fecha == date(2099, 1, 1)


@pytest.mark.parametrize(
    "tipo",
    ["DESCONOCIDO", "necesario", " NECESARIO ", None],
)
def test_create_rejects_invalid_type(tipo):
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate(payload(tipo=tipo))


@pytest.mark.parametrize("valor", ["0", "-1", "1.234", "10000000000.00", None])
def test_create_rejects_invalid_amount(valor):
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate(payload(valor=valor))


@pytest.mark.parametrize("descripcion", ["", "   ", "x" * 201])
def test_create_rejects_invalid_description(descripcion):
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate(payload(descripcion=descripcion))


def test_create_accepts_200_character_description():
    expense = ExpenseCreate.model_validate(payload(descripcion="x" * 200))

    assert len(expense.descripcion) == 200


@pytest.mark.parametrize("fecha", ["", "21/10/2026", "not-a-date"])
def test_create_rejects_invalid_date(fecha):
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate(payload(fecha=fecha))


def test_create_requires_all_fields():
    with pytest.raises(ValidationError):
        ExpenseCreate.model_validate({})


def test_update_accepts_full_payload():
    expense = ExpenseUpdate.model_validate(payload(tipo="INVERSION"))

    assert expense.tipo == ExpenseType.INVESTMENT


def test_read_serializes_contract_fields():
    expense = ExpenseRead.model_validate({**VALID_PAYLOAD, "id": 1})

    assert expense.model_dump(mode="json") == {
        "id": 1,
        "fecha": "2026-10-21",
        "descripcion": "Mercado",
        "tipo": "NECESARIO",
        "valor": "120.50",
    }


def test_read_requires_id():
    with pytest.raises(ValidationError):
        ExpenseRead.model_validate(VALID_PAYLOAD)
