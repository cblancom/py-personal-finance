from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.db.models.expense import ExpenseType


class ImportBatchRead(BaseModel):
    id: int
    nombre_archivo: str
    tipo_archivo: str
    tipo_movimiento: str
    tamano_bytes: int
    total_filas: int
    filas_importadas: int
    filas_pendientes: int
    filas_descartadas: int
    created_at: datetime


class ImportRowError(BaseModel):
    campo: str
    mensaje: str


class ImportPendingRowRead(BaseModel):
    id: int
    lote_id: int
    numero_fila: int
    tipo_movimiento: str
    fecha: date | None
    descripcion: str | None
    valor: Decimal | None
    categoria: str | None
    tipo_gasto: ExpenseType | None
    estado: str
    errores: list[ImportRowError]
    posible_duplicado: bool
    duplicado_de_id: int | None


class ImportPendingCountRead(BaseModel):
    pendientes: int


class ImportPendingUpdate(BaseModel):
    fecha: date | None = None
    descripcion: str | None = Field(default=None, max_length=200)
    valor: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    categoria: str | None = Field(default=None, max_length=100)
    tipo_gasto: ExpenseType | None = None
