import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.integration


def test_client_uses_test_database(client: TestClient):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_tables_and_migration_are_ready(test_engine: Engine):
    inspector = inspect(test_engine)
    table_names = inspector.get_table_names()

    assert "ingresos" in table_names
    assert "gastos" in table_names
    assert "lotes_importacion" in table_names
    assert "filas_importacion" in table_names
    assert "asignaciones_mensuales" in table_names

    income_columns = {column["name"] for column in inspector.get_columns("ingresos")}
    assert "tipo" in income_columns
    assert "categoria" not in income_columns

    import_columns = {column["name"] for column in inspector.get_columns("filas_importacion")}
    assert "tipo" in import_columns

    income_checks = {
        constraint["name"] for constraint in inspector.get_check_constraints("ingresos")
    }
    import_checks = {
        constraint["name"] for constraint in inspector.get_check_constraints("filas_importacion")
    }
    assert "ck_ingresos_tipo_valido" in income_checks
    assert "ck_filas_importacion_tipo_valido" in import_checks

    with test_engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    assert version == "0008"


def test_income_type_check_constraint(test_engine: Engine):
    with pytest.raises(IntegrityError), test_engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO ingresos (fecha, descripcion, tipo, valor) "
                "VALUES ('2026-01-01', 'Inválido', 'OTRO', 1)"
            )
        )
