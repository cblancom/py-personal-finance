# Tareas 002 — API de ingresos

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

- [x] **T-001 — Crear el modelo `Income` y registrarlo en metadata**
  - Requisitos: FR-001, NFR-001, NFR-002, NFR-003.
  - Dependencias: ninguna.
  - Descripción: crear `app/db/models/income.py` con la tabla `ingresos`, atributos ingleses, columnas españolas, checks e índice. Crear `app/db/models/__init__.py` e importar `Income`.
  - Hecho cuando: `Income.__tablename__ == "ingresos"`, las columnas son `id`, `fecha`, `descripcion`, `valor`, los checks y el índice existen en `Base.metadata` y ruff pasa.
  - Evidencia (2026-10-21): `Income.__tablename__` es `ingresos`; columnas `descripcion`, `fecha`, `id`, `valor`; checks `ck_ingresos_valor_positivo` y `ck_ingresos_descripcion_no_vacia`; índice `ix_ingresos_fecha`. Ruff y formato pasan (22 archivos); las 9 pruebas existentes siguen pasando.
  - Verificación:
    ```bash
    cd backend
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance \
      uv run python -c "from app.db.models import Income; print(Income.__tablename__); print(sorted(Income.__table__.columns.keys()))"
    uv run ruff check .
    ```

- [x] **T-002 — Ajustar Alembic y crear la migración `0002`**
  - Requisitos: FR-001, FR-002, NFR-003, NFR-007.
  - Dependencias: T-001.
  - Descripción: importar los modelos en `alembic/env.py`; usar la URL configurada si no está vacía y, en caso contrario, `get_settings()`; escapar `%`. Generar `0002_ingresos` con autogenerate, revisar checks e índice y aplicar la migración.
  - Hecho cuando: `alembic current` reporta `0002`; `\d ingresos` muestra columnas, checks e índice; `downgrade 0001` y `upgrade head` funcionan.
  - Evidencia (2026-10-21): migración `0002_create_ingresos.py`; `alembic current` = `0002 (head)`; `\d ingresos` muestra `id`, `fecha`, `descripcion`, `valor`, checks `ck_ingresos_*` e índice `ix_ingresos_fecha`; `downgrade 0001` y `upgrade head` funcionan. Ruff y formato pasan (23 archivos); las 9 pruebas siguen pasando.
  - Verificación:
    ```bash
    docker compose exec api uv run alembic revision --autogenerate --rev-id 0002 -m "create ingresos"
    docker compose exec api uv run alembic upgrade head
    docker compose exec api uv run alembic current
    docker compose exec db psql -U postgres -d personal_finance -c "\d ingresos"
    docker compose exec api uv run alembic downgrade 0001
    docker compose exec api uv run alembic upgrade head
    ```

- [x] **T-003 — Crear schemas Pydantic y pruebas de validación**
  - Requisitos: FR-008, FR-009, FR-010, FR-011, NFR-001, NFR-002, NFR-003.
  - Dependencias: T-001.
  - Descripción: crear `IncomeWrite`, `IncomeCreate`, `IncomeUpdate` e `IncomeRead` con campos en español y validaciones de fecha, descripción e importe. Añadir pruebas unitarias sin base de datos.
  - Hecho cuando: los casos válidos e inválidos pasan; la descripción se recorta; `valor` se serializa como string con dos decimales; ruff y pytest pasan sin PostgreSQL.
  - Evidencia (2026-10-21): 21 pruebas de schemas y 30 pruebas totales pasan sin PostgreSQL; se cubren importes válidos/límite/cero/negativos/demasiados decimales, descripción recortada/vacía/200/201 caracteres, fechas válidas/futuras/inválidas, campos obligatorios y serialización de `valor` como `"1500.50"`. Ruff y formato pasan (25 archivos).
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api/test_income_schemas.py
    uv run ruff check .
    ```

- [ ] **T-004 — Crear la base de test y el fixture de integración**
  - Requisitos: NFR-004, NFR-007, BR-009.
  - Dependencias: T-002.
  - Descripción: añadir el marcador `integration`; crear `tests/integration/conftest.py` y `__init__.py`. El fixture debe leer `TEST_DATABASE_URL`, omitir si falta, impedir que coincida con `DATABASE_URL`, crear `personal_finance_test` si no existe, ejecutar migraciones Alembic contra esa base, truncar `ingresos` entre pruebas y sobrescribir `get_db`.
  - Hecho cuando: una prueba de humo contra la base de test pasa; sin `TEST_DATABASE_URL` las pruebas de integración se omiten con un mensaje claro; la base de desarrollo no se modifica.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/integration -q
    TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance_test \
      uv run pytest tests/integration -q
    ```

- [ ] **T-005 — Implementar `POST`, `GET` lista y `GET` por id**
  - Requisitos: FR-003, FR-004, FR-005, FR-011, FR-012, FR-013, NFR-003, NFR-006.
  - Dependencias: T-002, T-003.
  - Descripción: crear `app/api/routes/incomes.py` con el router `/ingresos`, el mapeo `to_income_read`, los endpoints de creación, listado y consulta, y registrarlo en `app/main.py` bajo `/api`.
  - Hecho cuando: crear devuelve `201`; listar devuelve `200` con orden `fecha DESC, id DESC`; consultar devuelve `200` o `404`; el endpoint aparece en OpenAPI y las pruebas pasan.
  - Verificación:
    ```bash
    docker compose exec api env TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run pytest
    docker compose exec api uv run ruff check .
    ```

- [ ] **T-006 — Implementar `PUT` y `DELETE`**
  - Requisitos: FR-006, FR-007, FR-011, FR-012, FR-013.
  - Dependencias: T-005.
  - Descripción: añadir edición completa con `PUT` y eliminación con `DELETE`, reutilizando el helper de búsqueda y el mapeo de respuesta.
  - Hecho cuando: `PUT` actualiza los tres campos y devuelve `200`; `DELETE` devuelve `204`; ambos devuelven `404` para ids inexistentes; `PUT` inválido devuelve `422`; las pruebas pasan.
  - Verificación:
    ```bash
    docker compose exec api env TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run pytest
    docker compose exec api uv run ruff check .
    ```

- [ ] **T-007 — Completar pruebas de integración y restricciones**
  - Requisitos: FR-008, FR-009, FR-010, NFR-002, NFR-004.
  - Dependencias: T-004, T-005, T-006.
  - Descripción: cubrir lista vacía, orden, descripción recortada, ida y vuelta de importes, `422` por valor/descripción/fecha, `404` en todos los endpoints y violaciones directas de checks en PostgreSQL. Validar `downgrade 0001`/`upgrade head` sobre la base de test.
  - Hecho cuando: la suite de integración completa pasa; las restricciones de base de datos se comprueban; la migración es reversible; sin `TEST_DATABASE_URL` las pruebas de integración se omiten.
  - Verificación:
    ```bash
    docker compose exec api env TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run pytest
    docker compose exec api env DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run alembic downgrade 0001
    docker compose exec api env DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run alembic upgrade head
    ```

- [ ] **T-008 — Documentar, actualizar infraestructura y validar**
  - Requisitos: NFR-004, NFR-008, AC-011 a AC-014.
  - Dependencias: T-007.
  - Descripción: añadir `TEST_DATABASE_URL` a `.env.example` y al servicio `api` de `compose.yaml`; actualizar README, AGENTS y `specs/README.md`; ejecutar la validación completa, incluyendo regresión de salud, frontend y Docker.
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
| FR-011 | T-003, T-005, T-006 |
| FR-012 | T-005, T-006 |
| FR-013 | T-005, T-006 |

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
- La base `personal_finance_test` es la única que puede truncarse durante las pruebas.
- No se usa `Base.metadata.create_all()`; la base de test se prepara con Alembic.
- Los mensajes de validación de FastAPI pueden estar en inglés; la interfaz los traducirá en spec 005.
