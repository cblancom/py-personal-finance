import csv
from datetime import date
from decimal import Decimal
from io import BytesIO, StringIO

from openpyxl import load_workbook

from app.db.models import Expense, Income
from app.services.exports import (
    EXPENSE_HEADERS,
    INCOME_HEADERS,
    export_expenses_csv,
    export_expenses_xlsx,
    export_incomes_csv,
    export_incomes_xlsx,
)


def income(
    *,
    description: str = "Salario",
    income_type: str | None = "NO_NECESARIO",
    amount: Decimal = Decimal("1500.5"),
) -> Income:
    return Income(
        date=date(2026, 10, 21),
        description=description,
        income_type=income_type,
        amount=amount,
    )


def expense(
    *,
    description: str = "Mercado",
    expense_type: str = "NECESARIO",
    amount: Decimal = Decimal("120.5"),
) -> Expense:
    return Expense(
        date=date(2026, 10, 22),
        description=description,
        expense_type=expense_type,
        amount=amount,
    )


def csv_rows(payload: bytes) -> list[list[str]]:
    return list(csv.reader(StringIO(payload.decode("utf-8-sig"))))


def xlsx_rows(payload: bytes) -> tuple[str, list[tuple[object, ...]]]:
    workbook = load_workbook(BytesIO(payload), read_only=True, data_only=True)
    try:
        worksheet = workbook.worksheets[0]
        return worksheet.title, list(worksheet.iter_rows(values_only=True))
    finally:
        workbook.close()


def test_incomes_csv_uses_bom_headers_and_two_decimal_values():
    payload = export_incomes_csv([income()])

    assert payload.startswith(b"\xef\xbb\xbf")
    assert csv_rows(payload) == [
        list(INCOME_HEADERS),
        ["2026-10-21", "Salario", "1500.50", "NO_NECESARIO"],
    ]


def test_incomes_csv_preserves_special_description_characters():
    description = 'Salario, "octubre"\nquincena'

    payload = export_incomes_csv([income(description=description)])

    assert csv_rows(payload)[1][1] == description


def test_incomes_csv_exports_income_without_type_as_empty_category():
    payload = export_incomes_csv([income(income_type=None)])

    assert csv_rows(payload)[1][3] == ""


def test_incomes_xlsx_has_one_sheet_and_header():
    payload = export_incomes_xlsx([income()])

    title, rows = xlsx_rows(payload)

    assert title == "Ingresos"
    assert rows == [
        INCOME_HEADERS,
        ("2026-10-21", "Salario", "1500.50", "NO_NECESARIO"),
    ]


def test_expenses_csv_uses_tipo_de_gasto_header():
    payload = export_expenses_csv([expense()])

    assert csv_rows(payload) == [
        list(EXPENSE_HEADERS),
        ["2026-10-22", "Mercado", "120.50", "NECESARIO"],
    ]


def test_expenses_xlsx_has_one_sheet_and_header():
    payload = export_expenses_xlsx([expense()])

    title, rows = xlsx_rows(payload)

    assert title == "Gastos"
    assert rows == [
        EXPENSE_HEADERS,
        ("2026-10-22", "Mercado", "120.50", "NECESARIO"),
    ]


def test_empty_exports_contain_only_headers():
    assert csv_rows(export_incomes_csv([])) == [list(INCOME_HEADERS)]
    assert csv_rows(export_expenses_csv([])) == [list(EXPENSE_HEADERS)]
    assert xlsx_rows(export_incomes_xlsx([])) == ("Ingresos", [INCOME_HEADERS])
    assert xlsx_rows(export_expenses_xlsx([])) == ("Gastos", [EXPENSE_HEADERS])
