from app.services.imports import ImportFileError, csv_parser
from app.services.imports.csv_parser import parse_csv


def encode(text: str) -> bytes:
    return text.encode("utf-8")


def test_parse_csv_with_accents_and_comma_delimiter():
    parsed = parse_csv(encode("Fecha,Descripción,Valor,Categoría\n2026-10-21,Salario,1500.50,\n"))

    assert dict(parsed.headers) == {
        "fecha": 0,
        "descripcion": 1,
        "valor": 2,
        "categoria": 3,
    }
    assert len(parsed.rows) == 1
    row = parsed.rows[0]
    assert row.row_number == 2
    assert row.fecha == "2026-10-21"
    assert row.descripcion == "Salario"
    assert row.valor == "1500.50"
    assert row.categoria is None


def test_parse_csv_with_semicolon_alias_headers_and_leading_blank_rows():
    parsed = parse_csv(
        encode(
            "\n"
            "Monto;Date;Detalle;Comentario\n"
            "120,50;21/10/2026;Mercado;ignorado\n"
            "\n"
            "45,00;22/10/2026;Cine;ignorado\n"
        )
    )

    assert dict(parsed.headers) == {
        "valor": 0,
        "fecha": 1,
        "descripcion": 2,
    }
    assert [row.row_number for row in parsed.rows] == [3, 5]
    assert parsed.rows[0].valor == "120,50"
    assert parsed.rows[0].fecha == "21/10/2026"
    assert parsed.rows[1].descripcion == "Cine"


def test_parse_csv_accepts_bom_and_utf8():
    parsed = parse_csv(b"\xef\xbb\xbfFecha,Descripcion,Valor\n2026-10-21,Salario,10.00\n")

    assert len(parsed.rows) == 1
    assert parsed.rows[0].descripcion == "Salario"


def test_parse_csv_rejects_missing_headers():
    try:
        parse_csv(encode("Fecha,Descripcion\n2026-10-21,Salario\n"))
    except ImportFileError as exc:
        assert exc.issues
        assert exc.issues[0].message == "Falta la columna obligatoria 'valor'."
    else:
        raise AssertionError("Se esperaba ImportFileError")


def test_parse_csv_rejects_duplicate_headers():
    try:
        parse_csv(encode("Fecha,Date,Descripcion,Valor\n2026-10-21,2026-10-21,Salario,10\n"))
    except ImportFileError as exc:
        assert "duplicada" in exc.issues[0].message
    else:
        raise AssertionError("Se esperaba ImportFileError")


def test_parse_csv_rejects_empty_and_invalid_encoding():
    for content in (b"", b"   ", b"\xff\xfe"):
        try:
            parse_csv(content)
        except ImportFileError:
            pass
        else:
            raise AssertionError("Se esperaba ImportFileError")


def test_parse_csv_rejects_too_many_rows(monkeypatch):
    monkeypatch.setattr(csv_parser, "MAX_IMPORT_ROWS", 1)
    content = encode("Fecha,Descripcion,Valor\n2026-10-21,Primero,10\n2026-10-22,Segundo,20\n")

    try:
        parse_csv(content)
    except ImportFileError as exc:
        assert "máximo de filas" in str(exc)
    else:
        raise AssertionError("Se esperaba ImportFileError")


def test_parse_csv_rejects_too_large_file(monkeypatch):
    monkeypatch.setattr(csv_parser, "MAX_IMPORT_BYTES", 1)

    try:
        parse_csv(encode("Fecha,Descripcion,Valor\n"))
    except ImportFileError as exc:
        assert "tamaño máximo" in str(exc)
    else:
        raise AssertionError("Se esperaba ImportFileError")
