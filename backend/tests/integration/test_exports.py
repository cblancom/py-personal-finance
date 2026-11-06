import csv
from io import BytesIO, StringIO

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

pytestmark = pytest.mark.integration


def create_income(
    client: TestClient,
    *,
    fecha: str,
    descripcion: str,
    valor: str,
    tipo: str | None = None,
) -> None:
    response = client.post(
        "/api/ingresos",
        json={
            "fecha": fecha,
            "descripcion": descripcion,
            "tipo": tipo,
            "valor": valor,
        },
    )
    assert response.status_code == 201


def create_expense(
    client: TestClient,
    *,
    fecha: str,
    descripcion: str,
    valor: str,
    tipo: str,
) -> None:
    response = client.post(
        "/api/gastos",
        json={
            "fecha": fecha,
            "descripcion": descripcion,
            "tipo": tipo,
            "valor": valor,
        },
    )
    assert response.status_code == 201


def csv_rows(content: bytes) -> list[list[str]]:
    return list(csv.reader(StringIO(content.decode("utf-8-sig"))))


def xlsx_rows(content: bytes) -> tuple[str, list[tuple[object, ...]]]:
    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    try:
        worksheet = workbook.worksheets[0]
        return worksheet.title, list(worksheet.iter_rows(values_only=True))
    finally:
        workbook.close()


def test_export_incomes_csv_is_downloadable_and_ordered(client: TestClient):
    create_income(
        client,
        fecha="2026-10-22",
        descripcion="Consultoría",
        valor="800.00",
        tipo="NO_NECESARIO",
    )
    create_income(
        client,
        fecha="2026-10-21",
        descripcion="Salario",
        valor="1500.50",
    )

    response = client.get("/api/exportaciones/ingresos?formato=csv")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["content-disposition"].startswith('attachment; filename="ingresos_')
    assert response.headers["content-disposition"].endswith('.csv"')
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert csv_rows(response.content) == [
        ["Fecha", "Descripcion", "Valor", "Categoria"],
        ["2026-10-21", "Salario", "1500.50", ""],
        ["2026-10-22", "Consultoría", "800.00", "NO_NECESARIO"],
    ]


def test_export_incomes_xlsx_is_downloadable(client: TestClient):
    create_income(
        client,
        fecha="2026-10-21",
        descripcion="Salario",
        valor="1500.50",
        tipo="NECESARIO",
    )

    response = client.get("/api/exportaciones/ingresos?formato=xlsx")

    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"].startswith('attachment; filename="ingresos_')
    assert response.headers["content-disposition"].endswith('.xlsx"')
    assert xlsx_rows(response.content) == (
        "Ingresos",
        [
            ("Fecha", "Descripcion", "Valor", "Categoria"),
            ("2026-10-21", "Salario", "1500.50", "NECESARIO"),
        ],
    )


def test_export_expenses_csv_and_xlsx_use_tipo_de_gasto(client: TestClient):
    create_expense(
        client,
        fecha="2026-10-21",
        descripcion="Mercado",
        valor="120.50",
        tipo="NECESARIO",
    )

    csv_response = client.get("/api/exportaciones/gastos?formato=csv")
    xlsx_response = client.get("/api/exportaciones/gastos?formato=xlsx")

    assert csv_response.status_code == 200
    assert csv_rows(csv_response.content) == [
        ["Fecha", "Descripcion", "Valor", "Tipo de gasto"],
        ["2026-10-21", "Mercado", "120.50", "NECESARIO"],
    ]
    assert xlsx_response.status_code == 200
    assert xlsx_rows(xlsx_response.content) == (
        "Gastos",
        [
            ("Fecha", "Descripcion", "Valor", "Tipo de gasto"),
            ("2026-10-21", "Mercado", "120.50", "NECESARIO"),
        ],
    )


def test_empty_exports_contain_only_headers(client: TestClient):
    incomes_csv = client.get("/api/exportaciones/ingresos?formato=csv")
    expenses_xlsx = client.get("/api/exportaciones/gastos?formato=xlsx")

    assert csv_rows(incomes_csv.content) == [["Fecha", "Descripcion", "Valor", "Categoria"]]
    assert xlsx_rows(expenses_xlsx.content) == (
        "Gastos",
        [("Fecha", "Descripcion", "Valor", "Tipo de gasto")],
    )


@pytest.mark.parametrize("formato", ["json", "CSV", ""])
def test_export_rejects_invalid_format(client: TestClient, formato: str):
    response = client.get(f"/api/exportaciones/ingresos?formato={formato}")

    assert response.status_code == 422


def import_exported(
    client: TestClient,
    *,
    content: bytes,
    filename: str,
    content_type: str,
    movement_type: str,
):
    response = client.post(
        "/api/importaciones",
        files={"archivo": (filename, content, content_type)},
        data={"tipo_movimiento": movement_type},
    )
    assert response.status_code == 201
    return response.json()


def delete_all_incomes(client: TestClient) -> None:
    for income in client.get("/api/ingresos").json():
        assert client.delete(f"/api/ingresos/{income['id']}").status_code == 204


def delete_all_expenses(client: TestClient) -> None:
    for expense in client.get("/api/gastos").json():
        assert client.delete(f"/api/gastos/{expense['id']}").status_code == 204


def income_signature(client: TestClient) -> set[tuple[str, str, str | None, str]]:
    return {
        (income["fecha"], income["descripcion"], income["tipo"], income["valor"])
        for income in client.get("/api/ingresos").json()
    }


def expense_signature(client: TestClient) -> set[tuple[str, str, str, str]]:
    return {
        (expense["fecha"], expense["descripcion"], expense["tipo"], expense["valor"])
        for expense in client.get("/api/gastos").json()
    }


@pytest.mark.parametrize(
    ("formato", "filename", "content_type"),
    [
        ("csv", "ingresos.csv", "text/csv"),
        (
            "xlsx",
            "ingresos.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    ],
)
def test_income_export_round_trip_preserves_movements(
    client: TestClient,
    formato: str,
    filename: str,
    content_type: str,
):
    create_income(
        client,
        fecha="2026-10-21",
        descripcion='Salario, "octubre"\nquincena',
        valor="1500.50",
        tipo="NO_NECESARIO",
    )
    create_income(
        client,
        fecha="2026-10-22",
        descripcion="Consultoría",
        valor="800.00",
    )
    exported = client.get(f"/api/exportaciones/ingresos?formato={formato}")
    original = income_signature(client)

    delete_all_incomes(client)
    batch = import_exported(
        client,
        content=exported.content,
        filename=filename,
        content_type=content_type,
        movement_type="INGRESO",
    )

    assert batch["filas_importadas"] == 2
    assert batch["filas_pendientes"] == 0
    assert income_signature(client) == original


@pytest.mark.parametrize(
    ("formato", "filename", "content_type"),
    [
        ("csv", "gastos.csv", "text/csv"),
        (
            "xlsx",
            "gastos.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    ],
)
def test_expense_export_round_trip_preserves_movements(
    client: TestClient,
    formato: str,
    filename: str,
    content_type: str,
):
    create_expense(
        client,
        fecha="2026-10-21",
        descripcion='Mercado, "semanal"\ncon frutas',
        valor="120.50",
        tipo="NECESARIO",
    )
    create_expense(
        client,
        fecha="2026-10-22",
        descripcion="Fondo indexado",
        valor="200.00",
        tipo="INVERSION",
    )
    exported = client.get(f"/api/exportaciones/gastos?formato={formato}")
    original = expense_signature(client)

    delete_all_expenses(client)
    batch = import_exported(
        client,
        content=exported.content,
        filename=filename,
        content_type=content_type,
        movement_type="GASTO",
    )

    assert batch["filas_importadas"] == 2
    assert batch["filas_pendientes"] == 0
    assert expense_signature(client) == original
