from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.schemas.imports import (
    ImportBatchRead,
    ImportPendingCountRead,
    ImportPendingDiscardRead,
    ImportPendingRowRead,
    ImportPendingUpdate,
    ImportRowError,
)
from app.db.models import ExpenseType, ImportBatch, ImportRow
from app.db.session import get_db
from app.services.imports.errors import (
    ImportFileError,
    PendingRowConflict,
    PendingRowInvalid,
    PendingRowNotFound,
)
from app.services.imports.importer import import_file
from app.services.imports.limits import MAX_IMPORT_BYTES
from app.services.imports.pending import (
    commit_pending,
    count_pending,
    discard_all_pending,
    discard_pending,
    list_pending,
    update_pending,
)

router = APIRouter(prefix="/importaciones", tags=["importaciones"])


def _batch_read(batch: ImportBatch) -> ImportBatchRead:
    return ImportBatchRead(
        id=batch.id,
        nombre_archivo=batch.file_name,
        tipo_archivo=batch.file_type,
        tipo_movimiento=batch.movement_type,
        tamano_bytes=batch.size_bytes,
        total_filas=batch.total_rows,
        filas_importadas=batch.imported_rows,
        filas_pendientes=batch.pending_rows,
        filas_descartadas=batch.discarded_rows,
        created_at=batch.created_at,
    )


@router.post(
    "",
    response_model=ImportBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_import(
    archivo: Annotated[UploadFile, File()],
    tipo_movimiento: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
) -> ImportBatchRead:
    content = await archivo.read(MAX_IMPORT_BYTES + 1)

    try:
        batch = import_file(
            db,
            filename=archivo.filename,
            content_type=archivo.content_type,
            content=content,
            movement_type=tipo_movimiento,
        )
    except ImportFileError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return _batch_read(batch)


def _pending_read(row: ImportRow) -> ImportPendingRowRead:
    return ImportPendingRowRead(
        id=row.id,
        lote_id=row.batch_id,
        numero_fila=row.row_number,
        tipo_movimiento=row.movement_type,
        fecha=row.date,
        descripcion=row.description,
        valor=row.amount,
        categoria=row.category,
        tipo_gasto=ExpenseType(row.expense_type) if row.expense_type else None,
        estado=row.status,
        errores=[ImportRowError.model_validate(error) for error in row.errors],
        posible_duplicado=row.possible_duplicate,
        duplicado_de_id=row.duplicate_of_id,
    )


def _pending_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PendingRowNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PendingRowConflict):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, PendingRowInvalid):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "mensaje": str(exc),
                "errores": [
                    {"campo": issue.field, "mensaje": issue.message} for issue in exc.issues
                ],
            },
        )
    raise exc


@router.get("/pendientes", response_model=list[ImportPendingRowRead])
def get_pending_rows(db: Annotated[Session, Depends(get_db)]) -> list[ImportPendingRowRead]:
    return [_pending_read(row) for row in list_pending(db)]


@router.get("/pendientes/count", response_model=ImportPendingCountRead)
def get_pending_count(db: Annotated[Session, Depends(get_db)]) -> ImportPendingCountRead:
    return ImportPendingCountRead(pendientes=count_pending(db))


@router.delete("/pendientes", response_model=ImportPendingDiscardRead)
def discard_all_pending_rows(
    db: Annotated[Session, Depends(get_db)],
) -> ImportPendingDiscardRead:
    return ImportPendingDiscardRead(descartados=discard_all_pending(db))


@router.put("/pendientes/{pending_id}", response_model=ImportPendingRowRead)
def update_pending_row(
    pending_id: int,
    payload: ImportPendingUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> ImportPendingRowRead:
    changes = payload.model_dump(exclude_unset=True)
    try:
        row = update_pending(db, pending_id, changes)
    except (PendingRowNotFound, PendingRowConflict) as exc:
        raise _pending_error(exc) from exc
    return _pending_read(row)


@router.post(
    "/pendientes/{pending_id}/contabilizar",
    response_model=ImportPendingRowRead,
)
def commit_pending_row(
    pending_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ImportPendingRowRead:
    try:
        row = commit_pending(db, pending_id)
    except (PendingRowNotFound, PendingRowConflict, PendingRowInvalid) as exc:
        raise _pending_error(exc) from exc
    return _pending_read(row)


@router.delete("/pendientes/{pending_id}", status_code=status.HTTP_204_NO_CONTENT)
def discard_pending_row(
    pending_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        discard_pending(db, pending_id)
    except (PendingRowNotFound, PendingRowConflict) as exc:
        raise _pending_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
