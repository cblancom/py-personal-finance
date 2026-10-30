from datetime import date
from io import BytesIO

from openpyxl import Workbook

from app.services.imports import ImportFileError, xlsx_parser
from app.services.imports.xlsx_parser import parse_xlsx


def build_xlsx(rows: list[list[object]], extra_sheet: bool = False) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    if extra_sheet:
        second = workbook.create_sheet("Otra")
        second.append(["Fecha", "Descripcion", "Valor"])
        second.append(["2026-10-22", "Ignorado", 1])
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


def test_parse_xlsx_with_dates_and_numbers():
    parsed = parse_xlsx(
        build_xlsx(
            [
                ["Fecha", "Descripción", "Valor", "Categoría"],
                [date(2026, 10, 21), "Salario", 1500.5, None],
            ]
        )
    )

    assert dict(parsed.headers) == {
        "fecha": 0,
        "descripcion": 1,
        "valor": 2,
        "categoria": 3,
    }
    assert len(parsed.rows) == 1
    row = parsed.rows[0]
    assert row.row_number == 2
    assert isinstance(row.fecha, date)
    assert row.descripcion == "Salario"
    assert row.valor == 1500.5
    assert row.categoria is None


def test_parse_xlsx_uses_first_sheet_and_skips_empty_rows():
    parsed = parse_xlsx(
        build_xlsx(
            [
                [],
                ["Fecha", "Descripcion", "Valor"],
                [],
                ["2026-10-21", "Salario", 10],
            ],
            extra_sheet=True,
        )
    )

    assert [row.row_number for row in parsed.rows] == [4]
    assert parsed.rows[0].descripcion == "Salario"


def test_parse_xlsx_rejects_invalid_structure():
    try:
        parse_xlsx(build_xlsx([["Fecha", "Descripcion"]]))
    except ImportFileError as exc:
        assert exc.issues[0].message == "Falta la columna obligatoria 'valor'."
    else:
        raise AssertionError("Se esperaba ImportFileError")


def test_parse_xlsx_rejects_empty_and_invalid_content():
    for content in (b"", b"not-an-xlsx"):
        try:
            parse_xlsx(content)
        except ImportFileError:
            pass
        else:
            raise AssertionError("Se esperaba ImportFileError")


def test_parse_xlsx_rejects_too_many_rows(monkeypatch):
    monkeypatch.setattr(xlsx_parser, "MAX_IMPORT_ROWS", 1)
    content = build_xlsx(
        [
            ["Fecha", "Descripcion", "Valor"],
            ["2026-10-21", "Primero", 10],
            ["2026-10-22", "Segundo", 20],
        ]
    )

    try:
        parse_xlsx(content)
    except ImportFileError as exc:
        assert "máximo de filas" in str(exc)
    else:
        raise AssertionError("Se esperaba ImportFileError")


def test_parse_xlsx_rejects_too_large_file(monkeypatch):
    monkeypatch.setattr(xlsx_parser, "MAX_IMPORT_BYTES", 1)

    try:
        parse_xlsx(build_xlsx([["Fecha", "Descripcion", "Valor"]]))
    except ImportFileError as exc:
        assert "tamaño máximo" in str(exc)
    else:
        raise AssertionError("Se esperaba ImportFileError")
