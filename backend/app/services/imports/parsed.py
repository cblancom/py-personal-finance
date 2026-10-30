from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedRow:
    row_number: int
    fecha: object
    descripcion: object
    valor: object
    categoria: object


@dataclass(frozen=True)
class ParsedImport:
    headers: Mapping[str, int]
    rows: tuple[ParsedRow, ...]
