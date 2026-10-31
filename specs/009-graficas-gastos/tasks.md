# Tareas 009 — Gráficas de gastos mensuales

- Estado: validada.
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-003 ──► T-004 ──► T-005 ──► T-006 ──► T-007
```

T-001 implementa la agregación. T-002 expone el contrato. T-003 añade Recharts y el componente de gráfica. T-004 construye la sección con selector y estados. T-005 integra en `App`. T-006 consolida pruebas. T-007 actualiza metadatos, documentación y valida producción.

Las decisiones D-001 a D-005 de `spec.md` y el plan están aprobados. La implementación avanza por tareas.

## Tareas

- [x] **T-001 — Implementar la serie mensual de gastos**
  - Requisitos: FR-002, FR-003, NFR-001, NFR-002.
  - Dependencias: ninguna.
  - Descripción: crear `app/services/charts.py` con una función que agregue gastos por mes y tipo para un año, inicialice los doce meses en cero y devuelva la serie ordenada.
  - Hecho cuando: la consulta usa `SUM` y `GROUP BY`; los meses sin datos aparecen en cero; no se cargan gastos individuales; los importes usan `Decimal`.
  - Evidencia (2026-10-31): `charts.py` agrega por mes y tipo con `SUM`/`GROUP BY`, rellena los doce meses en cero y devuelve una serie con `Decimal`; 2 pruebas unitarias nuevas; 264/264 backend.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-002 — Exponer el endpoint y los schemas de la gráfica**
  - Requisitos: FR-002, FR-003, FR-012.
  - Dependencias: T-001.
  - Descripción: crear `app/api/schemas/charts.py` y `app/api/routes/charts.py` con `GET /api/graficos/gastos-mensuales?anio=...`, validar el año y registrar el router en `main.py`.
  - Hecho cuando: el endpoint responde `200`; usa el año actual si falta `anio`; devuelve doce meses y tres tipos; `422` para años inválidos; OpenAPI contiene la ruta.
  - Evidencia (2026-10-31): `GET /api/graficos/gastos-mensuales` valida `anio`, usa el año actual por defecto y devuelve doce meses con tres tipos; OpenAPI y pruebas de integración/schema incluidas; 264/264 backend.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api tests/integration
    uv run ruff check .
    ```

- [x] **T-003 — Añadir Recharts y el componente de gráfica**
  - Requisitos: FR-004, FR-005, FR-006, FR-008, NFR-003, NFR-004.
  - Dependencias: T-002.
  - Descripción: instalar `recharts@3.10.1` y `react-is@19.3.1`; crear tipos, cliente API y `ExpenseChart` con barras apiladas, tres líneas, leyenda y tooltips en COP.
  - Hecho cuando: Recharts renderiza ambos modos; las tres series usan los mismos datos; los importes se formatean correctamente; el build y las pruebas de componente pasan.
  - Evidencia (2026-10-31): Recharts 3.10.1 y react-is 19.3.1 instalados; tipos, cliente API y `ExpenseChart` con barras apiladas, tres líneas, leyenda y tooltip; 4 pruebas nuevas; 92/92 frontend y build OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-004 — Construir la sección con selector, toggle y tabla**
  - Requisitos: FR-006, FR-007, FR-009, FR-010, NFR-004, NFR-005.
  - Dependencias: T-003.
  - Descripción: crear `ChartSection` con selector de año, toggle `Barras`/`Líneas`, carga, error con reintento, estado vacío y `Ver datos` con tabla accesible.
  - Hecho cuando: el selector actualiza la serie; el toggle no vuelve a consultar; los estados se muestran correctamente; la tabla es navegable.
  - Evidencia (2026-10-31): `ChartSection` con selector de año, toggle sin refetch, estados de carga/error/vacío y `Ver datos`; 5 pruebas nuevas; 97/97 frontend; lint, typecheck y build OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [x] **T-005 — Integrar la gráfica en la pantalla principal**
  - Requisitos: FR-001, FR-011, NFR-005, NFR-007.
  - Dependencias: T-004.
  - Descripción: insertar `ChartSection` después de `SummaryPanel` y antes del tablist; pasar `refreshKey={loadVersion}` para refrescar tras mutaciones de gastos.
  - Hecho cuando: la gráfica aparece en la posición correcta; se actualiza al crear, editar, eliminar o importar gastos; no rompe las pestañas existentes.
  - Evidencia (2026-10-31): `ChartSection` insertado entre `SummaryPanel` y el tablist; refresco mediante `refreshKey={loadVersion}`; prueba de `App` y de refresco de la sección; 99/99 frontend y build OK (advertencia de chunk >500 kB por Recharts).
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-006 — Consolidar pruebas y regresión**
  - Requisitos: FR-001 a FR-012, NFR-004, NFR-007.
  - Dependencias: T-001 a T-005.
  - Descripción: cubrir backend, OpenAPI, cliente API, componentes, toggle, selector, estados, tabla y App; mockear `ResizeObserver` para Recharts; ejecutar las suites completas.
  - Hecho cuando: backend y frontend pasan; no hay regresiones en resumen, balance, importación ni CRUD.
  - Evidencia (2026-10-31): 264/264 pruebas backend y 99/99 frontend; sin regresiones en resumen, balance, importación ni CRUD. Build correcto con la advertencia de chunk >500 kB aceptada por decisión de producto.
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

- [x] **T-007 — Publicar la versión 1.0.0**
  - Requisitos: FR-013, NFR-006, NFR-008, AC-014.
  - Dependencias: T-006.
  - Descripción: actualizar metadatos a `1.0.0`, documentar la gráfica y la release, reconstruir producción y ejecutar el smoke test.
  - Hecho cuando: `package.json`, `package-lock.json`, `pyproject.toml`, `uv.lock`, `main.py` y README están sincronizados; producción está healthy; la especificación queda validada.
  - Evidencia (2026-10-31): versión 1.0.0 sincronizada en `package.json`, `package-lock.json`, `pyproject.toml`, `uv.lock` y `main.py`; 265/265 backend y 99/99 frontend; producción reconstruida, migración `0007` vigente, servicios healthy, smoke OK, versión OpenAPI 1.0.0 y endpoint de gráficas verificado.
  - Verificación:
    ```bash
    cd frontend
    npm run build
    ```
    ```bash
    cd backend
    uv lock
    uv run ruff check .
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
| FR-001 | T-005 |
| FR-002 | T-001, T-002 |
| FR-003 | T-001, T-002 |
| FR-004 | T-003 |
| FR-005 | T-003 |
| FR-006 | T-003, T-004 |
| FR-007 | T-004 |
| FR-008 | T-003 |
| FR-009 | T-004 |
| FR-010 | T-004 |
| FR-011 | T-005 |
| FR-012 | T-002, T-006 |
| FR-013 | T-007 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001, T-003 |
| NFR-002 | T-001 |
| NFR-003 | T-003, T-007 |
| NFR-004 | T-003, T-004 |
| NFR-005 | T-004, T-005 |
| NFR-006 | T-001, T-007 |
| NFR-007 | T-005, T-006 |
| NFR-008 | T-007 |

## Evidencia de validación

Validada en T-007.

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumple | Gráfica insertada entre resumen y formularios; prueba de `App`. |
| AC-002 | Cumple | Endpoint con doce meses y tres tipos; pruebas de API. |
| AC-003 | Cumple | Barras apiladas por categoría; prueba de componente. |
| AC-004 | Cumple | Tres líneas continuas; prueba de componente. |
| AC-005 | Cumple | Toggle Barras/Líneas sin refetch. |
| AC-006 | Cumple | Selector de año con recarga de la serie. |
| AC-007 | Cumple | Meses sin gastos en cero. |
| AC-008 | Cumple | Leyenda, tooltip y tabla accesible. |
| AC-009 | Cumple | Refresco con `refreshKey={loadVersion}`. |
| AC-010 | Cumple | Agregación SQL por mes y tipo. |
| AC-011 | Cumple | Estados de carga, error y vacío. |
| AC-012 | Cumple | Ruta y schemas en OpenAPI. |
| AC-013 | Cumple | 265/265 backend, 99/99 frontend y build. |
| AC-014 | Cumple | Metadatos y OpenAPI en 1.0.0. |

## Notas

- T-001 a T-007 están completadas; la especificación queda validada.
- No se modifica `legacy/`.
- No se modifican las especificaciones 001 a 008.
- Se añaden `recharts@3.10.1` y `react-is@19.3.1` al frontend.
- No se añaden dependencias backend.
- No se crean tablas ni migraciones.
- La versión 1.0.0 se declara en T-007.
