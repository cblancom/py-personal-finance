# Tareas 010 — Tipo opcional de ingresos

- Estado: validada (T-001 a T-008 completadas).
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-003 ──► T-004
  │          │          │
  │          ├──► T-005 ──► T-006
  │          └──► T-007
  └──────────────────────► T-008
```

T-001 prepara el modelo y la migración. T-002 actualiza el contrato de ingresos. T-003 y T-004 ajustan el balance mensual y anual. T-005 y T-006 actualizan la interfaz de ingresos y de balance. T-007 alinea la importación. T-008 consolida pruebas, documentación, versión y producción.

Las decisiones D-001 a D-006 de `spec.md` están aprobadas. El plan está aprobado y T-001 a T-008 están completadas; la especificación queda validada.

## Tareas

- [x] **T-001 — Reemplazar la categoría por tipo en el modelo y la migración**
  - Requisitos: FR-001, FR-011, NFR-001, NFR-002, NFR-009.
  - Dependencias: ninguna.
  - Descripción: añadir `ingresos.tipo` nullable con `CHECK`; mapear valores históricos exactos de `categoria`; eliminar `categoria`; añadir `filas_importacion.tipo` nullable con `CHECK`; crear la migración `0008_add_income_type` con `upgrade` y `downgrade`; actualizar `Income` e `ImportRow`.
  - Hecho cuando: la migración se aplica y revierte en la base de test; la restricción rechaza valores inválidos; `categoria` ya no existe en `ingresos`; los valores históricos no mapeables quedan en `NULL`.
  - Evidencia (2026-11-03): migración `0008_add_income_type` aplicada, revertida a `0007` y reaplicada en `personal_finance_test`; backfill verificado (`Necesario`→`NECESARIO`, `No Necesario`→`NO_NECESARIO`, `Inversión`→`INVERSION`, `Nómina`→`NULL`, vacío→`NULL`); `categoria` eliminada de `ingresos`; `tipo` añadida a `filas_importacion`; restricciones `ck_ingresos_tipo_valido` y `ck_filas_importacion_tipo_valido` presentes y la primera rechaza valores inválidos. `test_database.py`: 3/3; unitarias y API: 158/158; ruff y format OK. La suite completa se ejecutó con 243 passed y 30 failed por las referencias pendientes a `category` en rutas e importación; se corrigen en T-002 y T-007.
  - Verificación:
    ```bash
    cd backend
    uv run alembic upgrade head
    uv run alembic downgrade 0007
    uv run alembic upgrade head
    uv run pytest tests/integration/test_database.py
    uv run pytest tests/core tests/api
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-002 — Actualizar schemas, rutas y OpenAPI de ingresos**
  - Requisitos: FR-002, FR-003, AC-003, AC-004.
  - Dependencias: T-001.
  - Descripción: reemplazar `categoria` por `tipo` en `IncomeWrite`, `IncomeCreate`, `IncomeUpdate` e `IncomeRead`; normalizar vacío a `null`; mapear `income_type` en las rutas; actualizar pruebas de schema y API.
  - Hecho cuando: crear, listar, consultar y editar aceptan/devuelven `tipo`; `categoria` no aparece en el contrato; un valor inválido devuelve `422`; OpenAPI refleja el enum.
  - Evidencia (2026-11-03): `IncomeWrite`/`IncomeRead` usan `tipo` opcional con el enum de rubros; vacío se normaliza a `null`; las rutas mapean `income_type`; OpenAPI ya no expone `categoria`. 64/64 pruebas de schemas, OpenAPI e integración de ingresos; ruff y format OK.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api/test_income_schemas.py tests/api/test_incomes_openapi.py tests/integration/test_incomes.py
    uv run ruff check .
    ```

- [x] **T-003 — Ajustar el cálculo mensual y el contrato de rubros**
  - Requisitos: FR-004, FR-005, FR-006, FR-007, FR-009, NFR-001, NFR-002.
  - Dependencias: T-002.
  - Descripción: separar ingresos sin tipo y tipados en la agregación mensual; calcular el asignado solo con ingresos sin tipo; sumar ingresos tipados al disponible; ajustar `sin_asignar`; añadir `ingresos_tipados` a `RubroBalance`, `BalanceRubroRead` y la ruta; mantener la cadena de arrastre.
  - Hecho cuando: un ingreso sin tipo conserva el cálculo actual; un ingreso tipado no se pondera, se suma al rubro y no aumenta `sin_asignar`; el arrastre usa el restante con ingresos tipados; el contrato incluye `ingresos_tipados`.
  - Evidencia (2026-11-03): la agregación mensual separa ingresos por tipo; el asignado usa solo ingresos sin tipo; `ingresos_tipados` se suma al disponible y no a `sin_asignar`; el restante tipado alimenta el arrastre. Pruebas mensuales de ingreso tipado, no ponderación, `sin_asignar` y arrastre necesario→no necesario. 34/34 pruebas de balance; ruff y format OK.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core/test_monthly_balance.py tests/api/test_monthly_balance_schema.py tests/integration/test_monthly_balance.py
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-004 — Ajustar el cálculo anual**
  - Requisitos: FR-008, FR-009, AC-009, AC-010.
  - Dependencias: T-003.
  - Descripción: sumar ingresos tipados por rubro en el año; calcular `disponible_anual` y `restante_anual` con la semántica de necesarios; calcular el porcentaje ponderado sobre ingresos sin tipo; ajustar pruebas de integración y schema.
  - Hecho cuando: la tabla anual incluye `ingresos_tipados`; no hay doble conteo; el restante de necesarios incluye ingresos tipados; el porcentaje ponderado usa ingresos sin tipo.
  - Evidencia (2026-11-03): el anual suma `ingresos_tipados` por rubro, calcula `disponible` y `restante` con la semántica de necesarios y usa ingresos sin tipo como denominador del porcentaje ponderado. Pruebas de ingreso tipado no duplicado, transferencia de necesario a no necesario y porcentaje ponderado. 36/36 pruebas de balance; ruff y format OK.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/integration/test_monthly_balance.py tests/api/test_monthly_balance_schema.py tests/core/test_monthly_balance.py
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-005 — Actualizar el frontend de ingresos**
  - Requisitos: FR-003, AC-012, NFR-007.
  - Dependencias: T-002.
  - Descripción: cambiar `Income`/`IncomePayload` a `tipo`; añadir selector `Tipo (opcional)` en `IncomeForm`; mostrar columna `Tipo` en `IncomeList`; actualizar fixtures, cliente API y pruebas.
  - Hecho cuando: el formulario envía `tipo` o `null`; el listado muestra el tipo o `—`; la edición conserva el tipo; lint, typecheck y pruebas pasan.
  - Evidencia (2026-11-03): `Income` y `IncomePayload` usan `tipo`; el formulario muestra el selector `Tipo (opcional)`; el listado muestra la etiqueta del tipo o `—`; fixtures y pruebas actualizados. 99/99 frontend; lint, typecheck y build OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-006 — Mostrar ingresos tipados en el balance**
  - Requisitos: FR-009, FR-010, AC-012, NFR-007.
  - Dependencias: T-003, T-004, T-005.
  - Descripción: añadir `ingresos_tipados` a los tipos de balance; mostrar el campo en la vista mensual y en la tabla anual; añadir la nota explicativa; actualizar fixtures y pruebas de `MonthlyBalanceView`, `App` y cliente API.
  - Hecho cuando: la vista muestra `Ingresos tipados`; la invariante `disponible = asignado + arrastre + ingresos_tipados` es visible; la nota explica que no se reparten por porcentajes; las pruebas pasan.
  - Evidencia (2026-11-03): `BalanceRubro` incluye `ingresos_tipados`; la vista mensual y la tabla anual muestran el campo; la nota explica que no se reparten por porcentajes. Fixtures de `MonthlyBalanceView`, `App` y cliente API actualizados. 99/99 frontend; lint, typecheck y build OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-007 — Alinear la importación de ingresos**
  - Requisitos: FR-011, AC-011, NFR-004.
  - Dependencias: T-001, T-002.
  - Descripción: normalizar `Categoría`/`Tipo` como tipo de ingreso; aceptar alias; dejar pendientes los valores desconocidos con error `tipo`; guardar texto original en `filas_importacion.categoria`; añadir `tipo` a pendientes, actualización y commit; actualizar `PendingView` y pruebas.
  - Hecho cuando: un ingreso con tipo válido se importa tipado; vacío importa sin tipo; desconocido queda pendiente; la corrección y contabilización funcionan; la importación de gastos no cambia.
  - Evidencia (2026-11-03): la importación interpreta `Categoría`/`Tipo` como tipo; los valores válidos se importan tipados, vacío queda sin tipo y desconocido queda pendiente con error `tipo`; el texto original se conserva en `filas_importacion.categoria`; `PendingView` permite corregir el tipo de ingreso y la importación de gastos no cambia. 80/80 pruebas de importación backend; 100/100 frontend; lint, typecheck y build OK.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core/test_import_normalization.py tests/core/test_import_validation.py tests/integration/test_imports_api.py
    uv run ruff check .
    ```
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-008 — Consolidar pruebas, documentación y versión 1.2.0**
  - Requisitos: FR-012, FR-013, AC-013, AC-014, NFR-005, NFR-006, NFR-008, NFR-009.
  - Dependencias: T-001 a T-007.
  - Descripción: ejecutar suites completas y regresión; actualizar README, AGENTS y `specs/README.md`; sincronizar versión `1.2.0`; validar producción y registrar evidencia.
  - Hecho cuando: backend y frontend pasan; resumen y gráficas no cambian; documentación y metadatos están sincronizados; producción está healthy y el smoke test pasa.
  - Evidencia (2026-11-03): 291/291 backend y 100/100 frontend; ruff, format, lint, typecheck y build OK; versión 1.2.0 sincronizada; producción healthy con migración `0008`, smoke OK, `/api/ingresos` devuelve `tipo` y el balance devuelve `ingresos_tipados`. Se tomó respaldo de producción antes de la migración destructiva.
  - Verificación:
    ```bash
    cd backend
    uv run --env-file ../.env pytest
    uv run ruff check .
    uv run ruff format --check .
    ```
    ```bash
    cd frontend
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml config -q
    docker compose --env-file .env.production -f compose.prod.yaml up --build -d
    WEB_PORT=3001 ./scripts/smoke.sh
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-001 |
| FR-002 | T-002 |
| FR-003 | T-005 |
| FR-004 | T-003 |
| FR-005 | T-003 |
| FR-006 | T-003 |
| FR-007 | T-003 |
| FR-008 | T-004 |
| FR-009 | T-003, T-004, T-006 |
| FR-010 | T-006 |
| FR-011 | T-001, T-007 |
| FR-012 | T-008 |
| FR-013 | T-008 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001, T-003, T-004 |
| NFR-002 | T-001, T-002 |
| NFR-003 | T-001, T-002, T-003 |
| NFR-004 | T-002, T-003, T-004, T-005, T-006, T-007, T-008 |
| NFR-005 | T-008 |
| NFR-006 | T-008 |
| NFR-007 | T-005, T-006 |
| NFR-008 | T-008 |
| NFR-009 | T-001, T-008 |

## Evidencia de validación

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumple | `ingresos.tipo` nullable con `ck_ingresos_tipo_valido`; `filas_importacion.tipo` con `ck_filas_importacion_tipo_valido`. |
| AC-002 | Cumple | `0008_add_income_type` aplicada, revertida y reaplicada en base de test. |
| AC-003 | Cumple | Contrato de ingresos con `tipo`; `categoria` fuera de la API. |
| AC-004 | Cumple | Tipo inválido `422`; vacío se normaliza a `null`. |
| AC-005 | Cumple | Ingresos sin tipo conservan el cálculo porcentual. |
| AC-006 | Cumple | Ingreso tipado excluido de porcentajes y sumado a `disponible`. |
| AC-007 | Cumple | Ingreso tipado no aumenta `sin_asignar`. |
| AC-008 | Cumple | Restante con ingreso tipado participa en el arrastre. |
| AC-009 | Cumple | Tabla anual incluye `ingresos_tipados` sin doble conteo. |
| AC-010 | Cumple | Porcentaje ponderado anual calculado sobre ingresos sin tipo. |
| AC-011 | Cumple | Importación con tipo válido, vacío y desconocido pendiente. |
| AC-012 | Cumple | Formulario, listado, balance mensual y anual actualizados. |
| AC-013 | Cumple | Resumen incluye ingresos tipados; gráficas sin regresión. |
| AC-014 | Cumple | Documentación, versión 1.2.0 y producción validadas. |

## Notas

- La migración `0008_add_income_type` es destructiva para `ingresos.categoria`.
- Los valores históricos que no coincidan exactamente con un tipo se pierden.
- Antes de ejecutar la migración en producción se requiere respaldo y autorización explícita.
- No se modifica `legacy/`.
- No se añaden dependencias nuevas.
- La versión publicada es `1.2.0`.
