# Tareas 007 — Importación de ingresos y gastos desde Excel y CSV

- Estado: validada (revisión 3).
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
T-014 + T-015 ──► T-016 ──► T-017 ──► T-018 ──► T-019 ──► T-020 ──► T-021
```

T-001 crea la base de persistencia. T-003 puede avanzar en paralelo con T-002 después de T-001. T-013 prepara el límite de subida y valida las imágenes. T-004 y T-005 pueden ejecutarse en paralelo una vez listo T-003. T-006 integra el pipeline. T-007 y T-008 completan la API de pendientes. T-009 a T-012 implementan el frontend. T-014 y T-015 consolidan las pruebas; T-016 cerró la versión inicial. La revisión 2 se ejecutó en T-017 a T-020: semántica de categoría, descarte masivo, UI y revalidación. La revisión 3 se ejecutó en T-021: eliminación de movimientos importados.

Las decisiones D-001 a D-013 de `spec.md` y el plan están aprobados. Las revisiones 2 y 3 están validadas.

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

- [x] **T-009 — Crear tipos y cliente API del frontend**
  - Requisitos: FR-017, NFR-008.
  - Dependencias: T-006, T-007, T-008.
  - Descripción: crear `types/import.ts` y `api/imports.ts` con tipos de lote, pendiente, errores, conteo y respuestas; funciones `uploadImport`, `listPending`, `countPending`, `updatePending`, `commitPending` y `discardPending`. Usar `request` y rutas relativas `/api`. Añadir pruebas del cliente con `fetch` simulado.
  - Hecho cuando: los tipos reflejan el contrato; cada función usa método, ruta y cuerpo correctos; `204` se maneja sin parsear JSON; pruebas del cliente pasan.
  - Evidencia (2026-10-29): creados `types/import.ts` y `api/imports.ts`; carga multipart, listado, conteo, actualización, contabilización y descarte con rutas relativas. 6 pruebas nuevas de cliente; 57/57 pruebas de frontend, lint, typecheck y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [x] **T-010 — Crear la vista de importación**
  - Requisitos: FR-001, FR-017.
  - Dependencias: T-009.
  - Descripción: crear `ImportView` con selector de archivo, tipo ingreso/gasto, estado de carga, resumen del lote y errores accesibles. Aceptar solo `.csv` y `.xlsx`. Tras importar, notificar al contenedor para refrescar el resumen, las listas y el conteo. Incluir estado vacío y errores de red.
  - Hecho cuando: el usuario puede seleccionar y enviar un archivo; el resultado muestra importados y pendientes; los errores se muestran en español; la vista es accesible y responsive.
  - Evidencia (2026-10-29): creados `ImportView` y sus estilos; selector de archivo y tipo, estado de envío, resumen del lote, errores por estado HTTP, aviso de pendientes y botón de regreso. 4 pruebas de componente; 61/61 frontend, lint, typecheck y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-011 — Crear la vista de pendientes**
  - Requisitos: FR-008, FR-009, FR-010, FR-011, FR-017.
  - Dependencias: T-009.
  - Descripción: crear `PendingView` con listado, campos editables, errores por campo, guardado, contabilización con confirmación cuando aplique y descarte con confirmación. Deshabilitar contabilizar mientras haya errores. Mostrar estado vacío y refrescar conteo/resumen.
  - Hecho cuando: un pendiente se corrige, guarda, contabiliza o descarta desde la UI; los errores son visibles; la tabla es responsive; pruebas de componentes pasan.
  - Evidencia (2026-10-29): creados `PendingView` y sus estilos; listado responsive, errores por fila, edición de fecha/descripción/valor/categoría/tipo, guardado, contabilización y descarte con confirmación. 5 pruebas de componente; 66/66 frontend, lint, typecheck y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-012 — Integrar navegación, badge y refresco en App**
  - Requisitos: FR-012, FR-017.
  - Dependencias: T-010, T-011.
  - Descripción: añadir a `App` la navegación local entre principal, importación y pendientes; cargar el conteo de pendientes; mostrar botón `Importar` y `Pendientes` con indicador accesible; refrescar resumen, listas y conteo tras importar, contabilizar o descartar. Mantener las pestañas existentes.
  - Hecho cuando: se navega entre vistas sin router; el badge aparece solo con pendientes; se actualiza tras cada operación; las pruebas de App pasan; no se rompen ingresos, gastos ni resumen.
  - Evidencia (2026-10-29): `App` integra vistas principal, importación y pendientes; carga el conteo desde el backend; muestra badge accesible y lo oculta en cero; refresca datos y conteo tras importar, contabilizar o descartar. 68/68 frontend, lint, typecheck y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-013 — Configurar el límite de subida y validar las dependencias**
  - Requisitos: FR-016, NFR-004, NFR-009.
  - Dependencias: T-001.
  - Descripción: añadir `client_max_body_size 12m` en `docker/nginx.conf`; `python-multipart` y `openpyxl` ya quedaron incorporados en T-006/T-005. Reconstruir las imágenes de desarrollo y producción y verificar que las dependencias están disponibles en runtime.
  - Hecho cuando: las dependencias están en producción; el lock está actualizado; Nginx acepta el tamaño previsto; el backend rechaza archivos que superan su límite; las imágenes construyen.
  - Evidencia (2026-10-29): `client_max_body_size 12m` añadido a Nginx; `nginx -t` pasa; imágenes dev y prod reconstruidas; la imagen prod importa `python-multipart 0.0.32` y `openpyxl 3.1.5`; prueba unitaria confirma `413` para contenido por encima del límite. 225/225 backend en Docker; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv lock
    docker build -f docker/Dockerfile.api --target prod -t py-personal-finance-api-prod .
    docker build -f docker/Dockerfile.web -t py-personal-finance-web-prod .
    docker compose build api
    ```

- [x] **T-014 — Completar pruebas de backend y OpenAPI**
  - Requisitos: FR-001 a FR-016, NFR-001 a NFR-010.
  - Dependencias: T-001 a T-008, T-013.
  - Descripción: añadir pruebas unitarias de parsers, normalización, validación y huellas; pruebas de API para carga, pendientes, actualización, contabilización, descarte y errores; pruebas de integración para persistencia, aislamiento del resumen, transacciones, duplicados y concurrencia; pruebas de rutas en OpenAPI. Verificar migraciones upgrade/downgrade en la base de test.
  - Hecho cuando: todos los casos de la matriz están cubiertos; las pruebas de integración pasan contra PostgreSQL; el resumen no incluye pendientes; OpenAPI incluye las rutas nuevas.
  - Evidencia (2026-10-29): añadidas pruebas de rutas OpenAPI, importación con solo pendientes sin impacto en resumen y duplicados dentro del mismo archivo con contadores de lote. Verificado ciclo Alembic `0005 → 0004 → 0005`. 228/228 backend en Docker; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv run ruff check .
    uv run ruff format --check .
    uv run pytest
    docker compose exec api uv run pytest
    docker compose exec api uv run alembic current
    ```

- [x] **T-015 — Completar pruebas de frontend**
  - Requisitos: FR-012, FR-017, NFR-005, NFR-008.
  - Dependencias: T-009 a T-012.
  - Descripción: cubrir cliente API, `ImportView`, `PendingView`, badge, navegación de App, estados de carga/error/vacío, accesibilidad y formato COP. Verificar que las pruebas existentes de ingresos y gastos siguen pasando.
  - Hecho cuando: las pruebas cubren el flujo importar → pendientes → corregir → contabilizar/descartar; lint, typecheck, test y build pasan.
  - Evidencia (2026-10-29): ampliadas las pruebas de `ImportView` con errores 413/422 y estado de importación, y de `PendingView` con confirmación de posible duplicado. 72/72 frontend; lint, typecheck y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```

- [x] **T-016 — Documentar y validar la especificación**
  - Requisitos: AC-001 a AC-016, NFR-010.
  - Dependencias: T-014, T-015.
  - Descripción: actualizar README con el contrato de importación una vez implementado, actualizar AGENTS y `specs/README.md`, registrar la evidencia de aceptación, verificar los límites y el comportamiento de producción, y marcar la especificación como validada.
  - Hecho cuando: los AC están cubiertos con evidencia; la documentación coincide con la implementación; no hay regresiones; la especificación queda validada.
  - Evidencia (2026-10-29): README, AGENTS y `specs/README.md` actualizados con el contrato de importación y el estado validado. Producción reconstruida; migraciones `0004` y `0005` aplicadas; `api`, `db` y `web` healthy; smoke OK; `/api/importaciones/pendientes/count` responde cero; archivo vacío devuelve `422`; archivo de 13 MiB devuelve `413` en Nginx. Backend 228/228 y frontend 72/72; ruff, format, lint, typecheck y build pasan.
  - Verificación:
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml config -q
    WEB_PORT=3001 ./scripts/smoke.sh
    git diff --check
    ```

- [x] **T-017 — Alinear Categoría de gastos con Tipo de gasto**
  - Requisitos: FR-004, FR-009, AC-018.
  - Dependencias: T-006, T-008.
  - Descripción: para gastos, tratar `Categoría` como alias de `Tipo de gasto`; añadir alias de cabecera, emitir errores con campo `tipo_gasto` y hacer que la actualización de gastos use solo `tipo_gasto`. Mantener `categoria` como dato original de auditoría y conservar la categoría opcional de ingresos.
  - Hecho cuando: un gasto con `Categoría` válida se normaliza a `tipo_gasto`; un tipo desconocido queda pendiente con error `tipo_gasto`; la actualización de un gasto no requiere una categoría libre; las pruebas de ingresos siguen pasando.
  - Evidencia (2026-10-31): `Tipo de gasto` y `Categoría` comparten la columna canónica; los errores de gasto usan `tipo_gasto`; el valor original se conserva en `filas_importacion.categoria`. 230/230 pruebas de backend; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core tests/integration
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-018 — Implementar el descarte masivo global de pendientes**
  - Requisitos: FR-011, NFR-002, AC-017.
  - Dependencias: T-007, T-008.
  - Descripción: añadir `DELETE /api/importaciones/pendientes` para descartar lógicamente todos los pendientes en una transacción, devolver el número de descartados y recalcular los contadores de todos los lotes afectados. Añadir el schema de respuesta.
  - Hecho cuando: todos los pendientes pasan a `DESCARTADO`; el conteo global queda en cero; los contadores de los lotes son correctos; no se crean ni eliminan movimientos; `DELETE` es idempotente y devuelve `0` si no hay pendientes.
  - Evidencia (2026-10-31): endpoint `DELETE /api/importaciones/pendientes` con respuesta `{"descartados": n}`; prueba de integración con dos lotes verifica estados, contadores, resumen y segunda llamada idempotente. OpenAPI actualizado.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api tests/integration
    uv run ruff check .
    ```

- [x] **T-019 — Ajustar la UI de pendientes y añadir Descartar todo**
  - Requisitos: FR-009, FR-011, FR-017, AC-017, AC-018.
  - Dependencias: T-017, T-018, T-009, T-010, T-011, T-012.
  - Descripción: en gastos, mostrar solo `Tipo de gasto` y ocultar `Categoría`; en ingresos, mantener `Categoría`. Añadir el botón `Descartar todo` con confirmación, conteo de pendientes, estado deshabilitado y refresco de lista, badge y resumen. Añadir `discardAllPending` al cliente API.
  - Hecho cuando: la UI de gastos no muestra dos campos de categoría; `Descartar todo` descarta globalmente tras confirmar; cancelar no envía la petición; la lista, el badge y el resumen se actualizan; pruebas de componentes pasan.
  - Evidencia (2026-10-31): `PendingView` muestra `Categoría` solo para ingresos y `Tipo de gasto` solo para gastos; `Descartar todo` confirma, llama al endpoint, limpia la lista y refresca. 77/77 pruebas de frontend; lint, typecheck y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-020 — Revalidar la especificación 007**
  - Requisitos: AC-017, AC-018, NFR-010.
  - Dependencias: T-017, T-018, T-019.
  - Descripción: actualizar README/AGENTS/`specs/README.md` con la semántica corregida y el descarte masivo, completar la evidencia, ejecutar pruebas backend/frontend y validar la entrega de producción.
  - Hecho cuando: AC-017 y AC-018 tienen evidencia; la documentación refleja el comportamiento real; backend y frontend pasan; producción se reconstruye y el smoke test pasa; la especificación queda validada de nuevo.
  - Evidencia (2026-10-31): README, AGENTS y `specs/README.md` actualizados; backend 230/230 y frontend 77/77; producción reconstruida sin migraciones nuevas; smoke test OK y conteo de pendientes verificado.
  - Verificación:
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml config -q
    WEB_PORT=3001 ./scripts/smoke.sh
    (cd frontend && npm run lint && npm run typecheck && npm run test && npm run build)
    (cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest)
    docker compose exec api uv run pytest
    ```

- [x] **T-021 — Corregir la eliminación de movimientos importados**
  - Requisitos: AC-019, D-008.
  - Dependencias: T-001, T-006, T-008, T-014.
  - Descripción: añadir la migración `0006_allow_imported_without_movement` para relajar `ck_filas_importacion_referencia_movimiento`, actualizar la restricción en `ImportRow.__table_args__`, actualizar la versión esperada de Alembic en las pruebas y cubrir la eliminación de gastos e ingresos importados. La fila de importación debe conservar `estado = 'IMPORTADO'` y la referencia nula, sin reencolarse; el resumen debe reflejar la eliminación del movimiento.
  - Hecho cuando: eliminar un gasto o ingreso importado devuelve `204`; el movimiento desaparece; la fila de importación queda `IMPORTADO` con referencia nula; los contadores del lote no cambian; las eliminaciones manuales siguen funcionando; la migración `0006` se aplica y su downgrade funciona en una base sin filas huérfanas.
  - Evidencia (2026-10-31): migración `0006_allow_imported_without_movement` aplicada; restricción relajada; pruebas de eliminación de gastos e ingresos importados verifican `204`, fila `IMPORTADO`, referencia nula y contadores del lote. 232/232 pruebas de backend; ciclo Alembic `0006 → 0005 → 0006`; producción reconstruida y smoke OK.
  - Verificación:
    ```bash
    cd backend
    uv run ruff check .
    uv run ruff format --check .
    uv run --env-file ../.env pytest
    uv run --env-file ../.env alembic upgrade head
    ```
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml up --build -d
    WEB_PORT=3001 ./scripts/smoke.sh
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-006, T-010, T-013, T-014 |
| FR-002 | T-003, T-004, T-005, T-006 |
| FR-003 | T-003, T-004, T-005, T-014 |
| FR-004 | T-002, T-003, T-006, T-017 |
| FR-005 | T-006, T-014 |
| FR-006 | T-001, T-006, T-014 |
| FR-007 | T-006, T-014 |
| FR-008 | T-007, T-011, T-012 |
| FR-009 | T-008, T-011, T-017, T-019 |
| FR-010 | T-008, T-011 |
| FR-011 | T-008, T-011, T-018, T-019 |
| FR-012 | T-007, T-012, T-015 |
| FR-013 | T-008, T-014 |
| FR-014 | T-003, T-006, T-014 |
| FR-015 | T-004, T-005, T-006, T-014 |
| FR-016 | T-006, T-013, T-014 |
| FR-017 | T-010, T-011, T-012, T-015, T-019 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001, T-003, T-014 |
| NFR-002 | T-001, T-006, T-008, T-014, T-018 |
| NFR-003 | T-006, T-013, T-014 |
| NFR-004 | T-006, T-013, T-014 |
| NFR-005 | T-010, T-011, T-012, T-015 |
| NFR-006 | T-001 a T-021 |
| NFR-007 | T-006, T-008, T-014, T-021 |
| NFR-008 | T-002, T-009, T-014 |
| NFR-009 | T-013 |
| NFR-010 | T-014, T-015, T-016, T-020, T-021 |

## Evidencia de validación

Validada durante T-016, T-020 y T-021.

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumple | Pruebas de importación CSV de ingresos. |
| AC-002 | Cumple | Prueba de importación XLSX de gastos. |
| AC-003 | Cumple | Pruebas de alias y normalización de cabeceras. |
| AC-004 | Cumple | Pruebas de importación parcial con pendientes. |
| AC-005 | Cumple | Persistencia de filas en PostgreSQL y pruebas de integración. |
| AC-006 | Cumple | Pruebas de actualización y contabilización. |
| AC-007 | Cumple | Pruebas de descarte sin movimientos. |
| AC-008 | Cumple | Pruebas de conteo y badge en App. |
| AC-009 | Cumple | Pruebas de duplicados dentro y entre archivos. |
| AC-010 | Cumple | Pruebas de archivos vacíos, extensión y cabeceras. |
| AC-011 | Cumple | Límites de filas, servicio `413` y Nginx `413`. |
| AC-012 | Cumple | Prueba de segunda contabilización `409`. |
| AC-013 | Cumple | Pruebas de resumen con pendientes. |
| AC-014 | Cumple | Pruebas de componentes, accesibilidad y CSS responsive. |
| AC-015 | Cumple | Backend 232/232 y frontend 77/77; calidad completa. |
| AC-016 | Cumple | README, AGENTS y `specs/README.md` actualizados. |
| AC-017 | Cumple | Prueba de descarte masivo global y prueba de componente con confirmación. |
| AC-018 | Cumple | Pruebas de alias de cabecera, errores `tipo_gasto` y campos condicionales en la UI. |
| AC-019 | Cumple | Pruebas de eliminación de gastos e ingresos importados; la fila conserva `IMPORTADO` y la referencia nula. |

## Notas

- La versión inicial se implementó y validó; T-017 a T-020 completan la revisión 2; T-021 completa la revisión 3.
- No se modifica `legacy/`.
- No se modifican las especificaciones 001 a 006.
- `openpyxl` y `python-multipart` están incorporados; T-013 completó el límite de Nginx y la validación de imágenes.
- La importación usa tablas de staging separadas de `ingresos` y `gastos`.
- Los pendientes no participan en el resumen.
- La decisión D-002 está aprobada: T-002 incluye una categoría opcional de ingresos.
- La decisión D-001 está aprobada: un archivo contiene un solo tipo de movimiento seleccionado por el usuario.
- La decisión D-005 está aprobada: los duplicados quedan pendientes y el usuario decide si contabiliza o descarta.
- La decisión D-006 está aprobada: se permite guardar pendientes parcialmente inválidos.
- La decisión D-007 está aprobada: el descarte es lógico y conserva la fila con estado `DESCARTADO`.
- La decisión D-012 está aprobada: el historial de importaciones queda fuera de alcance; su visión futura está documentada en `spec.md`.
- La versión inicial quedó validada en T-016; la revisión 2 quedó validada en T-020; la revisión 3 quedó validada en T-021.
