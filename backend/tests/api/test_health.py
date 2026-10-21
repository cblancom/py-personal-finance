import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.main import app


class HealthySession:
    def execute(self, statement):
        return None


class UnhealthySession:
    def execute(self, statement):
        raise SQLAlchemyError("connection refused")


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def test_health_returns_ok(client):
    app.dependency_overrides[get_db] = HealthySession

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_degraded_when_database_fails(client):
    app.dependency_overrides[get_db] = UnhealthySession

    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_health_does_not_leak_database_details(client, caplog):
    class LeakySession:
        def execute(self, statement):
            raise SQLAlchemyError("postgresql://user:super-secret@db:5432/finance")

    app.dependency_overrides[get_db] = LeakySession

    with caplog.at_level(logging.WARNING):
        response = client.get("/api/health")

    assert response.status_code == 503
    assert "super-secret" not in response.text
    assert "super-secret" not in caplog.text


def test_health_is_documented_in_openapi():
    schema = app.openapi()

    assert "/api/health" in schema["paths"]
    assert "get" in schema["paths"]["/api/health"]
