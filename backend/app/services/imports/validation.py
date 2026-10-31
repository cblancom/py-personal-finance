from dataclasses import dataclass, field
from datetime import date as DateType
from decimal import Decimal

from app.db.models import ExpenseType, ImportMovementType
from app.services.imports.errors import ValidationIssue
from app.services.imports.normalization import (
    build_fingerprint,
    normalize_expense_type,
    normalize_income_category,
    parse_amount,
    parse_date,
)


@dataclass
class ValidatedRow:
    movement_type: str
    date: DateType | None = None
    description: str | None = None
    amount: Decimal | None = None
    category: str | None = None
    expense_type: ExpenseType | None = None
    fingerprint: str | None = None
    errors: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def validate_import_row(
    *,
    movement_type: object,
    fecha: object,
    descripcion: object,
    valor: object,
    categoria: object = None,
    tipo_gasto: ExpenseType | str | None = None,
) -> ValidatedRow:
    movement = (
        movement_type.value
        if isinstance(movement_type, ImportMovementType)
        else _text(movement_type)
    )
    row = ValidatedRow(movement_type=movement)

    if movement not in {
        ImportMovementType.INCOME.value,
        ImportMovementType.EXPENSE.value,
    }:
        row.errors.append(
            ValidationIssue(
                field="tipo_movimiento",
                message="El tipo de movimiento no es válido.",
            )
        )

    if fecha is None or _text(fecha) == "":
        row.errors.append(ValidationIssue(field="fecha", message="La fecha es obligatoria."))
    else:
        try:
            row.date = parse_date(fecha)
        except ValueError as exc:
            row.errors.append(ValidationIssue(field="fecha", message=str(exc)))

    description = _text(descripcion)
    if not description:
        row.errors.append(
            ValidationIssue(
                field="descripcion",
                message="La descripción es obligatoria.",
            )
        )
    elif len(description) > 200:
        row.errors.append(
            ValidationIssue(
                field="descripcion",
                message="La descripción no puede superar los 200 caracteres.",
            )
        )
    else:
        row.description = description

    if valor is None or _text(valor) == "":
        row.errors.append(ValidationIssue(field="valor", message="El valor es obligatorio."))
    else:
        try:
            row.amount = parse_amount(valor)
        except ValueError as exc:
            row.errors.append(ValidationIssue(field="valor", message=str(exc)))

    if movement == ImportMovementType.EXPENSE.value:
        category_text = _text(categoria)
        if tipo_gasto is not None:
            try:
                row.expense_type = (
                    tipo_gasto if isinstance(tipo_gasto, ExpenseType) else ExpenseType(tipo_gasto)
                )
            except ValueError:
                row.errors.append(
                    ValidationIssue(
                        field="tipo_gasto",
                        message="El tipo de gasto no es válido.",
                    )
                )
            else:
                row.category = category_text or None
        elif not category_text:
            row.errors.append(
                ValidationIssue(
                    field="tipo_gasto",
                    message="El tipo de gasto es obligatorio.",
                )
            )
        else:
            expense_type = normalize_expense_type(category_text)
            if expense_type is None:
                row.errors.append(
                    ValidationIssue(
                        field="tipo_gasto",
                        message="El tipo de gasto no es válido.",
                    )
                )
            else:
                row.category = category_text
                row.expense_type = expense_type
    elif movement == ImportMovementType.INCOME.value:
        try:
            row.category = normalize_income_category(categoria)
        except ValueError as exc:
            row.errors.append(ValidationIssue(field="categoria", message=str(exc)))

    if (
        row.is_valid
        and row.date is not None
        and row.description is not None
        and row.amount is not None
    ):
        row.fingerprint = build_fingerprint(
            movement_type=row.movement_type,
            fecha=row.date,
            descripcion=row.description,
            valor=row.amount,
            categoria=row.category,
            tipo_gasto=row.expense_type.value if row.expense_type else None,
        )

    return row
