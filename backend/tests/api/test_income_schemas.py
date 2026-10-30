from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.api.schemas.income import IncomeCreate, IncomeRead, IncomeUpdate

VALID_PAYLOAD = {
    "fecha": "2026-10-21",
    "descripcion": "Salario",
    "valor": "1500.50",
}


def payload(**overrides):
    return {**VALID_PAYLOAD, **overrides}


def test_create_accepts_valid_payload():
    income = IncomeCreate.model_validate(VALID_PAYLOAD)

    assert income.fecha == date(2026, 10, 21)
    assert income.descripcion == "Salario"
    assert income.categoria is None
    assert income.valor == Decimal("1500.50")


def test_create_trims_description():
    income = IncomeCreate.model_validate(payload(descripcion="  Salario  "))

    assert income.descripcion == "Salario"


def test_create_accepts_optional_category():
    income = IncomeCreate.model_validate(payload(categoria="  Salario  "))

    assert income.categoria == "Salario"


def test_create_normalizes_blank_category():
    income = IncomeCreate.model_validate(payload(categoria="   "))

    assert income.categoria is None


def test_create_rejects_long_category():
    with pytest.raises(ValidationError):
        IncomeCreate.model_validate(payload(categoria="x" * 101))


def test_create_accepts_numeric_amount():
    income = IncomeCreate.model_validate(payload(valor=1500.5))

    assert income.valor == Decimal("1500.5")


def test_create_accepts_boundary_amount():
    income = IncomeCreate.model_validate(payload(valor="9999999999.99"))

    assert income.valor == Decimal("9999999999.99")


def test_create_accepts_future_date():
    income = IncomeCreate.model_validate(payload(fecha="2099-01-01"))

    assert income.fecha == date(2099, 1, 1)


@pytest.mark.parametrize("valor", ["0", "-1", "1.234", "10000000000.00", None])
def test_create_rejects_invalid_amount(valor):
    with pytest.raises(ValidationError):
        IncomeCreate.model_validate(payload(valor=valor))


@pytest.mark.parametrize("descripcion", ["", "   ", "x" * 201])
def test_create_rejects_invalid_description(descripcion):
    with pytest.raises(ValidationError):
        IncomeCreate.model_validate(payload(descripcion=descripcion))


def test_create_accepts_200_character_description():
    income = IncomeCreate.model_validate(payload(descripcion="x" * 200))

    assert len(income.descripcion) == 200


@pytest.mark.parametrize("fecha", ["", "21/10/2026", "not-a-date"])
def test_create_rejects_invalid_date(fecha):
    with pytest.raises(ValidationError):
        IncomeCreate.model_validate(payload(fecha=fecha))


def test_create_requires_all_fields():
    with pytest.raises(ValidationError):
        IncomeCreate.model_validate({})


def test_update_accepts_full_payload():
    income = IncomeUpdate.model_validate(VALID_PAYLOAD)

    assert income.valor == Decimal("1500.50")


def test_read_serializes_decimal_as_string():
    income = IncomeRead.model_validate({**VALID_PAYLOAD, "id": 1})

    assert income.model_dump(mode="json") == {
        "id": 1,
        "fecha": "2026-10-21",
        "descripcion": "Salario",
        "categoria": None,
        "valor": "1500.50",
    }


def test_read_requires_id():
    with pytest.raises(ValidationError):
        IncomeRead.model_validate(VALID_PAYLOAD)
