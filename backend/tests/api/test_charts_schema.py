from decimal import Decimal

from app.api.schemas.charts import ExpenseChartMonthRead, ExpenseChartRead
from app.db.models import ExpenseType


def test_expense_chart_serializes_contract_fields():
    chart = ExpenseChartRead(
        anio=2026,
        meses=[
            ExpenseChartMonthRead(
                mes=1,
                gastos_por_tipo={
                    ExpenseType.NECESSARY: Decimal("100.00"),
                    ExpenseType.NON_NECESSARY: Decimal("50.00"),
                    ExpenseType.INVESTMENT: Decimal("20.00"),
                },
            )
        ],
    )

    assert chart.model_dump(mode="json") == {
        "anio": 2026,
        "meses": [
            {
                "mes": 1,
                "gastos_por_tipo": {
                    "NECESARIO": "100.00",
                    "NO_NECESARIO": "50.00",
                    "INVERSION": "20.00",
                },
            }
        ],
    }
