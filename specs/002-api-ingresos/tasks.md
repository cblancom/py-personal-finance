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

- [x] **T-004 — Crear la base de test y el fixture de integración**
  - Requisitos: NFR-004, NFR-007, BR-009.
  - Dependencias: T-002.
  - Descripción: añadir el marcador `integration`; crear `tests/integration/conftest.py` y `__init__.py`. El fixture debe leer `TEST_DATABASE_URL`, omitir si falta, impedir que coincida con `DATABASE_URL`, crear `personal_finance_test` si no existe, ejecutar migraciones Alembic contra esa base, truncar `ingresos` entre pruebas y sobrescribir `get_db`.
  - Hecho cuando: una prueba de humo contra la base de test pasa; sin `TEST_DATABASE_URL` las pruebas de integración se omiten con un mensaje claro; la base de desarrollo no se modifica.
  - Evidencia (2026-10-21): marcador `integration` registrado; fixture crea `personal_finance_test`, ejecuta migraciones y trunca `ingresos`; pruebas de humo verifican tabla/versión `0002` y el cliente contra la base de test. Sin `TEST_DATABASE_URL`: 30 pruebas pasan y 2 se omiten con mensaje claro. Con la URL de test: 32 pruebas pasan. La base de desarrollo no se modifica. Ruff y formato pasan (28 archivos).
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/integration -q
    TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance_test \
      uv run pytest tests/integration -q
    ```

- [x] **T-005 — Implementar `POST`, `GET` lista y `GET` por id**
  - Requisitos: FR-003, FR-004, FR-005, FR-011, FR-012, FR-013, NFR-003, NFR-006.
  - Dependencias: T-002, T-003.
  - Descripción: crear `app/api/routes/incomes.py` con el router `/ingresos`, el mapeo `to_income_read`, los endpoints de creación, listado y consulta, y registrarlo en `app/main.py` bajo `/api`.
  - Hecho cuando: crear devuelve `201`; listar devuelve `200` con orden `fecha DESC, id DESC`; consultar devuelve `200` o `404`; el endpoint aparece en OpenAPI y las pruebas pasan.
  - Evidencia (2026-10-21): `POST /api/ingresos` devuelve `201`; `GET /api/ingresos` devuelve lista ordenada; `GET /api/ingresos/{id}` devuelve `200` o `404`. OpenAPI documenta ambas rutas. 5 pruebas de integración nuevas y 1 prueba de OpenAPI; con `TEST_DATABASE_URL`: 38 pruebas pasan; sin ella: 31 pasan y 7 se omiten. En Docker, `GET /api/ingresos` responde `200 []` y un id inexistente `404`. Ruff y formato pasan (31 archivos).
  - Verificación:
    ```bash
    docker compose exec api env TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run pytest
    docker compose exec api uv run ruff check .
    ```

- [x] **T-006 — Implementar `PUT` y `DELETE`**
  - Requisitos: FR-006, FR-007, FR-011, FR-012, FR-013.
  - Dependencias: T-005.
  - Descripción: añadir edición completa con `PUT` y eliminación con `DELETE`, reutilizando el helper de búsqueda y el mapeo de respuesta.
  - Hecho cuando: `PUT` actualiza los tres campos y devuelve `200`; `DELETE` devuelve `204`; ambos devuelven `404` para ids inexistentes; `PUT` inválido devuelve `422`; las pruebas pasan.
  - Evidencia (2026-10-21): `PUT` actualiza fecha, descripción y valor, persiste y devuelve `200`; `DELETE` devuelve `204` sin cuerpo; ambos devuelven `404`; `PUT` inválido devuelve `422`. Se añadieron 5 pruebas de integración y OpenAPI documenta `put`/`delete`. Con `TEST_DATABASE_URL`: 43 pruebas pasan; sin ella: 31 pasan y 12 se omiten. Ciclo manual en Docker: POST `201` → PUT `200` → DELETE `204` → GET `404`. Ruff y formato pasan (31 archivos).
  - Verificación:
    ```bash
    docker compose exec api env TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run pytest
    docker compose exec api uv run ruff check .
    ```

- [x] **T-007 — Completar pruebas de integración y restricciones**
  - Requisitos: FR-008, FR-009, FR-010, NFR-002, NFR-004.
  - Dependencias: T-004, T-005, T-006.
  - Descripción: cubrir lista vacía, orden, descripción recortada, ida y vuelta de importes, `422` por valor/descripción/fecha, `404` en todos los endpoints y violaciones directas de checks en PostgreSQL. Validar `downgrade 0001`/`upgrade head` sobre la base de test.
  - Hecho cuando: la suite de integración completa pasa; las restricciones de base de datos se comprueban; la migración es reversible; sin `TEST_DATABASE_URL` las pruebas de integración se omiten.
  - Evidencia (2026-10-21): se cubren lista vacía, orden, descripción recortada, importes `1500.5` → `1500.50` y `9999999999.99`, `422` por importe/descripción/fecha/campos ausentes, `404` en GET/PUT/DELETE y violaciones directas de `valor > 0` y descripción no vacía con `IntegrityError`. Con `TEST_DATABASE_URL`: 62 pruebas pasan; sin ella: 31 pasan y 31 se omiten. `downgrade 0001` + `upgrade head` sobre la base de test deja `0002 (head)` y la suite vuelve a pasar. Ruff y formato pasan (31 archivos).
  - Verificación:
    ```bash
    docker compose exec api env TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run pytest
    docker compose exec api env DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run alembic downgrade 0001
    docker compose exec api env DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance_test uv run alembic upgrade head
    ```

- [x] **T-008 — Documentar, actualizar infraestructura y validar**
  - Requisitos: NFR-004, NFR-008, AC-011 a AC-014.
  - Dependencias: T-007.
  - Descripción: añadir `TEST_DATABASE_URL` a `.env.example` y al servicio `api` de `compose.yaml`; actualizar README, AGENTS y `specs/README.md`; ejecutar la validación completa, incluyendo regresión de salud, frontend y Docker.
  - Hecho cuando: la suite completa pasa en Docker; la suite unitaria pasa sin base de datos; el frontend sigue pasando; `docker compose up --build` deja todo saludable; la documentación refleja el contrato y el estado real.
  - Evidencia (2026-10-21): `TEST_DATABASE_URL` añadida a `.env.example` y al servicio `api`; README, AGENTS e índice actualizados. `docker compose config -q` OK; `up --build -d` deja `db`, `api` y `web` healthy; `/api/health` responde `200`; `GET /api/ingresos` responde `200 []`; `docker compose exec api uv run pytest` → 62 passed; suite unitaria local sin URL → 31 passed, 31 skipped; frontend → 7 passed, lint/typecheck/build OK; ruff/formato OK (31 archivos); `alembic current` → `0002 (head)`; sin secretos en logs.
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

Completada durante T-008.

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumplido | Tabla `ingresos` creada por la migración `0002` con columnas, checks e índice. |
| AC-002 | Cumplido | `downgrade 0001` + `upgrade head` sobre `personal_finance_test`; `alembic current` = `0002 (head)`. |
| AC-003 | Cumplido | Prueba de integración: `POST /api/ingresos` → `201` con `id`. |
| AC-004 | Cumplido | Prueba de integración: listado ordenado por `fecha DESC, id DESC`. |
| AC-005 | Cumplido | Pruebas de `GET` por id con `200` y `404`. |
| AC-006 | Cumplido | Prueba de `PUT` con actualización de los tres campos y persistencia. |
| AC-007 | Cumplido | Pruebas de `DELETE` con `204` y `404`. |
| AC-008 | Cumplido | Pruebas de `422` para importe, descripción, fecha y campos ausentes. |
| AC-009 | Cumplido | Inserciones directas inválidas producen `IntegrityError` por los checks. |
| AC-010 | Cumplido | Ida y vuelta `1500.5` → `1500.50` y límite `9999999999.99` como string. |
| AC-011 | Cumplido | `uv run pytest` sin `TEST_DATABASE_URL`: 31 passed, 31 skipped. |
| AC-012 | Cumplido | `docker compose exec api uv run pytest`: 62 passed contra `personal_finance_test`. |
| AC-013 | Cumplido | Prueba de OpenAPI para `POST`, `GET`, `PUT` y `DELETE`. |
| AC-014 | Cumplido | `/api/health` 200, frontend 7 pruebas, lint/typecheck/build y Docker healthy. |

## Notas

- No se implementa frontend en esta especificación.
- No se ejecuta `docker compose down -v` sin autorización.
- La base `personal_finance_test` es la única que puede truncarse durante las pruebas.
- No se usa `Base.metadata.create_all()`; la base de test se prepara con Alembic.
- Los mensajes de validación de FastAPI pueden estar en inglés; la interfaz los traducirá en spec 005.
