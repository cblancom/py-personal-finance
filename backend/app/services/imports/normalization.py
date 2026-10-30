import hashlib
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.db.models import ExpenseType
from app.services.imports.errors import ValidationIssue

HEADER_ALIASES = {
    "fecha": "fecha",
    "date": "fecha",
    "descripcion": "descripcion",
    "detalle": "descripcion",
    "valor": "valor",
    "monto": "valor",
    "importe": "valor",
    "categoria": "categoria",
    "tipo": "categoria",
}
REQUIRED_HEADERS = ("fecha", "descripcion", "valor")
EXPENSE_TYPE_ALIASES = {
    "necesario": ExpenseType.NECESSARY,
    "no necesario": ExpenseType.NON_NECESSARY,
    "inversion": ExpenseType.INVESTMENT,
}


@dataclass(frozen=True)
class HeaderMapping:
    positions: Mapping[str, int]
    errors: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def normalize_key(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.casefold().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_header(value: object) -> str:
    return normalize_key(value)


def canonical_header(value: object) -> str | None:
    return HEADER_ALIASES.get(normalize_header(value))


def map_headers(headers: Sequence[object]) -> HeaderMapping:
    positions: dict[str, int] = {}
    errors: list[ValidationIssue] = []

    for index, header in enumerate(headers):
        if header is None:
            continue

        canonical = canonical_header(header)
        if canonical is None:
            continue
        if canonical in positions:
            errors.append(
                ValidationIssue(
                    field="cabecera",
                    message=f"La columna '{canonical}' está duplicada.",
                )
            )
            continue
        positions[canonical] = index

    for required in REQUIRED_HEADERS:
        if required not in positions:
            errors.append(
                ValidationIssue(
                    field="cabecera",
                    message=f"Falta la columna obligatoria '{required}'.",
                )
            )

    return HeaderMapping(positions=positions, errors=tuple(errors))


def normalize_expense_type(value: object) -> ExpenseType | None:
    return EXPENSE_TYPE_ALIASES.get(normalize_key(value))


def normalize_income_category(value: object) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None
    if len(text) > 100:
        raise ValueError("La categoría no puede superar los 100 caracteres.")
    return text


def parse_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise ValueError("La fecha no es válida.")

    text = value.strip()
    if not text:
        raise ValueError("La fecha es obligatoria.")

    for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue

    raise ValueError("La fecha no es válida.")


def parse_amount(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("El valor no es válido.")

    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, (int, float)):
        amount = Decimal(str(value))
    elif isinstance(value, str):
        text = re.sub(r"\s+", "", value.strip())
        if not text:
            raise ValueError("El valor es obligatorio.")
        if not re.fullmatch(r"[+-]?[\d.,]+", text):
            raise ValueError("El valor no es válido.")

        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        elif "," in text:
            if text.count(",") > 1:
                raise ValueError("El valor no es válido.")
            text = text.replace(",", ".")
        elif text.count(".") > 1:
            raise ValueError("El valor no es válido.")

        try:
            amount = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError("El valor no es válido.") from exc
    else:
        raise ValueError("El valor no es válido.")

    if not amount.is_finite():
        raise ValueError("El valor no es válido.")
    if amount <= 0:
        raise ValueError("El valor debe ser mayor que 0.")

    exponent = amount.as_tuple().exponent
    if isinstance(exponent, int) and max(0, -exponent) > 2:
        raise ValueError("El valor admite como máximo 2 decimales.")
    if len(amount.as_tuple().digits) > 12:
        raise ValueError("El valor admite como máximo 12 dígitos.")

    return amount.quantize(Decimal("0.01"))


def build_fingerprint(
    *,
    movement_type: str,
    fecha: date,
    descripcion: str,
    valor: Decimal,
    categoria: str | None = None,
    tipo_gasto: str | None = None,
) -> str:
    category_key = tipo_gasto or normalize_key(categoria or "")
    canonical = "|".join(
        (
            movement_type,
            fecha.isoformat(),
            normalize_key(descripcion),
            f"{valor.quantize(Decimal('0.01')):.2f}",
            category_key,
        )
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
