from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Expense,
    ImportBatch,
    ImportFileType,
    ImportMovementType,
    ImportRow,
    ImportRowStatus,
    Income,
)
from app.services.imports.csv_parser import parse_csv
from app.services.imports.errors import ImportFileError
from app.services.imports.limits import MAX_IMPORT_BYTES
from app.services.imports.parsed import ParsedImport, ParsedRow
from app.services.imports.validation import ValidatedRow, validate_import_row
from app.services.imports.xlsx_parser import parse_xlsx

ALLOWED_MIME_TYPES = {
    ImportFileType.CSV: {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "text/plain",
        "application/octet-stream",
    },
    ImportFileType.XLSX: {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
}
EXTENSION_TYPES = {
    ".csv": ImportFileType.CSV,
    ".xlsx": ImportFileType.XLSX,
}


def _detect_file_type(filename: str | None, content_type: str | None) -> tuple[str, ImportFileType]:
    name = Path(filename).name.strip() if filename else ""
    if not name:
        raise ImportFileError("El archivo no tiene un nombre válido.")

    file_type = EXTENSION_TYPES.get(Path(name).suffix.lower())
    if file_type is None:
        raise ImportFileError(
            "El archivo debe ser CSV o XLSX.",
            status_code=415,
        )

    if content_type:
        mime = content_type.split(";", 1)[0].strip().lower()
        if mime not in ALLOWED_MIME_TYPES[file_type]:
            raise ImportFileError(
                "El tipo de contenido del archivo no está permitido.",
                status_code=415,
            )

    return name, file_type


def _movement_type(value: str | ImportMovementType) -> ImportMovementType:
    if isinstance(value, ImportMovementType):
        return value
    try:
        return ImportMovementType(value)
    except ValueError as exc:
        raise ImportFileError("El tipo de movimiento no es válido.") from exc


def _parse_content(file_type: ImportFileType, content: bytes) -> ParsedImport:
    if file_type is ImportFileType.CSV:
        return parse_csv(content)
    return parse_xlsx(content)


def _serialize_value(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _raw_data(row: ParsedRow) -> dict[str, object]:
    return {
        "fecha": _serialize_value(row.fecha),
        "descripcion": _serialize_value(row.descripcion),
        "valor": _serialize_value(row.valor),
        "categoria": _serialize_value(row.categoria),
    }


def _row_errors(validated: ValidatedRow) -> list[dict[str, str]]:
    return [{"campo": issue.field, "mensaje": issue.message} for issue in validated.errors]


def _prior_rows(db: Session, fingerprints: set[str]) -> dict[str, ImportRow]:
    if not fingerprints:
        return {}

    rows = db.scalars(
        select(ImportRow)
        .where(
            ImportRow.fingerprint.in_(fingerprints),
            ImportRow.status.in_([ImportRowStatus.PENDING.value, ImportRowStatus.IMPORTED.value]),
        )
        .order_by(ImportRow.id)
    ).all()

    prior: dict[str, ImportRow] = {}
    for row in rows:
        if row.fingerprint is not None:
            prior.setdefault(row.fingerprint, row)
    return prior


def import_file(
    db: Session,
    *,
    filename: str | None,
    content_type: str | None,
    content: bytes,
    movement_type: str | ImportMovementType,
) -> ImportBatch:
    if not content:
        raise ImportFileError("El archivo está vacío.")
    if len(content) > MAX_IMPORT_BYTES:
        raise ImportFileError(
            "El archivo supera el tamaño máximo permitido.",
            status_code=413,
        )

    name, file_type = _detect_file_type(filename, content_type)
    movement = _movement_type(movement_type)
    parsed = _parse_content(file_type, content)

    if not parsed.rows:
        raise ImportFileError("El archivo no contiene filas de datos.")

    validated_rows = [
        (
            parsed_row,
            validate_import_row(
                movement_type=movement,
                fecha=parsed_row.fecha,
                descripcion=parsed_row.descripcion,
                valor=parsed_row.valor,
                categoria=parsed_row.categoria,
            ),
        )
        for parsed_row in parsed.rows
    ]
    fingerprints = {
        validated.fingerprint
        for _, validated in validated_rows
        if validated.fingerprint is not None
    }
    prior_by_fingerprint = _prior_rows(db, fingerprints)

    try:
        batch = ImportBatch(
            file_name=name,
            file_type=file_type.value,
            movement_type=movement.value,
            size_bytes=len(content),
        )
        db.add(batch)
        db.flush()

        rows: list[ImportRow] = []
        importable: list[tuple[ImportRow, ValidatedRow]] = []
        duplicate_targets: list[tuple[ImportRow, ImportRow]] = []
        seen: dict[str, ImportRow] = {}

        for parsed_row, validated in validated_rows:
            errors = _row_errors(validated)
            row = ImportRow(
                batch_id=batch.id,
                row_number=parsed_row.row_number,
                movement_type=movement.value,
                date=validated.date,
                description=validated.description,
                amount=validated.amount,
                category=validated.category,
                expense_type=(
                    validated.expense_type.value if validated.expense_type is not None else None
                ),
                errors=errors,
                raw_data=_raw_data(parsed_row),
                fingerprint=validated.fingerprint,
                status=ImportRowStatus.PENDING.value,
            )

            if validated.is_valid and validated.fingerprint is not None:
                target = seen.get(validated.fingerprint) or prior_by_fingerprint.get(
                    validated.fingerprint
                )
                if target is not None:
                    row.possible_duplicate = True
                    row.errors = [
                        *errors,
                        {
                            "campo": "duplicado",
                            "mensaje": "Posible duplicado; revisa antes de contabilizar.",
                        },
                    ]
                    duplicate_targets.append((row, target))
                else:
                    importable.append((row, validated))
                seen.setdefault(validated.fingerprint, row)

            rows.append(row)

        db.add_all(rows)
        db.flush()

        for row, target in duplicate_targets:
            if target.id is not None:
                row.duplicate_of_id = target.id

        movements: list[tuple[ImportRow, Income | Expense]] = []
        for row, validated in importable:
            if movement is ImportMovementType.INCOME:
                movement_row: Income | Expense = Income(
                    date=validated.date,
                    description=validated.description,
                    category=validated.category,
                    amount=validated.amount,
                )
            else:
                if validated.expense_type is None:
                    raise ImportFileError("El tipo de gasto no es válido.")
                movement_row = Expense(
                    date=validated.date,
                    description=validated.description,
                    expense_type=validated.expense_type.value,
                    amount=validated.amount,
                )
            db.add(movement_row)
            movements.append((row, movement_row))

        db.flush()

        for row, movement_row in movements:
            if isinstance(movement_row, Income):
                row.income_id = movement_row.id
            else:
                row.expense_id = movement_row.id
            row.status = ImportRowStatus.IMPORTED.value

        batch.total_rows = len(rows)
        batch.imported_rows = len(movements)
        batch.pending_rows = len(rows) - len(movements)
        batch.discarded_rows = 0

        db.commit()
        db.refresh(batch)
        return batch
    except Exception:
        db.rollback()
        raise
