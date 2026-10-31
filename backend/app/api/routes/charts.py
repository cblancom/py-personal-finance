from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas.charts import ExpenseChartMonthRead, ExpenseChartRead
from app.db.session import get_db
from app.services.charts import get_monthly_expense_series

router = APIRouter(prefix="/graficos", tags=["graficos"])


@router.get("/gastos-mensuales", response_model=ExpenseChartRead)
def get_monthly_expense_chart(
    db: Annotated[Session, Depends(get_db)],
    anio: Annotated[int | None, Query(ge=1900, le=2100)] = None,
) -> ExpenseChartRead:
    target_year = anio or date.today().year
    series = get_monthly_expense_series(db, target_year)
    return ExpenseChartRead(
        anio=series.year,
        meses=[
            ExpenseChartMonthRead(
                mes=point.month,
                gastos_por_tipo=point.expenses_by_type,
            )
            for point in series.months
        ],
    )
