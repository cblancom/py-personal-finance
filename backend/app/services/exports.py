import csv
from collections.abc import Iterable, Sequence
from decimal import Decimal
from io import BytesIO, StringIO

from openpyxl import Workbook

from app.db.models import Expense, Income

INCOME_HEADERS = ("Fecha", "Descripcion", "Valor", "Categoria")
EXPENSE_HEADERS = ("Fecha", "Descripcion", "Valor", "Tipo de gasto")


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def _type_value(value: object) -> str:
    return "" if value is None else str(value)


def _csv_bytes(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> bytes:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, delimiter=",", lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def _xlsx_bytes(
    sheet_title: str,
    headers: Sequence[str],
    rows: Iterable[Sequence[str]],
) -> bytes:
    workbook = Workbook()
    worksheet = workbook.worksheets[0]
    worksheet.title = sheet_title
    worksheet.append(list(headers))
    for row in rows:
        worksheet.append(list(row))

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


def _income_row(income: Income) -> tuple[str, str, str, str]:
    return (
        income.date.isoformat(),
        income.description,
        _money(income.amount),
        _type_value(income.income_type),
    )


def _expense_row(expense: Expense) -> tuple[str, str, str, str]:
    return (
        expense.date.isoformat(),
        expense.description,
        _money(expense.amount),
        _type_value(expense.expense_type),
    )


def export_incomes_csv(incomes: Iterable[Income]) -> bytes:
    return _csv_bytes(INCOME_HEADERS, (_income_row(income) for income in incomes))


def export_incomes_xlsx(incomes: Iterable[Income]) -> bytes:
    return _xlsx_bytes(
        "Ingresos",
        INCOME_HEADERS,
        (_income_row(income) for income in incomes),
    )


def export_expenses_csv(expenses: Iterable[Expense]) -> bytes:
    return _csv_bytes(EXPENSE_HEADERS, (_expense_row(expense) for expense in expenses))


def export_expenses_xlsx(expenses: Iterable[Expense]) -> bytes:
    return _xlsx_bytes(
        "Gastos",
        EXPENSE_HEADERS,
        (_expense_row(expense) for expense in expenses),
    )
