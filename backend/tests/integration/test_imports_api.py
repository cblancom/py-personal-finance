from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import ImportRow, ImportRowStatus

pytestmark = pytest.mark.integration

HEADER = "Fecha,Descripcion,Valor,Categoria\n"


def post_csv(
    client: TestClient,
    content: str,
    movement_type: str = "INGRESO",
    filename: str = "movimientos.csv",
    content_type: str = "text/csv",
):
    return client.post(
        "/api/importaciones",
        files={"archivo": (filename, content.encode("utf-8"), content_type)},
        data={"tipo_movimiento": movement_type},
    )


def build_xlsx() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["Fecha", "Descripción", "Valor", "Categoría"])
    worksheet.append(["2026-10-21", "Salario", 1500.5, None])
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


def test_import_csv_income(client: TestClient):
    response = post_csv(
        client,
        HEADER + "2026-10-21,Salario,1500.50,Nómina\n",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nombre_archivo"] == "movimientos.csv"
    assert body["tipo_archivo"] == "CSV"
    assert body["tipo_movimiento"] == "INGRESO"
    assert body["total_filas"] == 1
    assert body["filas_importadas"] == 1
    assert body["filas_pendientes"] == 0

    incomes = client.get("/api/ingresos").json()
    assert incomes == [
        {
            "id": 1,
            "fecha": "2026-10-21",
            "descripcion": "Salario",
            "categoria": "Nómina",
            "valor": "1500.50",
        }
    ]
    assert client.get("/api/resumen").json()["total_ingresos"] == "1500.50"


def test_import_csv_expense_with_pending_row(
    client: TestClient,
    test_session_factory: sessionmaker[Session],
):
    content = HEADER + "2026-10-21,Mercado,120.50,No Necesario\n" + "2026-10-22,Cine,45.00,\n"
    response = post_csv(client, content, movement_type="GASTO")

    assert response.status_code == 201
    assert response.json()["filas_importadas"] == 1
    assert response.json()["filas_pendientes"] == 1

    assert client.get("/api/gastos").json()[0]["tipo"] == "NO_NECESARIO"
    assert client.get("/api/resumen").json()["total_gastos"] == "120.50"

    with test_session_factory() as session:
        rows = session.scalars(select(ImportRow).order_by(ImportRow.row_number)).all()
        assert [row.status for row in rows] == [
            ImportRowStatus.IMPORTED.value,
            ImportRowStatus.PENDING.value,
        ]
        assert rows[1].errors[0]["campo"] == "categoria"


def test_import_xlsx_income(client: TestClient):
    response = client.post(
        "/api/importaciones",
        files={
            "archivo": (
                "movimientos.xlsx",
                build_xlsx(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"tipo_movimiento": "INGRESO"},
    )

    assert response.status_code == 201
    assert response.json()["tipo_archivo"] == "XLSX"
    assert response.json()["filas_importadas"] == 1
    assert client.get("/api/ingresos").json()[0]["valor"] == "1500.50"


def test_duplicate_import_is_left_pending(
    client: TestClient,
    test_session_factory: sessionmaker[Session],
):
    content = HEADER + "2026-10-21,Salario,1500.50,Nómina\n"

    assert post_csv(client, content).status_code == 201
    second = post_csv(client, content)

    assert second.status_code == 201
    assert second.json()["filas_importadas"] == 0
    assert second.json()["filas_pendientes"] == 1
    assert client.get("/api/resumen").json()["total_ingresos"] == "1500.50"

    with test_session_factory() as session:
        duplicate = session.scalars(
            select(ImportRow)
            .where(ImportRow.possible_duplicate.is_(True))
            .order_by(ImportRow.id.desc())
        ).first()
        assert duplicate is not None
        assert duplicate.status == ImportRowStatus.PENDING.value
        assert duplicate.duplicate_of_id is not None
        assert duplicate.errors[0]["campo"] == "duplicado"


def test_import_rejects_invalid_extension(client: TestClient):
    response = post_csv(
        client,
        HEADER,
        filename="movimientos.txt",
        content_type="text/plain",
    )

    assert response.status_code == 415


def test_import_rejects_missing_headers(client: TestClient):
    response = post_csv(client, "Fecha,Descripcion\n2026-10-21,Salario\n")

    assert response.status_code == 422
    assert "columnas requeridas" in response.json()["detail"]


def test_import_rejects_empty_file(client: TestClient):
    response = post_csv(client, "")

    assert response.status_code == 422


def test_import_rejects_invalid_movement_type(client: TestClient):
    response = post_csv(
        client,
        HEADER + "2026-10-21,Salario,1500.50,Nómina\n",
        movement_type="OTRO",
    )

    assert response.status_code == 422
    assert "tipo de movimiento" in response.json()["detail"]


def test_import_creates_batch(client: TestClient):
    response = post_csv(client, HEADER + "2026-10-21,Salario,100.00,\n")

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["filas_descartadas"] == 0
    assert body["created_at"]


def create_pending_expense(client: TestClient):
    content = HEADER + "2026-10-21,Mercado,120.50,\n"
    response = post_csv(client, content, movement_type="GASTO")
    assert response.status_code == 201
    pending = client.get("/api/importaciones/pendientes").json()
    assert len(pending) == 1
    return pending[0]


def test_list_pending_rows_and_count(client: TestClient):
    pending = create_pending_expense(client)

    assert pending["lote_id"] == 1
    assert pending["numero_fila"] == 2
    assert pending["tipo_movimiento"] == "GASTO"
    assert pending["estado"] == "PENDIENTE"
    assert pending["errores"][0]["campo"] == "categoria"
    assert client.get("/api/importaciones/pendientes/count").json() == {"pendientes": 1}


def test_update_and_commit_pending_row(client: TestClient):
    pending = create_pending_expense(client)

    updated = client.put(
        f"/api/importaciones/pendientes/{pending['id']}",
        json={"categoria": "No Necesario"},
    )

    assert updated.status_code == 200
    assert updated.json()["estado"] == "PENDIENTE"
    assert updated.json()["tipo_gasto"] == "NO_NECESARIO"
    assert updated.json()["errores"] == []

    committed = client.post(f"/api/importaciones/pendientes/{pending['id']}/contabilizar")

    assert committed.status_code == 200
    assert committed.json()["estado"] == "IMPORTADO"
    assert client.get("/api/importaciones/pendientes/count").json() == {"pendientes": 0}
    assert client.get("/api/gastos").json()[0]["tipo"] == "NO_NECESARIO"
    assert client.get("/api/resumen").json()["total_gastos"] == "120.50"


def test_update_pending_can_set_type_without_category(client: TestClient):
    pending = create_pending_expense(client)

    updated = client.put(
        f"/api/importaciones/pendientes/{pending['id']}",
        json={"tipo_gasto": "NECESARIO"},
    )

    assert updated.status_code == 200
    assert updated.json()["categoria"] is None
    assert updated.json()["tipo_gasto"] == "NECESARIO"
    assert updated.json()["errores"] == []

    committed = client.post(f"/api/importaciones/pendientes/{pending['id']}/contabilizar")
    assert committed.status_code == 200
    assert client.get("/api/gastos").json()[0]["tipo"] == "NECESARIO"


def test_commit_invalid_pending_returns_422(client: TestClient):
    pending = create_pending_expense(client)

    response = client.post(f"/api/importaciones/pendientes/{pending['id']}/contabilizar")

    assert response.status_code == 422
    assert response.json()["detail"]["errores"][0]["campo"] == "categoria"
    assert client.get("/api/importaciones/pendientes/count").json() == {"pendientes": 1}


def test_discard_pending_row(client: TestClient):
    pending = create_pending_expense(client)

    response = client.delete(f"/api/importaciones/pendientes/{pending['id']}")

    assert response.status_code == 204
    assert client.get("/api/importaciones/pendientes/count").json() == {"pendientes": 0}
    assert client.get("/api/gastos").json() == []
    assert client.get("/api/resumen").json()["total_gastos"] == "0.00"


def test_committed_pending_cannot_be_committed_again(client: TestClient):
    pending = create_pending_expense(client)

    assert (
        client.put(
            f"/api/importaciones/pendientes/{pending['id']}",
            json={"categoria": "Necesario"},
        ).status_code
        == 200
    )
    assert (
        client.post(f"/api/importaciones/pendientes/{pending['id']}/contabilizar").status_code
        == 200
    )
    assert (
        client.post(f"/api/importaciones/pendientes/{pending['id']}/contabilizar").status_code
        == 409
    )


def test_pending_not_found(client: TestClient):
    assert (
        client.put(
            "/api/importaciones/pendientes/999",
            json={"descripcion": "Otro"},
        ).status_code
        == 404
    )
    assert client.delete("/api/importaciones/pendientes/999").status_code == 404
    assert client.post("/api/importaciones/pendientes/999/contabilizar").status_code == 404
