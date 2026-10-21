# Tareas 004 — API de resumen

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-003 ──► T-004
```

## Tareas

- [x] **T-001 — Crear el schema de respuesta del resumen**
  - Requisitos: FR-005, FR-006, NFR-001, NFR-003.
  - Dependencias: ninguna.
  - Descripción: crear `SummaryResponse` con `total_ingresos`, `total_gastos`, `balance` y `gastos_por_tipo: dict[ExpenseType, Decimal]`. Añadir una prueba de serialización sin base de datos.
  - Hecho cuando: el JSON contiene las claves en español, los tres tipos y valores como strings; el balance negativo se serializa correctamente; ruff y pytest pasan.
  - Evidencia (2026-10-21): `SummaryResponse` serializa las cuatro claves, los tres tipos como `NECESARIO`/`NO_NECESARIO`/`INVERSION`, importes como strings y balance negativo como `"-150.00"`. 3 pruebas de schema pasan; suite unitaria 62 passed, 67 skipped; ruff y formato OK (40 archivos).
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api/test_summary_schema.py
    uv run ruff check .
    ```

- [x] **T-002 — Implementar la agregación y `GET /api/resumen`**
  - Requisitos: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-001, NFR-002, NFR-003, NFR-005, NFR-006, NFR-007.
  - Dependencias: T-001.
  - Descripción: crear `app/api/routes/summary.py` con agregaciones SQL para ingresos y gastos agrupados por tipo. Normalizar importes a dos decimales, completar tipos ausentes con cero, calcular el balance y registrar el router en `app/main.py` bajo `/api`.
  - Hecho cuando: `GET /api/resumen` responde `200`; la base vacía devuelve todo en `"0.00"`; los totales, el balance y el desglose son correctos; no se cargan movimientos individuales en memoria; no se añade migración.
  - Evidencia (2026-10-21): `GET /api/resumen` responde `200`; base vacía devuelve todo `"0.00"`; con ingresos `1000.00` y gastos `NECESARIO 300.00` + `INVERSION 200.00` devuelve totales `1000.00`/`500.00`, balance `500.00` y desglose correcto. Usa `SUM` y `GROUP BY`; no crea migración ni dependencias. Ruff y formato pasan (41 archivos); 62 unitarias pasan y 67 se omiten.
  - Verificación:
    ```bash
    cd backend
    uv run ruff check .
    curl -sS http://localhost:8000/api/resumen
    ```

- [x] **T-003 — Cubrir el resumen con pruebas de integración y OpenAPI**
  - Requisitos: FR-001 a FR-011, NFR-004.
  - Dependencias: T-002.
  - Descripción: crear `tests/integration/test_summary.py` y `tests/api/test_summary_openapi.py`. Crear ingresos y gastos mediante las APIs y verificar totales, balance, desglose, tipos ausentes, base vacía, balance negativo, strings decimales y consistencia entre total y desglose.
  - Hecho cuando: todos los casos pasan contra `personal_finance_test`; la suite sin `TEST_DATABASE_URL` sigue omitiendo integración; OpenAPI documenta `/api/resumen`.
  - Evidencia (2026-10-21): 5 pruebas de integración cubren base vacía, solo ingresos, solo gastos, mezcla, balance negativo, tipos ausentes y consistencia `total_gastos == suma(desglose)`; 1 prueba de OpenAPI. Con `TEST_DATABASE_URL`: 135 pruebas pasan; sin ella: 63 pasan y 72 se omiten. Ruff y formato pasan (43 archivos).
  - Verificación:
    ```bash
    cd backend
    TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance_test \
      uv run pytest
    uv run ruff check .
    ```

- [x] **T-004 — Documentar y validar la especificación**
  - Requisitos: NFR-008, AC-011, AC-012.
  - Dependencias: T-003.
  - Descripción: actualizar README, AGENTS y `specs/README.md` con el endpoint de resumen, el contrato y el estado. Ejecutar la validación completa, incluyendo ingresos, gastos, salud, frontend y Docker.
  - Hecho cuando: la suite completa pasa en Docker; el frontend sigue pasando; los tres endpoints responden `200`; la documentación refleja el contrato; la spec queda validada.
  - Evidencia (2026-10-21): README, AGENTS y `specs/README.md` actualizados con el resumen y el estado validado. `docker compose config -q` OK; `up --build -d` deja `db`, `api` y `web` healthy; `/api/health`, `/api/ingresos`, `/api/gastos` y `/api/resumen` responden `200`; resumen vacío devuelve todo `"0.00"`; `docker compose exec api uv run pytest` → 135 passed; suite unitaria local sin URL → 63 passed, 72 skipped; frontend → 7 passed, lint/typecheck/build OK; ruff/formato OK (43 archivos); `alembic current` → `0003 (head)`; sin secretos en logs.
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
| FR-001 | T-002, T-003 |
| FR-002 | T-002, T-003 |
| FR-003 | T-002, T-003 |
| FR-004 | T-002, T-003 |
| FR-005 | T-001, T-002, T-003 |
| FR-006 | T-001, T-002, T-003 |
| FR-007 | T-002, T-003 |
| FR-008 | T-002, T-003 |
| FR-009 | T-002 |
| FR-010 | T-002, T-003 |
| FR-011 | T-003 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001, T-002 |
| NFR-002 | T-002 |
| NFR-003 | T-001, T-002 |
| NFR-004 | T-003, T-004 |
| NFR-005 | T-002 |
| NFR-006 | T-002 |
| NFR-007 | T-002, T-004 |
| NFR-008 | T-003, T-004 |

## Evidencia de validación

Completada durante T-004.

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumplido | `GET /api/resumen` responde `200`; OpenAPI documenta la ruta. |
| AC-002 | Cumplido | Totales de ingresos verificados con varios registros. |
| AC-003 | Cumplido | Totales de gastos verificados con varios registros. |
| AC-004 | Cumplido | Balance positivo y negativo verificados. |
| AC-005 | Cumplido | `gastos_por_tipo` incluye los tres tipos. |
| AC-006 | Cumplido | Tipos sin movimientos aparecen en `"0.00"`. |
| AC-007 | Cumplido | `total_gastos` coincide con la suma del desglose. |
| AC-008 | Cumplido | Base vacía devuelve todos los valores en `"0.00"`. |
| AC-009 | Cumplido | Importes serializados como strings con dos decimales. |
| AC-010 | Cumplido | Agregaciones con `SUM` y `GROUP BY` en PostgreSQL. |
| AC-011 | Cumplido | Las suites de ingresos y gastos siguen pasando. |
| AC-012 | Cumplido | Prueba de OpenAPI para `/api/resumen`. |

## Notas

- No se implementa frontend en esta especificación.
- No se crean tablas ni migraciones.
- No se añaden dependencias.
- El resumen es global; el filtro mensual queda post-MVP.
- La base `personal_finance_test` es compartida con las pruebas de ingresos y gastos.
- Los mensajes de validación de FastAPI pueden estar en inglés; la interfaz los traducirá en spec 005.
