import os
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.main import app


def _validate_database_name(url: URL) -> str:
    database = url.database
    if not database or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", database):
        pytest.exit(
            "TEST_DATABASE_URL debe incluir un nombre de base de datos válido",
            returncode=1,
        )
    if database == "postgres":
        pytest.exit(
            "TEST_DATABASE_URL no debe apuntar a la base postgres",
            returncode=1,
        )
    return database


def _assert_separate_from_development_database(url: URL) -> None:
    development_url = os.getenv("DATABASE_URL")
    if not development_url:
        return

    development = make_url(development_url)
    same_server = url.host == development.host and (url.port or 5432) == (development.port or 5432)
    if same_server and url.database == development.database:
        pytest.exit(
            "TEST_DATABASE_URL apunta a la misma base que DATABASE_URL; "
            "se aborta para evitar pérdida de datos",
            returncode=1,
        )


def _create_database_if_missing(url: URL, database_name: str) -> None:
    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database_name},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        admin_engine.dispose()


def _run_migrations(test_url: str) -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", test_url.replace("%", "%%"))
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def _test_database_url() -> str:
    test_url = os.getenv("TEST_DATABASE_URL")
    if not test_url:
        pytest.skip(
            "TEST_DATABASE_URL no está configurada; las pruebas de integración requieren PostgreSQL"
        )
    assert test_url

    url = make_url(test_url)
    _assert_separate_from_development_database(url)
    database_name = _validate_database_name(url)
    _create_database_if_missing(url, database_name)
    _run_migrations(test_url)
    return test_url


@pytest.fixture(scope="session")
def test_engine(_test_database_url: str) -> Iterator[Engine]:
    engine = create_engine(_test_database_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def reset_movements(test_engine: Engine) -> Iterator[None]:
    with test_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE ingresos, gastos RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def client(test_session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
