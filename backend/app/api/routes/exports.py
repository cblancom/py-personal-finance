from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Expense, Income
from app.db.session import get_db
from app.services.exports import (
    export_expenses_csv,
    export_expenses_xlsx,
    export_incomes_csv,
    export_incomes_xlsx,
)

ExportFormat = Literal["csv", "xlsx"]

CSV_MEDIA_TYPE = "text/csv; charset=utf-8"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

router = APIRouter(prefix="/exportaciones", tags=["exportaciones"])


def _download_response(content: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _filename(resource: str, formato: ExportFormat) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{resource}_{timestamp}.{formato}"


@router.get("/ingresos")
def export_incomes(
    formato: Annotated[ExportFormat, Query(description="Formato de exportación")],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    incomes = db.scalars(select(Income).order_by(Income.date, Income.id)).all()
    if formato == "csv":
        content = export_incomes_csv(incomes)
        media_type = CSV_MEDIA_TYPE
    else:
        content = export_incomes_xlsx(incomes)
        media_type = XLSX_MEDIA_TYPE
    return _download_response(content, _filename("ingresos", formato), media_type)


@router.get("/gastos")
def export_expenses(
    formato: Annotated[ExportFormat, Query(description="Formato de exportación")],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    expenses = db.scalars(select(Expense).order_by(Expense.date, Expense.id)).all()
    if formato == "csv":
        content = export_expenses_csv(expenses)
        media_type = CSV_MEDIA_TYPE
    else:
        content = export_expenses_xlsx(expenses)
        media_type = XLSX_MEDIA_TYPE
    return _download_response(content, _filename("gastos", formato), media_type)
