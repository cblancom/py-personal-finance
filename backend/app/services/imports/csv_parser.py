import csv
import io
from collections.abc import Sequence

from app.services.imports.errors import ImportFileError
from app.services.imports.limits import MAX_IMPORT_BYTES, MAX_IMPORT_ROWS
from app.services.imports.normalization import map_headers
from app.services.imports.parsed import ParsedImport, ParsedRow


def _ensure_size(content: bytes) -> None:
    if len(content) > MAX_IMPORT_BYTES:
        raise ImportFileError("El archivo supera el tamaño máximo permitido.")


def _detect_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:5])
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;").delimiter
    except csv.Error:
        return ";" if sample.count(";") > sample.count(",") else ","


def _cell(row: Sequence[str], index: int | None) -> object:
    if index is None or index >= len(row):
        return None
    value = row[index].strip()
    return value or None


def parse_csv(content: bytes) -> ParsedImport:
    if not content:
        raise ImportFileError("El archivo está vacío.")

    _ensure_size(content)

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportFileError("El archivo CSV no tiene una codificación UTF-8 válida.") from exc

    if not text.strip():
        raise ImportFileError("El archivo está vacío.")

    reader = csv.reader(io.StringIO(text), delimiter=_detect_delimiter(text))
    header: list[str] | None = None
    header_line = 0

    for row_number, row in enumerate(reader, start=1):
        if any(cell.strip() for cell in row):
            header = row
            header_line = row_number
            break

    if header is None:
        raise ImportFileError("El archivo no contiene una cabecera válida.")

    mapping = map_headers(header)
    if not mapping.is_valid:
        raise ImportFileError(
            "El archivo no tiene las columnas requeridas.",
            mapping.errors,
        )

    rows: list[ParsedRow] = []
    for row_number, row in enumerate(reader, start=header_line + 1):
        parsed = ParsedRow(
            row_number=row_number,
            fecha=_cell(row, mapping.positions.get("fecha")),
            descripcion=_cell(row, mapping.positions.get("descripcion")),
            valor=_cell(row, mapping.positions.get("valor")),
            categoria=_cell(row, mapping.positions.get("categoria")),
        )
        if (
            parsed.fecha is None
            and parsed.descripcion is None
            and parsed.valor is None
            and parsed.categoria is None
        ):
            continue
        rows.append(parsed)
        if len(rows) > MAX_IMPORT_ROWS:
            raise ImportFileError("El archivo supera el máximo de filas permitido.")

    return ParsedImport(headers=mapping.positions, rows=tuple(rows))
