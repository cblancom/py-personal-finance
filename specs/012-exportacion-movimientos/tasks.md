# Tareas 012 — Exportación de ingresos y gastos

- Estado: validada (T-001 a T-006 completadas).
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-003 ──► T-004 ──► T-005 ──► T-006
```

T-001 implementa la generación de archivos. T-002 expone los endpoints. T-003 añade el cliente de descarga. T-004 integra la sección y renombra el botón. T-005 cubre pruebas y compatibilidad. T-006 documenta, versiona y valida.

Las decisiones D-001 a D-005 de `spec.md` están aprobadas. El plan está aprobado y T-001 a T-006 están completadas; la especificación queda validada.

## Tareas

- [x] **T-001 — Implementar la generación CSV y XLSX**
  - Requisitos: FR-002, FR-003, FR-008, NFR-001, NFR-002.
  - Dependencias: ninguna.
  - Descripción: crear `app/services/exports.py` con funciones para serializar ingresos y gastos en CSV y XLSX. Usar `csv` estándar, UTF-8 con BOM, coma y punto decimal; usar `openpyxl` para XLSX con una hoja y cabecera.
  - Hecho cuando: los cuatro formatos generan bytes válidos; los importes son strings con dos decimales; las descripciones con comas, comillas y acentos se conservan; una exportación vacía incluye solo cabecera.
  - Evidencia (2026-11-06): `app/services/exports.py` genera CSV con BOM UTF-8, coma y punto decimal, y XLSX con una hoja y cabecera. 7/7 pruebas en `tests/core/test_exports.py`; ruff y format OK. Las rutas y la UI quedan para T-002 a T-004.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core/test_exports.py
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-002 — Exponer los endpoints de exportación**
  - Requisitos: FR-001, FR-004, FR-009, NFR-003, NFR-006.
  - Dependencias: T-001.
  - Descripción: crear `app/api/routes/exports.py` con `GET /exportaciones/ingresos` y `GET /exportaciones/gastos`; validar `formato`; consultar movimientos ordenados por fecha e id; devolver `Response` con MIME y `Content-Disposition`. Registrar el router en `main.py`.
  - Hecho cuando: ambos recursos responden CSV/XLSX; los nombres de archivo y cabeceras son correctos; un formato inválido devuelve `422`; OpenAPI documenta las rutas.
  - Evidencia (2026-11-06): `GET /api/exportaciones/ingresos` y `GET /api/exportaciones/gastos` aceptan `formato=csv|xlsx`, devuelven adjuntos con MIME y `Content-Disposition`, ordenan por fecha e id y rechazan formatos inválidos con `422`. 8/8 pruebas de OpenAPI e integración; suite completa 306/306; ruff y format OK.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api/test_exports_openapi.py tests/integration/test_exports.py
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-003 — Crear el cliente de descarga del frontend**
  - Requisitos: FR-004, FR-006, NFR-005.
  - Dependencias: T-002.
  - Descripción: crear `frontend/src/api/exports.ts` con `downloadIncomes` y `downloadExpenses`; usar `fetch`, `blob`, `Content-Disposition` y un enlace temporal. Manejar errores con `ApiError`.
  - Hecho cuando: las funciones descargan el MIME correcto; el nombre del archivo se obtiene del servidor o se construye de forma consistente; los errores se propagan.
  - Evidencia (2026-11-06): `downloadIncomes` y `downloadExpenses` usan `fetch`, `blob`, `Content-Disposition` y un enlace temporal; los errores se convierten en `ApiError`. 4/4 pruebas del cliente; lint y typecheck OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test -- --run exports
    npm run lint
    npm run typecheck
    ```

- [x] **T-004 — Integrar la sección de exportación y renombrar el botón**
  - Requisitos: FR-005, FR-006, AC-005, AC-006, AC-007.
  - Dependencias: T-003.
  - Descripción: crear `ExportSection` con selector CSV/XLSX, botones `Exportar ingresos` y `Exportar gastos`, estado `Preparando...` y error accesible. Integrarlo en `ImportView` debajo del formulario. Cambiar el botón de `App` a `Importar/Exportar`.
  - Hecho cuando: la sección aparece dentro de la vista; ambos botones llaman al formato correcto; el botón principal se llama `Importar/Exportar`; no se rompe el flujo de importación.
  - Evidencia (2026-11-06): `ExportSection` permite elegir CSV/XLSX y exportar ingresos o gastos con estado `Preparando...` y error accesible; está integrado en `ImportView`; el botón principal y el título de la vista usan `Importar/Exportar`. 109/109 pruebas frontend; lint, typecheck y build OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test -- --run ExportSection ImportView App
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-005 — Cubrir compatibilidad de ida y vuelta**
  - Requisitos: FR-007, AC-008, AC-009, NFR-001.
  - Dependencias: T-001, T-002, T-004.
  - Descripción: añadir pruebas de integración que exporten ingresos y gastos en CSV/XLSX y los reimporten en una base limpia; comparar fecha, descripción, valor y tipo. Cubrir acentos, comas, comillas, saltos de línea, ingresos sin tipo y exportaciones vacías.
  - Hecho cuando: la ida y vuelta conserva los movimientos; los casos especiales pasan; las exportaciones vacías son válidas.
  - Evidencia (2026-11-06): pruebas parametrizadas de ida y vuelta para ingresos y gastos en CSV y XLSX; se conservan fecha, descripción, valor y tipo, incluyendo acentos, comas, comillas y saltos de línea. 11/11 pruebas de exportación; ruff y format OK.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/integration/test_exports.py
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-006 — Documentar, versionar y validar**
  - Requisitos: FR-009, AC-010, NFR-004, NFR-006.
  - Dependencias: T-001 a T-005.
  - Descripción: actualizar README, AGENTS y `specs/README.md`; sincronizar versión `1.3.0`; ejecutar suites completas y validar producción.
  - Hecho cuando: documentación y metadatos están sincronizados; backend y frontend pasan; producción está healthy y el smoke test pasa; la spec queda validada.
  - Evidencia (2026-11-06): 310/310 backend y 109/109 frontend; ruff, format, lint, typecheck y build OK; versión 1.3.0 sincronizada; producción healthy con smoke OK y endpoints de exportación CSV/XLSX verificados. La especificación queda validada.
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
| FR-001 | T-002 |
| FR-002 | T-001 |
| FR-003 | T-001 |
| FR-004 | T-002, T-003 |
| FR-005 | T-004 |
| FR-006 | T-003, T-004 |
| FR-007 | T-005 |
| FR-008 | T-001, T-002 |
| FR-009 | T-002, T-006 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001, T-005 |
| NFR-002 | T-001 |
| NFR-003 | T-002 |
| NFR-004 | T-006 |
| NFR-005 | T-004 |
| NFR-006 | T-002, T-006 |

## Evidencia de validación

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumple | Endpoints de ingresos y gastos en CSV/XLSX documentados y probados. |
| AC-002 | Cumple | CSV con BOM UTF-8, coma y punto decimal. |
| AC-003 | Cumple | XLSX con hoja `Ingresos`/`Gastos` y cabecera. |
| AC-004 | Cumple | `Content-Disposition` y MIME verificados. |
| AC-005 | Cumple | Botón principal `Importar/Exportar`. |
| AC-006 | Cumple | Selector de formato y botones en `ImportView`. |
| AC-007 | Cumple | Estado `Preparando...` y error accesible. |
| AC-008 | Cumple | Ida y vuelta CSV/XLSX para ingresos y gastos. |
| AC-009 | Cumple | Exportaciones vacías solo con cabeceras. |
| AC-010 | Cumple | Sin dependencias nuevas ni cambios de contrato existente. |

## Notas

- La exportación es de movimientos, no un backup completo de PostgreSQL.
- Reimportar en la misma base duplica movimientos.
- No se incluyen asignaciones mensuales, pendientes, lotes, IDs ni historial.
- No se añaden dependencias.
- La versión publicada es `1.3.0`.
