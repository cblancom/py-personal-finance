from decimal import Decimal

from app.api.schemas.summary import SummaryResponse
from app.db.models.expense import ExpenseType


def test_summary_serializes_contract_fields():
    summary = SummaryResponse(
        total_ingresos=Decimal("5000.00"),
        total_gastos=Decimal("1500.50"),
        balance=Decimal("3499.50"),
        gastos_por_tipo={
            ExpenseType.NECESSARY: Decimal("1000.00"),
            ExpenseType.NON_NECESSARY: Decimal("300.50"),
            ExpenseType.INVESTMENT: Decimal("200.00"),
        },
    )

    assert summary.model_dump(mode="json") == {
        "total_ingresos": "5000.00",
        "total_gastos": "1500.50",
        "balance": "3499.50",
        "gastos_por_tipo": {
            "NECESARIO": "1000.00",
            "NO_NECESARIO": "300.50",
            "INVERSION": "200.00",
        },
    }


def test_summary_serializes_negative_balance():
    summary = SummaryResponse(
        total_ingresos=Decimal("100.00"),
        total_gastos=Decimal("250.00"),
        balance=Decimal("-150.00"),
        gastos_por_tipo={
            ExpenseType.NECESSARY: Decimal("0.00"),
            ExpenseType.NON_NECESSARY: Decimal("0.00"),
            ExpenseType.INVESTMENT: Decimal("0.00"),
        },
    )

    assert summary.model_dump(mode="json")["balance"] == "-150.00"


def test_summary_serializes_empty_totals():
    summary = SummaryResponse(
        total_ingresos=Decimal("0.00"),
        total_gastos=Decimal("0.00"),
        balance=Decimal("0.00"),
        gastos_por_tipo={
            ExpenseType.NECESSARY: Decimal("0.00"),
            ExpenseType.NON_NECESSARY: Decimal("0.00"),
            ExpenseType.INVESTMENT: Decimal("0.00"),
        },
    )

    assert summary.model_dump(mode="json") == {
        "total_ingresos": "0.00",
        "total_gastos": "0.00",
        "balance": "0.00",
        "gastos_por_tipo": {
            "NECESARIO": "0.00",
            "NO_NECESARIO": "0.00",
            "INVERSION": "0.00",
        },
    }
