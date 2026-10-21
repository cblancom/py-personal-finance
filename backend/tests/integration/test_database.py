import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, inspect, text

pytestmark = pytest.mark.integration


def test_client_uses_test_database(client: TestClient):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_tables_and_migration_are_ready(test_engine: Engine):
    table_names = inspect(test_engine).get_table_names()

    assert "ingresos" in table_names
    assert "gastos" in table_names

    with test_engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    assert version == "0003"
