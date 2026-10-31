# Tareas 007 — Importación de ingresos y gastos desde Excel y CSV

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002
  ├──► T-003 ──► T-004
  ├──► T-003 ──► T-005
  └──► T-013
T-002 + T-004 + T-005 ──► T-006 ──► T-007 ──► T-008
T-008 ──► T-009 ──► T-010 ──┐
                    └──► T-011 ──┴──► T-012
T-001 a T-008 + T-013 ──► T-014
T-009 a T-012 ──► T-015
T-014 + T-015 ──► T-016
```

T-001 crea la base de persistencia. T-003 puede avanzar en paralelo con T-002 después de T-001. T-013 prepara el límite de subida y valida las imágenes. T-004 y T-005 pueden ejecutarse en paralelo una vez listo T-003. T-006 integra el pipeline. T-007 y T-008 completan la API de pendientes. T-009 a T-012 implementan el frontend. T-014 y T-015 consolidan las pruebas; T-016 cierra la especificación.

Las decisiones D-001 a D-012 de `spec.md` y el plan están aprobados. La implementación avanza por tareas.

## Tareas

- [x] **T-001 — Crear el modelo y la migración de importaciones**
  - Requisitos: FR-006, NFR-001, NFR-002.
  - Dependencias: ninguna.
  - Descripción: crear los modelos SQLAlchemy `ImportBatch` y `ImportRow` con tablas `lotes_importacion` y `filas_importacion`; atributos internos en inglés y columnas en español. Incluir estados, errores, datos originales, huella, referencias a movimientos, constraints e índices. Crear la migración `0004_create_import_tables` con `upgrade` y `downgrade`. Exportar los modelos en `app/db/models/__init__.py`.
  - Hecho cuando: la migración aplica y revierte en la base de test; los constraints e índices existen; no se usa `create_all`; ruff y pruebas unitarias pasan.
  - Evidencia (2026-10-29): creados `ImportBatch`, `ImportFileType`, `ImportMovementType`, `ImportRow` e `ImportRowStatus`; tablas `lotes_importacion` y `filas_importacion` con checks, FKs e índices; migración `0004_create_import_tables` aplicada, revertida a `0003` y reaplicada en la base de test; 135/135 pruebas pasan; ruff y format pasan.
  - Verificación:
    ```bash
    docker compose exec api uv run alembic upgrade head
    docker compose exec api uv run pytest tests/api
    cd backend
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-002 — Añadir la categoría opcional de ingresos**
  - Requisitos: FR-004, NFR-008; decisión D-002.
  - Dependencias: T-001.
  - Descripción: según D-002 aprobada, añadir `categoria` nullable a `ingresos`, migración `0005_add_income_category`, schemas Pydantic de ingresos, respuesta de lectura, formulario y listado de ingresos. Mantener compatibilidad con clientes que no envían el campo. El campo es opcional y no se exige para crear ni editar ingresos.
  - Hecho cuando: la migración aplica y revierte; `POST`/`PUT` aceptan categoría opcional; `GET` la devuelve; el formulario y listado la manejan; las pruebas existentes de ingresos siguen pasando.
  - Evidencia (2026-10-29): `ingresos.categoria` añadida como `VARCHAR(100)` nullable; migración `0005_add_income_category` aplicada, revertida a `0004` y reaplicada; schemas y rutas aceptan/devuelven categoría opcional; formulario y listado de ingresos la muestran y editan; categoría vacía se normaliza a `null`. Backend: 139/139 pruebas; frontend: 51/51, lint, typecheck y build. Ruff y format pasan.
  - Verificación:
    ```bash
    docker compose exec api uv run pytest tests/api tests/integration
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [x] **T-003 — Implementar normalización, validación y huellas**
  - Requisitos: FR-002, FR-003, FR-004, FR-014, NFR-001.
  - Dependencias: T-001.
  - Descripción: crear utilidades del backend para normalizar cabeceras (sin acentos, minúsculas, alias), normalizar descripciones y categorías, parsear fechas y valores a `Decimal`, validar filas y calcular la huella SHA-256. Definir la estructura de errores por campo. Cubrir formatos y límites con pruebas unitarias.
  - Hecho cuando: alias de cabecera, fechas, valores y categorías se normalizan; los errores son deterministas; la huella es estable; no se usa `float`; pruebas unitarias pasan.
  - Evidencia (2026-10-29): creados `app/services/imports/{errors,normalization,validation}.py`; alias de cabecera, fechas ISO y `DD/MM/YYYY`, importes con punto/coma, categorías de gasto, categoría opcional de ingreso, errores por campo y huella SHA-256 estable. 59 pruebas de `tests/core`; 193/193 pruebas de backend en Docker; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core tests/api
    uv run ruff check .
    ```

- [x] **T-004 — Implementar el parser CSV**
  - Requisitos: FR-001, FR-002, FR-003, FR-015, FR-016.
  - Dependencias: T-003.
  - Descripción: parsear CSV con `utf-8-sig`, detectar delimitador coma/punto y coma, validar cabeceras, conservar números de fila, omitir filas vacías y rechazar archivos vacíos, codificaciones no soportadas o cabeceras faltantes. No leer el archivo completo sin límite.
  - Hecho cuando: CSV válidos producen filas normalizadas; archivos inválidos producen errores de archivo; se respetan límites; pruebas unitarias pasan.
  - Evidencia (2026-10-29): creado `app/services/imports/csv_parser.py`; soporta UTF-8 con BOM, delimitadores coma/punto y coma, alias de cabecera, filas vacías, números de fila originales y límites de tamaño/filas. 73 pruebas core; 207/207 pruebas backend en Docker; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core
    uv run ruff check .
    ```

- [x] **T-005 — Implementar el parser XLSX**
  - Requisitos: FR-001, FR-002, FR-003, FR-015, FR-016.
  - Dependencias: T-003.
  - Descripción: usar `openpyxl` para leer la primera hoja en modo `read_only` y `data_only`, validar extensión y contenido, convertir fechas y números a tipos internos, omitir filas vacías y rechazar libros vacíos o con estructura inválida. No ejecutar macros ni fórmulas.
  - Hecho cuando: XLSX válidos producen filas normalizadas; archivos inválidos se rechazan; no se usan `float` para cálculos; pruebas unitarias pasan.
  - Evidencia (2026-10-29): creado `app/services/imports/xlsx_parser.py`; añadido `openpyxl` 3.1.5; lee la primera hoja en `read_only`/`data_only`, conserva fechas y números, omite filas vacías y aplica límites. 73 pruebas core; 207/207 pruebas backend en Docker; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core
    uv run ruff check .
    ```

- [x] **T-006 — Implementar el servicio de importación y el endpoint de carga**
  - Requisitos: FR-001, FR-005, FR-007, FR-014, FR-015; NFR-002.
  - Dependencias: T-001, T-002, T-003, T-004, T-005.
  - Descripción: añadir `python-multipart`, crear schemas de lote y fila, implementar el servicio que valida el archivo, clasifica filas, detecta duplicados, crea el lote y los movimientos completos en una transacción, y expone `POST /api/importaciones`. Añadir límites de tamaño, filas, extensión y MIME.
  - Hecho cuando: CSV y XLSX válidos crean lote y movimientos; filas inválidas quedan pendientes; un fallo de base de datos revierte todo; respuestas `413`/`415`/`422` son claras; no se registran datos sensibles.
  - Evidencia (2026-10-29): creado `app/services/imports/importer.py` y `POST /api/importaciones`; soporta CSV/XLSX, límites, MIME/extensión, validación por fila, contabilización transaccional, pendientes y detección de duplicados. `python-multipart` añadido; 9 pruebas de API y 216/216 backend en Docker; ruff y format pasan.
  - Verificación:
    ```bash
    docker compose exec api uv run pytest tests/api tests/integration
    curl -F 'archivo=@archivo.csv' -F 'tipo_movimiento=GASTO' \
      http://localhost:8000/api/importaciones
    ```

- [x] **T-007 — Implementar listado y conteo de pendientes**
  - Requisitos: FR-008, FR-012, NFR-008.
  - Dependencias: T-006.
  - Descripción: crear los schemas de pendientes y los endpoints `GET /api/importaciones/pendientes` y `GET /api/importaciones/pendientes/count`. Listar solo estado `PENDIENTE`, ordenar por lote y fila, y calcular el conteo desde PostgreSQL. Declarar la ruta `count` antes de la ruta con identificador.
  - Hecho cuando: los pendientes se listan con errores y datos disponibles; el conteo coincide con la base; no se incluyen importados ni descartados; pruebas de API pasan.
  - Evidencia (2026-10-29): creados `ImportPendingRowRead`, `ImportPendingCountRead` y los endpoints de listado y conteo; se listan solo pendientes ordenados por lote/fila y el conteo se obtiene de PostgreSQL. 16 pruebas de importación y 224/224 backend en Docker; ruff y format pasan.
  - Verificación:
    ```bash
    docker compose exec api uv run pytest tests/api
    curl http://localhost:8000/api/importaciones/pendientes
    curl http://localhost:8000/api/importaciones/pendientes/count
    ```

- [x] **T-008 — Implementar actualización, contabilización y descarte**
  - Requisitos: FR-009, FR-010, FR-011, FR-013, NFR-002.
  - Dependencias: T-006, T-007.
  - Descripción: implementar `PUT /api/importaciones/pendientes/{id}`, `POST /api/importaciones/pendientes/{id}/contabilizar` y `DELETE /api/importaciones/pendientes/{id}`. Revalidar en servidor, bloquear la fila, crear el movimiento y actualizar la referencia en una transacción, y aplicar descarte lógico. Devolver `404`, `409` y `422` correctamente.
  - Hecho cuando: un pendiente se corrige, contabiliza una sola vez y se descarta; la segunda contabilización devuelve `409`; una fila inválida devuelve `422`; el resumen solo cambia al contabilizar.
  - Evidencia (2026-10-29): implementados `PUT`, `POST /contabilizar` y `DELETE`; revalidación en servidor, bloqueo de fila, contabilización transaccional, descarte lógico y actualización de contadores del lote. Se permite elegir `tipo_gasto` cuando la categoría es desconocida. 16 pruebas de importación y 224/224 backend en Docker; ruff y format pasan.
  - Verificación:
    ```bash
    docker compose exec api uv run pytest tests/api tests/integration
    curl -X POST http://localhost:8000/api/importaciones/pendientes/1/contabilizar
    ```

- [ ] **T-009 — Crear tipos y cliente API del frontend**
  - Requisitos: FR-017, NFR-008.
  - Dependencias: T-006, T-007, T-008.
  - Descripción: crear `types/import.ts` y `api/imports.ts` con tipos de lote, pendiente, errores, conteo y respuestas; funciones `uploadImport`, `listPending`, `countPending`, `updatePending`, `commitPending` y `discardPending`. Usar `request` y rutas relativas `/api`. Añadir pruebas del cliente con `fetch` simulado.
  - Hecho cuando: los tipos reflejan el contrato; cada función usa método, ruta y cuerpo correctos; `204` se maneja sin parsear JSON; pruebas del cliente pasan.
  - Evidencia (pendiente):
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [ ] **T-010 — Crear la vista de importación**
  - Requisitos: FR-001, FR-017.
  - Dependencias: T-009.
  - Descripción: crear `ImportView` con selector de archivo, tipo ingreso/gasto, estado de carga, resumen del lote y errores accesibles. Aceptar solo `.csv` y `.xlsx`. Tras importar, notificar al contenedor para refrescar el resumen, las listas y el conteo. Incluir estado vacío y errores de red.
  - Hecho cuando: el usuario puede seleccionar y enviar un archivo; el resultado muestra importados y pendientes; los errores se muestran en español; la vista es accesible y responsive.
  - Evidencia (pendiente):
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [ ] **T-011 — Crear la vista de pendientes**
  - Requisitos: FR-008, FR-009, FR-010, FR-011, FR-017.
  - Dependencias: T-009.
  - Descripción: crear `PendingView` con listado, campos editables, errores por campo, guardado, contabilización con confirmación cuando aplique y descarte con confirmación. Deshabilitar contabilizar mientras haya errores. Mostrar estado vacío y refrescar conteo/resumen.
  - Hecho cuando: un pendiente se corrige, guarda, contabiliza o descarta desde la UI; los errores son visibles; la tabla es responsive; pruebas de componentes pasan.
  - Evidencia (pendiente):
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [ ] **T-012 — Integrar navegación, badge y refresco en App**
  - Requisitos: FR-012, FR-017.
  - Dependencias: T-010, T-011.
  - Descripción: añadir a `App` la navegación local entre principal, importación y pendientes; cargar el conteo de pendientes; mostrar botón `Importar` y `Pendientes` con indicador accesible; refrescar resumen, listas y conteo tras importar, contabilizar o descartar. Mantener las pestañas existentes.
  - Hecho cuando: se navega entre vistas sin router; el badge aparece solo con pendientes; se actualiza tras cada operación; las pruebas de App pasan; no se rompen ingresos, gastos ni resumen.
  - Evidencia (pendiente):
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [ ] **T-013 — Configurar el límite de subida y validar las dependencias**
  - Requisitos: FR-016, NFR-004, NFR-009.
  - Dependencias: T-001.
  - Descripción: añadir `client_max_body_size 12m` en `docker/nginx.conf`; `python-multipart` y `openpyxl` ya quedaron incorporados en T-006/T-005. Reconstruir las imágenes de desarrollo y producción y verificar que las dependencias están disponibles en runtime.
  - Hecho cuando: las dependencias están en producción; el lock está actualizado; Nginx acepta el tamaño previsto; el backend rechaza archivos que superan su límite; las imágenes construyen.
  - Evidencia (pendiente):
  - Verificación:
    ```bash
    cd backend
    uv lock
    docker build -f docker/Dockerfile.api --target prod -t py-personal-finance-api-prod .
    docker build -f docker/Dockerfile.web -t py-personal-finance-web-prod .
    docker compose build api
    ```

- [ ] **T-014 — Completar pruebas de backend y OpenAPI**
  - Requisitos: FR-001 a FR-016, NFR-001 a NFR-010.
  - Dependencias: T-001 a T-008, T-013.
  - Descripción: añadir pruebas unitarias de parsers, normalización, validación y huellas; pruebas de API para carga, pendientes, actualización, contabilización, descarte y errores; pruebas de integración para persistencia, aislamiento del resumen, transacciones, duplicados y concurrencia; pruebas de rutas en OpenAPI. Verificar migraciones upgrade/downgrade en la base de test.
  - Hecho cuando: todos los casos de la matriz están cubiertos; las pruebas de integración pasan contra PostgreSQL; el resumen no incluye pendientes; OpenAPI incluye las rutas nuevas.
  - Evidencia (pendiente):
  - Verificación:
    ```bash
    cd backend
    uv run ruff check .
    uv run ruff format --check .
    uv run pytest
    docker compose exec api uv run pytest
    docker compose exec api uv run alembic current
    ```

- [ ] **T-015 — Completar pruebas de frontend**
  - Requisitos: FR-012, FR-017, NFR-005, NFR-008.
  - Dependencias: T-009 a T-012.
  - Descripción: cubrir cliente API, `ImportView`, `PendingView`, badge, navegación de App, estados de carga/error/vacío, accesibilidad y formato COP. Verificar que las pruebas existentes de ingresos y gastos siguen pasando.
  - Hecho cuando: las pruebas cubren el flujo importar → pendientes → corregir → contabilizar/descartar; lint, typecheck, test y build pasan.
  - Evidencia (pendiente):
  - Verificación:
    ```bash
    cd frontend
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```

- [ ] **T-016 — Documentar y validar la especificación**
  - Requisitos: AC-001 a AC-016, NFR-010.
  - Dependencias: T-014, T-015.
  - Descripción: actualizar README con el contrato de importación una vez implementado, actualizar AGENTS y `specs/README.md`, registrar la evidencia de aceptación, verificar los límites y el comportamiento de producción, y marcar la especificación como validada.
  - Hecho cuando: los AC están cubiertos con evidencia; la documentación coincide con la implementación; no hay regresiones; la especificación queda validada.
  - Evidencia (pendiente):
  - Verificación:
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml config -q
    WEB_PORT=3001 ./scripts/smoke.sh
    git diff --check
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-006, T-010, T-013, T-014 |
| FR-002 | T-003, T-004, T-005, T-006 |
| FR-003 | T-003, T-004, T-005, T-014 |
| FR-004 | T-002, T-003, T-006 |
| FR-005 | T-006, T-014 |
| FR-006 | T-001, T-006, T-014 |
| FR-007 | T-006, T-014 |
| FR-008 | T-007, T-011, T-012 |
| FR-009 | T-008, T-011 |
| FR-010 | T-008, T-011 |
| FR-011 | T-008, T-011 |
| FR-012 | T-007, T-012, T-015 |
| FR-013 | T-008, T-014 |
| FR-014 | T-003, T-006, T-014 |
| FR-015 | T-004, T-005, T-006, T-014 |
| FR-016 | T-006, T-013, T-014 |
| FR-017 | T-010, T-011, T-012, T-015 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001, T-003, T-014 |
| NFR-002 | T-001, T-006, T-008, T-014 |
| NFR-003 | T-006, T-013, T-014 |
| NFR-004 | T-006, T-013, T-014 |
| NFR-005 | T-010, T-011, T-012, T-015 |
| NFR-006 | T-001 a T-016 |
| NFR-007 | T-006, T-008, T-014 |
| NFR-008 | T-002, T-009, T-014 |
| NFR-009 | T-013 |
| NFR-010 | T-014, T-015, T-016 |

## Evidencia de validación

Se completa durante T-016.

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
| AC-015 | Pendiente | |
| AC-016 | Pendiente | |

## Notas

- No se implementa nada en esta etapa; todos los checkboxes quedan pendientes.
- No se modifica `legacy/`.
- No se modifican las especificaciones 001 a 006.
- `openpyxl` y `python-multipart` ya se incorporaron; T-013 queda para el límite de Nginx y la validación de imágenes.
- La importación usa tablas de staging separadas de `ingresos` y `gastos`.
- Los pendientes no participan en el resumen.
- La decisión D-002 está aprobada: T-002 incluye una categoría opcional de ingresos.
- La decisión D-001 está aprobada: un archivo contiene un solo tipo de movimiento seleccionado por el usuario.
- La decisión D-005 está aprobada: los duplicados quedan pendientes y el usuario decide si contabiliza o descarta.
- La decisión D-006 está aprobada: se permite guardar pendientes parcialmente inválidos.
- La decisión D-007 está aprobada: el descarte es lógico y conserva la fila con estado `DESCARTADO`.
- La decisión D-012 está aprobada: el historial de importaciones queda fuera de alcance; su visión futura está documentada en `spec.md`.
- No se declara la especificación validada hasta ejecutar T-016.
