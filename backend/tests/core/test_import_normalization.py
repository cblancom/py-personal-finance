from datetime import date, datetime
from decimal import Decimal

import pytest

from app.db.models import ExpenseType
from app.services.imports import (
    build_fingerprint,
    canonical_header,
    map_headers,
    normalize_expense_type,
    normalize_header,
    normalize_income_category,
    normalize_key,
    parse_amount,
    parse_date,
)


def test_normalize_key_removes_accents_case_and_separators():
    assert normalize_key("  No_Necesario  ") == "no necesario"
    assert normalize_header("Descripción") == "descripcion"
    assert normalize_header("FECHA") == "fecha"


def test_canonical_header_maps_aliases():
    assert canonical_header("date") == "fecha"
    assert canonical_header("Monto") == "valor"
    assert canonical_header("tipo") == "categoria"
    assert canonical_header("desconocida") is None


def test_map_headers_returns_positions_and_ignores_unknown_columns():
    mapping = map_headers(["Fecha", "Descripción", "Valor", "Comentario"])

    assert mapping.is_valid
    assert dict(mapping.positions) == {
        "fecha": 0,
        "descripcion": 1,
        "valor": 2,
    }
    assert mapping.errors == ()


def test_map_headers_requires_mandatory_columns():
    mapping = map_headers(["Fecha", "Descripción"])

    assert not mapping.is_valid
    assert [issue.message for issue in mapping.errors] == ["Falta la columna obligatoria 'valor'."]


def test_map_headers_rejects_duplicate_aliases():
    mapping = map_headers(["Fecha", "Date", "Descripción", "Valor"])

    assert not mapping.is_valid
    assert mapping.errors[0].message == "La columna 'fecha' está duplicada."


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("necesario", ExpenseType.NECESSARY),
        ("No Necesario", ExpenseType.NON_NECESSARY),
        ("no_necesario", ExpenseType.NON_NECESSARY),
        ("no-necesario", ExpenseType.NON_NECESSARY),
        ("Inversión", ExpenseType.INVESTMENT),
        ("inversion", ExpenseType.INVESTMENT),
    ],
)
def test_normalize_expense_type_aliases(value, expected):
    assert normalize_expense_type(value) == expected


def test_normalize_expense_type_rejects_unknown_category():
    assert normalize_expense_type("Mercado") is None


def test_normalize_income_category():
    assert normalize_income_category(None) is None
    assert normalize_income_category("   ") is None
    assert normalize_income_category("  Nómina  ") == "Nómina"


def test_normalize_income_category_rejects_long_text():
    with pytest.raises(ValueError, match="100 caracteres"):
        normalize_income_category("x" * 101)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (date(2026, 10, 21), date(2026, 10, 21)),
        (datetime(2026, 10, 21, 12, 30), date(2026, 10, 21)),
        ("2026-10-21", date(2026, 10, 21)),
        ("21/10/2026", date(2026, 10, 21)),
        (" 21/10/2026 ", date(2026, 10, 21)),
    ],
)
def test_parse_date_accepts_supported_values(value, expected):
    assert parse_date(value) == expected


@pytest.mark.parametrize("value", ["", "  ", "21-10-2026", "not-a-date", None, 123])
def test_parse_date_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        parse_date(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1500.5", Decimal("1500.50")),
        ("1500,5", Decimal("1500.50")),
        ("1.500,50", Decimal("1500.50")),
        ("1,500.50", Decimal("1500.50")),
        ("9999999999.99", Decimal("9999999999.99")),
        (1500.5, Decimal("1500.50")),
        (1500, Decimal("1500.00")),
        (Decimal("10"), Decimal("10.00")),
    ],
)
def test_parse_amount_accepts_valid_values(value, expected):
    assert parse_amount(value) == expected


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("0", "mayor que 0"),
        ("-1", "mayor que 0"),
        ("1.234", "2 decimales"),
        ("10000000000.00", "12 dígitos"),
        ("abc", "no es válido"),
        ("$1.000", "no es válido"),
        ("", "obligatorio"),
        (None, "no es válido"),
    ],
)
def test_parse_amount_rejects_invalid_values(value, message):
    with pytest.raises(ValueError, match=message):
        parse_amount(value)


def test_build_fingerprint_is_stable_and_normalizes_text():
    first = build_fingerprint(
        movement_type="INGRESO",
        fecha=date(2026, 10, 21),
        descripcion="  Nómina   mensual ",
        valor=Decimal("1500.50"),
        categoria="Nómina",
    )
    second = build_fingerprint(
        movement_type="INGRESO",
        fecha=date(2026, 10, 21),
        descripcion="nomina mensual",
        valor=Decimal("1500.50"),
        categoria="nomina",
    )

    assert first == second
    assert len(first) == 64


def test_build_fingerprint_changes_with_amount_or_category():
    base = {
        "movement_type": "GASTO",
        "fecha": date(2026, 10, 21),
        "descripcion": "Mercado",
        "valor": Decimal("120.50"),
        "tipo_gasto": "NECESARIO",
    }

    assert build_fingerprint(**base) != build_fingerprint(**{**base, "valor": Decimal("120.51")})
    assert build_fingerprint(**base) != build_fingerprint(**{**base, "tipo_gasto": "NO_NECESARIO"})
