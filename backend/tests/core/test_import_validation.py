from datetime import date
from decimal import Decimal

import pytest

from app.db.models import ExpenseType, ImportMovementType
from app.services.imports import validate_import_row


def test_valid_income_with_optional_category():
    row = validate_import_row(
        movement_type="INGRESO",
        fecha="2026-10-21",
        descripcion="  Salario  ",
        valor="1.500,50",
        categoria="  Nómina  ",
    )

    assert row.is_valid
    assert row.date == date(2026, 10, 21)
    assert row.description == "Salario"
    assert row.amount == Decimal("1500.50")
    assert row.category == "Nómina"
    assert row.expense_type is None
    assert row.fingerprint is not None


def test_valid_income_without_category():
    row = validate_import_row(
        movement_type=ImportMovementType.INCOME,
        fecha=date(2026, 10, 21),
        descripcion="Salario",
        valor=Decimal("1500.50"),
    )

    assert row.is_valid
    assert row.category is None
    assert row.fingerprint is not None


def test_valid_expense_maps_category_to_type():
    row = validate_import_row(
        movement_type="GASTO",
        fecha="21/10/2026",
        descripcion="Mercado",
        valor="120,50",
        categoria="No Necesario",
    )

    assert row.is_valid
    assert row.expense_type == ExpenseType.NON_NECESSARY
    assert row.category == "No Necesario"
    assert row.amount == Decimal("120.50")
    assert row.fingerprint is not None


def test_expense_category_is_required():
    row = validate_import_row(
        movement_type="GASTO",
        fecha="2026-10-21",
        descripcion="Mercado",
        valor="120.50",
        categoria="",
    )

    assert not row.is_valid
    assert [issue.field for issue in row.errors] == ["categoria"]
    assert row.errors[0].message == "La categoría es obligatoria para gastos."


def test_expense_category_must_be_known():
    row = validate_import_row(
        movement_type="GASTO",
        fecha="2026-10-21",
        descripcion="Mercado",
        valor="120.50",
        categoria="Mercado",
    )

    assert not row.is_valid
    assert row.errors[0].message == "La categoría del gasto no es válida."


def test_invalid_fields_are_collected_without_fingerprint():
    row = validate_import_row(
        movement_type="GASTO",
        fecha=None,
        descripcion="",
        valor="0",
        categoria="",
    )

    assert not row.is_valid
    assert [issue.field for issue in row.errors] == [
        "fecha",
        "descripcion",
        "valor",
        "categoria",
    ]
    assert row.fingerprint is None


def test_invalid_movement_type_is_rejected():
    row = validate_import_row(
        movement_type="OTRO",
        fecha="2026-10-21",
        descripcion="Salario",
        valor="100.00",
    )

    assert not row.is_valid
    assert [issue.field for issue in row.errors] == ["tipo_movimiento"]


def test_invalid_date_and_amount_messages_are_clear():
    row = validate_import_row(
        movement_type="INGRESO",
        fecha="21-10-2026",
        descripcion="Salario",
        valor="1.234",
    )

    assert not row.is_valid
    assert [issue.message for issue in row.errors] == [
        "La fecha no es válida.",
        "El valor admite como máximo 2 decimales.",
    ]


def test_income_category_length_is_validated():
    row = validate_import_row(
        movement_type="INGRESO",
        fecha="2026-10-21",
        descripcion="Salario",
        valor="100.00",
        categoria="x" * 101,
    )

    assert not row.is_valid
    assert row.errors[0].message == "La categoría no puede superar los 100 caracteres."


@pytest.mark.parametrize(
    ("description", "message"),
    [
        ("", "La descripción es obligatoria."),
        ("x" * 201, "La descripción no puede superar los 200 caracteres."),
    ],
)
def test_description_validation(description, message):
    row = validate_import_row(
        movement_type="INGRESO",
        fecha="2026-10-21",
        descripcion=description,
        valor="100.00",
    )

    assert not row.is_valid
    assert row.errors[0].message == message
