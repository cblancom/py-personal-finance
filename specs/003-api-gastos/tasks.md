# Tareas 003 — API de gastos

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-004 ─────────────┐
  │          └──► T-005 ──► T-006 ──► T-007 ──► T-008
  └──► T-003 ──► T-005
```

## Tareas

- [x] **T-001 — Crear el modelo `Expense` y `ExpenseType`**
  - Requisitos: FR-001, FR-011, NFR-001, NFR-002, NFR-003.
  - Dependencias: ninguna.
  - Descripción: crear `app/db/models/expense.py` con el enum `ExpenseType`, la tabla `gastos`, atributos ingleses, columnas españolas, checks e índice. Exportar `Expense` desde `app/db/models/__init__.py`.
  - Hecho cuando: `Expense.__tablename__ == "gastos"`, las columnas son `id`, `fecha`, `descripcion`, `tipo`, `valor`, los checks y el índice existen, y `ExpenseType` expone los tres valores correctos. Ruff pasa.
  - Evidencia (2026-10-21): modelo `gastos` con columnas `id`, `fecha`, `descripcion`, `tipo`, `valor`; checks `ck_gastos_*`; índice `ix_gastos_fecha`; `ExpenseType` = `NECESARIO`, `NO_NECESARIO`, `INVERSION`. Se usa `StrEnum` para evitar UP042. Ruff, formato y pruebas existentes pasan.
  - Verificación:
    ```bash
    cd backend
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance \
      uv run python -c "from app.db.models import Expense; print(Expense.__tablename__); print(sorted(Expense.__table__.columns.keys()))"
    uv run ruff check .
    ```

- [x] **T-002 — Crear la migración `0003`**
  - Requisitos: FR-001, FR-002, NFR-003, NFR-007.
  - Dependencias: T-001.
  - Descripción: generar `0003_create_gastos` con `down_revision = "0002"`, revisar los checks e índice, aplicar la migración y validar el downgrade.
  - Hecho cuando: `alembic current` reporta `0003`; `\d gastos` muestra columnas, checks e índice; `downgrade 0002` y `upgrade head` funcionan.
  - Evidencia (2026-10-21): migración `0003_create_gastos`; `alembic current` = `0003 (head)`; `\d gastos` muestra columnas, checks `ck_gastos_*` e índice `ix_gastos_fecha`; `downgrade 0002` + `upgrade head` funcionan. Ruff y formato pasan.
  - Verificación:
    ```bash
    docker compose exec api uv run alembic revision --autogenerate --rev-id 0003 -m "create gastos"
    docker compose exec api uv run alembic upgrade head
    docker compose exec db psql -U postgres -d personal_finance -c "\d gastos"
    docker compose exec api uv run alembic downgrade 0002
    docker compose exec api uv run alembic upgrade head
    ```

- [x] **T-003 — Crear schemas Pydantic y pruebas unitarias**
  - Requisitos: FR-008, FR-009, FR-010, FR-011, FR-012, NFR-001, NFR-002, NFR-003.
  - Dependencias: T-001.
  - Descripción: crear `ExpenseWrite`, `ExpenseCreate`, `ExpenseUpdate` y `ExpenseRead` con `tipo: ExpenseType`; validar fecha, descripción y valor. Añadir pruebas sin base de datos.
  - Hecho cuando: los tres tipos válidos se aceptan; tipo desconocido/minúsculas se rechaza; importes, descripción y fecha inválidos fallan; `valor` se serializa como string; ruff y pytest pasan sin PostgreSQL.
  - Evidencia (2026-10-21): 27 pruebas de schemas pasan sin PostgreSQL; cubren los tres tipos, tipo desconocido/minúsculas, importes, descripción, fecha, campos obligatorios, recorte y serialización de `tipo`/`valor`. Ruff y formato pasan (35 archivos).
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api/test_expense_schemas.py
    uv run ruff check .
    ```

- [x] **T-004 — Adaptar el fixture de integración a `gastos`**
  - Requisitos: NFR-004, NFR-009.
  - Dependencias: T-002.
  - Descripción: actualizar `tests/integration/conftest.py` para truncar `ingresos` y `gastos` entre pruebas. Actualizar `test_database.py` para esperar la revisión `0003` y la existencia de ambas tablas.
  - Hecho cuando: las pruebas de integración de ingresos siguen pasando, la base de test está en `0003`, y el fixture limpia ambas tablas.
  - Evidencia (2026-10-21): fixture `reset_movements` trunca `ingresos, gastos`; base de test en `0003` con ambas tablas. Con `TEST_DATABASE_URL`: 89 pruebas pasan (incluidas las de ingresos); sin ella: 58 pasan y 31 se omiten. Ruff y formato pasan (35 archivos).
  - Verificación:
    ```bash
    cd backend
    TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance_test \
      uv run pytest tests/integration -q
    uv run pytest tests/integration -q
    ```

- [ ] **T-005 — Implementar `POST`, `GET` lista y `GET` por id**
  - Requisitos: FR-003, FR-004, FR-005, FR-012, FR-013, FR-014, NFR-003, NFR-006.
  - Dependencias: T-002, T-003.
  - Descripción: crear `app/api/routes/expenses.py` con el router `/gastos`, `to_expense_read`, `get_expense_or_404`, los endpoints de creación, listado y consulta, y registrarlo en `app/main.py` bajo `/api`.
  - Hecho cuando: crear devuelve `201`; listar devuelve `200` con orden `fecha DESC, id DESC`; consultar devuelve `200` o `404`; OpenAPI documenta las rutas y las pruebas pasan.
  - Verificación:
    ```bash
    docker compose exec api uv run pytest
    docker compose exec api uv run ruff check .
    ```

- [ ] **T-006 — Implementar `PUT` y `DELETE`**
  - Requisitos: FR-006, FR-007, FR-012, FR-013, FR-014.
  - Dependencias: T-005.
  - Descripción: añadir edición completa con `PUT` y eliminación con `DELETE`, reutilizando el helper y el mapeo.
  - Hecho cuando: `PUT` actualiza los cuatro campos y devuelve `200`; `DELETE` devuelve `204`; ambos devuelven `404`; `PUT` inválido devuelve `422`; las pruebas pasan.
  - Verificación:
    ```bash
    docker compose exec api uv run pytest
    docker compose exec api uv run ruff check .
    ```

- [ ] **T-007 — Completar pruebas de integración y restricciones**
  - Requisitos: FR-008, FR-009, FR-010, FR-011, NFR-002, NFR-004.
  - Dependencias: T-004, T-005, T-006.
  - Descripción: cubrir lista vacía, orden, descripción recortada, ida y vuelta de importes, `422` por valor/descripción/fecha/tipo, `404` en todos los endpoints y violaciones directas de checks (valor, descripción y tipo). Validar `downgrade 0002`/`upgrade head` sobre la base de test.
  - Hecho cuando: la suite de integración completa pasa; las tres restricciones de base de datos se comprueban; la migración es reversible; sin `TEST_DATABASE_URL` las pruebas de integración se omiten.
  - Verificación:
    ```bash
    docker compose exec api env TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run pytest
    docker compose exec api env DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run alembic downgrade 0002
    docker compose exec api env DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run alembic upgrade head
    ```

- [ ] **T-008 — Documentar, actualizar infraestructura y validar**
  - Requisitos: NFR-004, NFR-008, AC-011 a AC-014.
  - Dependencias: T-007.
  - Descripción: actualizar README, AGENTS y `specs/README.md` con la API de gastos, los valores de `tipo`, el estado y las pruebas. Ejecutar la validación completa, incluyendo ingresos, salud, frontend y Docker.
  - Hecho cuando: la suite completa pasa en Docker; la suite unitaria pasa sin base de datos; el frontend sigue pasando; `docker compose up --build` deja todo saludable; la documentación refleja el contrato y el estado real.
  - Verificación:
    ```bash
    docker compose config -q
    docker compose up --build -d
    docker compose exec api uv run pytest
    docker compose exec api uv run ruff check .
    docker compose exec api uv run ruff format --check .
    docker compose exec api uv run alembic current
    cd frontend && npm run lint && npm run typecheck && npm run test && npm run build
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-001, T-002 |
| FR-002 | T-002 |
| FR-003 | T-005 |
| FR-004 | T-005 |
| FR-005 | T-005 |
| FR-006 | T-006 |
| FR-007 | T-006 |
| FR-008 | T-003, T-007 |
| FR-009 | T-003, T-007 |
| FR-010 | T-003, T-007 |
| FR-011 | T-001, T-003, T-007 |
| FR-012 | T-003, T-005, T-006 |
| FR-013 | T-005, T-006 |
| FR-014 | T-005, T-006 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001, T-003 |
| NFR-002 | T-001, T-003, T-007 |
| NFR-003 | T-001, T-003, T-005, T-006 |
| NFR-004 | T-004, T-007, T-008 |
| NFR-005 | T-005, T-006 |
| NFR-006 | T-005 |
| NFR-007 | T-002, T-004, T-007 |
| NFR-008 | T-008 |
| NFR-009 | T-004, T-007 |

## Evidencia de validación

Se completa durante T-008.

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Pendiente | |
| AC-002 | Pendiente | |
| AC-003 | Pendiente | |
| AC-004 | Pendiente | |
| AC-005 | Pendiente | |
| AC-006 | Pendiente | |
| AC-007 | Pendiente | |
| AC-008 | Pendiente | |
| AC-009 | Pendiente | |
| AC-010 | Pendiente | |
| AC-011 | Pendiente | |
| AC-012 | Pendiente | |
| AC-013 | Pendiente | |
| AC-014 | Pendiente | |

## Notas

- No se implementa frontend en esta especificación.
- No se ejecuta `docker compose down -v` sin autorización.
- La base `personal_finance_test` es compartida con la API de ingresos; el fixture debe truncar `ingresos` y `gastos`.
- No se usa `Base.metadata.create_all()`; la base de test se prepara con Alembic.
- El tipo se almacena como `VARCHAR(20)` + `CHECK`, no como enum nativo de PostgreSQL.
- Los mensajes de validación de FastAPI pueden estar en inglés; la interfaz los traducirá en spec 005.
