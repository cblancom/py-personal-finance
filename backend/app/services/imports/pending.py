from typing import cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Expense,
    ExpenseType,
    ImportBatch,
    ImportMovementType,
    ImportRow,
    ImportRowStatus,
    Income,
)
from app.services.imports.errors import (
    PendingRowConflict,
    PendingRowInvalid,
    PendingRowNotFound,
    ValidationIssue,
)
from app.services.imports.validation import validate_import_row


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _errors(issues: tuple[ValidationIssue, ...] | list[ValidationIssue]) -> list[dict[str, str]]:
    return [{"campo": issue.field, "mensaje": issue.message} for issue in issues]


def _get_pending(db: Session, pending_id: int) -> ImportRow:
    row = db.scalar(select(ImportRow).where(ImportRow.id == pending_id).with_for_update())
    if row is None:
        raise PendingRowNotFound("Pendiente no encontrado.")
    if row.status != ImportRowStatus.PENDING.value:
        raise PendingRowConflict("El pendiente ya fue contabilizado o descartado.")
    return row


def _refresh_batch_counts(db: Session, batch_id: int) -> None:
    counts = dict(
        db.execute(
            select(ImportRow.status, func.count())
            .where(ImportRow.batch_id == batch_id)
            .group_by(ImportRow.status)
        ).all()
    )
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        return
    batch.imported_rows = counts.get(ImportRowStatus.IMPORTED.value, 0)
    batch.pending_rows = counts.get(ImportRowStatus.PENDING.value, 0)
    batch.discarded_rows = counts.get(ImportRowStatus.DISCARDED.value, 0)


def list_pending(db: Session) -> list[ImportRow]:
    return list(
        db.scalars(
            select(ImportRow)
            .where(ImportRow.status == ImportRowStatus.PENDING.value)
            .order_by(ImportRow.batch_id, ImportRow.row_number)
        ).all()
    )


def count_pending(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(ImportRow)
            .where(ImportRow.status == ImportRowStatus.PENDING.value)
        )
        or 0
    )


def update_pending(
    db: Session,
    pending_id: int,
    changes: dict[str, object],
) -> ImportRow:
    row = _get_pending(db, pending_id)
    old_fingerprint = row.fingerprint

    category = _text(changes["categoria"]) if "categoria" in changes else row.category

    if "tipo_gasto" in changes:
        expense_type = changes["tipo_gasto"]
    elif "categoria" in changes:
        expense_type = None
    else:
        expense_type = row.expense_type

    expense_type = cast(ExpenseType | str | None, expense_type)

    validated = validate_import_row(
        movement_type=row.movement_type,
        fecha=changes.get("fecha", row.date),
        descripcion=changes.get("descripcion", row.description),
        valor=changes.get("valor", row.amount),
        categoria=category,
        tipo_gasto=expense_type,
    )

    row.date = validated.date
    row.description = validated.description
    row.amount = validated.amount
    row.category = validated.category
    row.expense_type = validated.expense_type.value if validated.expense_type is not None else None
    row.errors = _errors(validated.errors)
    row.fingerprint = validated.fingerprint

    if row.fingerprint != old_fingerprint:
        row.possible_duplicate = False
        row.duplicate_of_id = None

    try:
        db.commit()
        db.refresh(row)
        return row
    except Exception:
        db.rollback()
        raise


def commit_pending(db: Session, pending_id: int) -> ImportRow:
    row = _get_pending(db, pending_id)
    validated = validate_import_row(
        movement_type=row.movement_type,
        fecha=row.date,
        descripcion=row.description,
        valor=row.amount,
        categoria=row.category,
        tipo_gasto=row.expense_type,
    )

    if not validated.is_valid:
        row.errors = _errors(validated.errors)
        db.commit()
        raise PendingRowInvalid(tuple(validated.errors))

    if row.movement_type == ImportMovementType.INCOME.value:
        movement: Income | Expense = Income(
            date=validated.date,
            description=validated.description,
            category=validated.category,
            amount=validated.amount,
        )
    else:
        if validated.expense_type is None:
            raise PendingRowInvalid(
                (
                    ValidationIssue(
                        field="tipo_gasto",
                        message="El tipo de gasto es obligatorio.",
                    ),
                )
            )
        movement = Expense(
            date=validated.date,
            description=validated.description,
            expense_type=validated.expense_type.value,
            amount=validated.amount,
        )

    try:
        db.add(movement)
        db.flush()
        if isinstance(movement, Income):
            row.income_id = movement.id
        else:
            row.expense_id = movement.id
        row.status = ImportRowStatus.IMPORTED.value
        row.errors = []
        db.flush()
        _refresh_batch_counts(db, row.batch_id)
        db.commit()
        db.refresh(row)
        return row
    except Exception:
        db.rollback()
        raise


def discard_pending(db: Session, pending_id: int) -> None:
    row = _get_pending(db, pending_id)
    try:
        row.status = ImportRowStatus.DISCARDED.value
        db.flush()
        _refresh_batch_counts(db, row.batch_id)
        db.commit()
    except Exception:
        db.rollback()
        raise
