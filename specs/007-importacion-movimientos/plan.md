# Plan técnico 007 — Importación de ingresos y gastos desde Excel y CSV

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Fase: 5.
- Iteración: MVP+.

## 1. Resumen de la solución

Se añade un flujo de importación en dos fases:

1. **Carga y clasificación:** el usuario sube un archivo CSV o XLSX, indica si contiene ingresos o gastos, y el backend lo parsea, valida y clasifica fila por fila.
2. **Revisión y contabilización:** las filas completas se incorporan a la contabilidad; las incompletas, inválidas o posiblemente duplicadas se guardan como pendientes para corrección, contabilización o descarte.

La pieza central es una tabla de staging persistente:

```text
Archivo
  │
  ▼
Parser CSV/XLSX
  │
  ▼
Normalización y validación
  │
  ├── fila completa ──► ingresos / gastos
  │                         │
  │                         └── referencia al movimiento
  │
  └── fila incompleta ──► filas_importacion (PENDIENTE)
                              │
                              ├── corregir
                              ├── contabilizar
                              └── descartar
```

Los pendientes viven en tablas distintas de `ingresos` y `gastos`; por tanto, no alteran el resumen. La interfaz muestra una pantalla de importación y otra de pendientes, con un indicador obtenido del backend.

El plan base incorpora las decisiones aprobadas D-001 a D-012 de la especificación.

## 2. Arquitectura y flujo de datos

```text
Navegador
   │  multipart/form-data
   ▼
Nginx
   │  /api/importaciones
   ▼
FastAPI
   │
   ├── valida archivo y límites
   ├── parsea CSV/XLSX
   ├── normaliza cabeceras y valores
   ├── valida cada fila
   ├── calcula huella de duplicados
   ├── abre una transacción
   │     ├── crea lote
   │     ├── inserta filas de importación
   │     ├── crea movimientos completos
   │     └── registra referencias
   └── devuelve resumen del lote
```

La bandeja de pendientes consulta `filas_importacion` con estado `PENDIENTE`. La contabilización manual crea un movimiento y actualiza la fila en la misma transacción.

## 3. Componentes y responsabilidades

### Backend

| Componente | Responsabilidad |
|---|---|
| `app/db/models/import_batch.py` | Lote de importación y sus contadores. |
| `app/db/models/import_row.py` | Fila de importación, estado, errores, huella y referencias. |
| `app/api/schemas/imports.py` | Contratos Pydantic de lotes, pendientes y actualización. |
| `app/api/routes/imports.py` | Endpoints de carga, pendientes, contabilización y descarte. |
| `app/services/imports/` | Parser CSV/XLSX, normalización, validación, huellas y transacciones. |
| `app/main.py` | Registro del router bajo `/api`. |
| `alembic/versions/0004_*.py` | Tablas de importación. |
| `alembic/versions/0005_*.py` | Categoría opcional de ingresos (D-002 aprobada). |

### Frontend

| Componente | Responsabilidad |
|---|---|
| `src/types/import.ts` | Tipos de lote, pendiente y errores. |
| `src/api/imports.ts` | Carga, listado, conteo, actualización, contabilización y descarte. |
| `src/components/ImportView.tsx` | Selector de archivo, tipo, envío y resultado. |
| `src/components/PendingView.tsx` | Bandeja, edición y acciones sobre pendientes. |
| `src/components/PendingBadge.tsx` | Indicador accesible de pendientes. |
| `src/App.tsx` | Navegación local entre vista principal, importación y pendientes. |
| `src/index.css` | Estilos nuevos reutilizando el sistema existente. |

No se introduce router, Context, Redux, Zustand, librería de formularios ni un servicio adicional.

## 4. Cambios en el modelo de datos

### 4.1 Tabla `lotes_importacion`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `Integer` PK | Autoincremental. |
| `nombre_archivo` | `String(255)` | Solo nombre base, sin ruta. |
| `tipo_archivo` | `String(10)` | `CSV` o `XLSX`. |
| `tipo_movimiento` | `String(10)` | `INGRESO` o `GASTO`. |
| `tamano_bytes` | `Integer` | Tamaño validado. |
| `total_filas` | `Integer` | Filas de datos no vacías. |
| `filas_importadas` | `Integer` | Movimientos creados. |
| `filas_pendientes` | `Integer` | Filas en estado pendiente. |
| `filas_descartadas` | `Integer` | Filas descartadas. |
| `created_at` | `DateTime(timezone=True)` | Fecha de creación. |

Constraint: contadores no negativos.

### 4.2 Tabla `filas_importacion`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `Integer` PK | Autoincremental. |
| `lote_id` | FK `lotes_importacion.id` | `ON DELETE CASCADE`. |
| `numero_fila` | `Integer` | Fila original del archivo, base 1. |
| `tipo_movimiento` | `String(10)` | `INGRESO` o `GASTO`. |
| `fecha` | `Date` nullable | Puede faltar o ser inválida. |
| `descripcion` | `String(200)` nullable | Texto recortado. |
| `valor` | `Numeric(12, 2)` nullable | Puede faltar o ser inválido. |
| `categoria` | `String(100)` nullable | Texto original o normalizado. |
| `tipo_gasto` | `String(20)` nullable | Tipo mapeado para gastos. |
| `estado` | `String(20)` | `PENDIENTE`, `IMPORTADO`, `DESCARTADO`. |
| `errores` | `JSONB` | Lista de `{campo, mensaje}`. |
| `datos_originales` | `JSONB` | Fila cruda para auditoría; no se registra en logs. |
| `huella` | `String(64)` | SHA-256 normalizado para duplicados. |
| `posible_duplicado` | `Boolean` | Advertencia. |
| `duplicado_de_id` | FK self nullable | Fila previa que originó la advertencia. |
| `movimiento_ingreso_id` | FK `ingresos.id` nullable | `ON DELETE SET NULL`. |
| `movimiento_gasto_id` | FK `gastos.id` nullable | `ON DELETE SET NULL`. |
| `created_at` | `DateTime(timezone=True)` | Auditoría. |
| `updated_at` | `DateTime(timezone=True)` | Auditoría. |

Restricciones e índices:

- `UniqueConstraint(lote_id, numero_fila)`.
- `CheckConstraint` para estados válidos.
- `CheckConstraint` para tipos de movimiento válidos.
- `CheckConstraint` para `tipo_gasto` válido o nulo.
- `CheckConstraint` que exige exactamente una referencia de movimiento cuando el estado es `IMPORTADO`, y ninguna cuando es `PENDIENTE` o `DESCARTADO`.
- Índices en `lote_id`, `estado` y `huella`.
- No se impone unicidad sobre `huella`, porque pueden existir duplicados legítimos.

### 4.3 Categoría de ingresos

Según D-002 aprobada:

- Añadir `categoria` nullable `String(100)` a `ingresos`.
- Añadir `categoria` opcional a `IncomeWrite`/`IncomeCreate`/`IncomeUpdate`/`IncomeRead`.
- Mostrar y editar la categoría en el formulario de ingresos.
- Mostrarla en el listado de ingresos.
- Mantener compatibilidad con clientes que no envían el campo.

La categoría de ingresos es opcional: no se exige al crear ni editar un ingreso.

### 4.4 Migraciones

- `0004_create_import_tables`: crea `lotes_importacion` y `filas_importacion`, constraints e índices.
- `0005_add_income_category`: añade `categoria` opcional a `ingresos` (D-002 aprobada).
- Ambas migraciones deben tener `upgrade` y `downgrade` funcionales.
- La suite de integración aplica Alembic a la base de test.
- No se modifica el esquema con `create_all`.

## 5. Contrato de API

Todos los campos externos van en español; el código interno en inglés.

### 5.1 `POST /api/importaciones`

Contenido: `multipart/form-data`.

| Campo | Tipo | Obligatorio | Nota |
|---|---|---|---|
| `archivo` | archivo | Sí | `.csv` o `.xlsx`. |
| `tipo_movimiento` | `INGRESO` / `GASTO` | Sí | Decisión D-001. |

Respuesta `201`:

```json
{
  "id": 1,
  "nombre_archivo": "movimientos.csv",
  "tipo_archivo": "CSV",
  "tipo_movimiento": "GASTO",
  "total_filas": 10,
  "filas_importadas": 7,
  "filas_pendientes": 3,
  "filas_descartadas": 0
}
```

Errores:

- `413`: archivo demasiado grande.
- `415`: extensión o tipo no permitido.
- `422`: archivo vacío, cabeceras faltantes, codificación no soportada, hoja vacía, demasiadas filas o error de parseo.
- `500`: error interno sin detalles técnicos.

### 5.2 `GET /api/importaciones/pendientes`

Respuesta `200`:

```json
[
  {
    "id": 12,
    "lote_id": 1,
    "numero_fila": 4,
    "tipo_movimiento": "GASTO",
    "fecha": null,
    "descripcion": "Mercado",
    "valor": "120.50",
    "categoria": "mercado",
    "tipo_gasto": null,
    "estado": "PENDIENTE",
    "errores": [
      {"campo": "fecha", "mensaje": "La fecha es obligatoria."}
    ],
    "posible_duplicado": false
  }
]
```

Solo devuelve filas `PENDIENTE`. La lista puede ordenarse por `lote_id` y `numero_fila`.

### 5.3 `GET /api/importaciones/pendientes/count`

Respuesta `200`:

```json
{"pendientes": 3}
```

Cuenta solo filas `PENDIENTE`. La ruta debe declararse antes de `/{pending_id}`.

### 5.4 `PUT /api/importaciones/pendientes/{pending_id}`

Cuerpo:

```json
{
  "fecha": "2026-10-21",
  "descripcion": "Mercado",
  "valor": "120.50",
  "categoria": "necesario",
  "tipo_gasto": "NECESARIO"
}
```

Todos los campos son opcionales; los ausentes conservan su valor. El servidor revalida y devuelve la fila con errores actualizados.

- `200`: actualización guardada, aunque queden errores (D-006 aprobada).
- `404`: pendiente inexistente.
- `409`: fila ya importada o descartada.
- `422`: errores de forma del cuerpo.

### 5.5 `POST /api/importaciones/pendientes/{pending_id}/contabilizar`

- `200`: movimiento creado y fila marcada como `IMPORTADO`.
- `404`: pendiente inexistente.
- `409`: ya importado o descartado.
- `422`: todavía tiene errores de validación.

Respuesta:

```json
{
  "fila": {
    "id": 12,
    "estado": "IMPORTADO",
    "movimiento_tipo": "GASTO",
    "movimiento_id": 8
  },
  "movimiento": {
    "fecha": "2026-10-21",
    "descripcion": "Mercado",
    "tipo": "NECESARIO",
    "valor": "120.50",
    "id": 8
  }
}
```

La respuesta concreta se definirá en el schema Pydantic; el frontend solo necesita actualizar el resumen y la bandeja.

### 5.6 `DELETE /api/importaciones/pendientes/{pending_id}`

- `204`: fila descartada lógicamente.
- `404`: pendiente inexistente.
- `409`: fila ya importada.

No se borra físicamente la fila (D-007 aprobada).

## 6. Schemas Pydantic

Ubicación: `app/api/schemas/imports.py`.

- `ImportBatchRead`.
- `PendingRowRead`.
- `PendingUpdate`.
- `PendingCount`.
- `PendingCommitResponse`.
- `ValidationIssue` con `campo` y `mensaje`.
- `ImportMovementType` con `INGRESO`/`GASTO`.
- `ImportRowStatus` con `PENDIENTE`/`IMPORTADO`/`DESCARTADO`.

Los DTO de frontera usan nombres en español. Los modelos SQLAlchemy usan atributos internos en inglés con columnas explícitas.

## 7. Pipeline de importación

### 7.1 Validación del archivo

Antes de parsear:

- Comprobar nombre base y extensión.
- Comprobar tipo de contenido.
- Comprobar tamaño máximo.
- Leer como máximo el límite permitido.
- Rechazar `.xls`, `.xlsm`, `.xlsb`, PDF, ZIP y formatos desconocidos.
- Rechazar archivos vacíos.

Los límites serán constantes configurables en el servicio, con valores iniciales de 10 MiB y 5.000 filas. Nginx debe permitir el tamaño con `client_max_body_size 12m`.

### 7.2 Parser CSV

- Decodificar con `utf-8-sig`.
- Rechazar codificaciones no soportadas con `422`.
- Detectar delimitador coma o punto y coma.
- Leer cabecera y filas con `csv.reader`.
- Ignorar filas completamente vacías.
- Conservar el número de fila original.
- Rechazar cabeceras duplicadas o requeridas ausentes.

### 7.3 Parser XLSX

- Usar `openpyxl` con `read_only=True` y `data_only=True`.
- Leer solo la primera hoja.
- Usar la primera fila con contenido como cabecera.
- Convertir fechas y números a tipos internos.
- No ejecutar macros ni fórmulas.
- Rechazar libros vacíos o sin filas de datos.
- Convertir números a `Decimal` mediante su representación textual, sin operaciones con `float`.

### 7.4 Normalización de cabeceras

- Normalizar con `unicodedata` (sin acentos), minúsculas, espacios y separadores.
- Mapear alias documentados:
  - `fecha`, `date`.
  - `descripcion`, `descripción`, `detalle`.
  - `valor`, `monto`, `importe`.
  - `categoria`, `categoría`, `tipo`.
- Rechazar cabeceras ambiguas o duplicadas.
- Ignorar columnas adicionales.

### 7.5 Validación de filas

- Fecha: ISO `YYYY-MM-DD`, `DD/MM/YYYY` o celda de fecha de Excel.
- Descripción: recortar, mínimo 1 y máximo 200.
- Valor: `Decimal` mayor que 0, máximo 12 dígitos y 2 decimales.
- Categoría de gasto: normalizar y mapear a `NECESARIO`, `NO_NECESARIO` o `INVERSION`.
- Categoría de ingreso: opcional, máximo 100 caracteres (D-002 aprobada).
- Errores por campo, con mensajes en español.
- Una fila con errores queda `PENDIENTE`.
- Una fila completa y sin duplicado queda lista para contabilizar.

### 7.6 Huella de duplicados

Calcular SHA-256 sobre una cadena canónica:

```text
tipo_movimiento | fecha ISO | descripcion_normalizada | valor_canonico | tipo_gasto/categoria
```

- Comparar con filas del mismo lote.
- Comparar con filas de lotes anteriores.
- Si coincide, marcar `posible_duplicado` y dejar la fila pendiente.
- Guardar `duplicado_de_id` cuando la coincidencia sea una fila conocida.
- No aplicar una restricción única.
- La contabilización manual permite confirmar un posible duplicado.

La comparación con movimientos manuales que no provienen de importaciones queda fuera de alcance en esta versión.

## 8. Transacciones y consistencia

### Importación

1. Parsear y validar fuera de la transacción.
2. Abrir una transacción.
3. Crear el lote.
4. Insertar todas las filas de importación.
5. Crear movimientos para filas completas y actualizar sus referencias.
6. Actualizar contadores del lote.
7. Confirmar.
8. Ante un error de base de datos, revertir todo el lote.

### Contabilización de un pendiente

1. Bloquear la fila con `SELECT ... FOR UPDATE`.
2. Comprobar estado `PENDIENTE`.
3. Revalidar todos los campos.
4. Crear el movimiento.
5. Marcar la fila `IMPORTADO` y guardar la referencia.
6. Recalcular contadores del lote.
7. Confirmar.

Dos solicitudes concurrentes no deben crear dos movimientos. La segunda recibe `409`.

### Actualización

1. Bloquear la fila.
2. Comprobar que sigue `PENDIENTE`.
3. Actualizar campos.
4. Revalidar y recalcular errores.
5. Guardar.
6. No crear movimientos.

### Descarte

1. Bloquear la fila.
2. Comprobar que sigue `PENDIENTE`.
3. Cambiar a `DESCARTADO`.
4. Recalcular contadores.
5. Confirmar.

## 9. Cambios en el frontend

### 9.1 Navegación

`App` mantiene:

- `view: 'main' | 'import' | 'pending'`.
- `pendingCount`.
- Los estados actuales de resumen, listas, carga y error.

La cabecera o la zona de acciones principales incluye:

- Botón `Importar`.
- Botón `Pendientes` con badge cuando `pendingCount > 0`.
- Botón de regreso en las vistas secundarias.

No se usa router.

### 9.2 Vista de importación

`ImportView`:

- Input de archivo con etiqueta accesible.
- Selector `Ingreso`/`Gasto`.
- Botón de envío con estado de carga.
- Resultado con totales importados, pendientes y descartados.
- Errores de archivo en `role="alert"`.
- Enlace o botón para abrir pendientes cuando haya filas pendientes.

### 9.3 Vista de pendientes

`PendingView`:

- Lista de pendientes.
- Campos editables: fecha, descripción, valor, categoría y tipo de gasto cuando aplique.
- Errores por campo.
- Botón `Guardar`.
- Botón `Contabilizar`, deshabilitado si hay errores.
- Botón `Descartar` con confirmación.
- Estado vacío.
- Tabla responsive con acciones accesibles.

### 9.4 Estado y refresco

- `App` carga `pendingCount` junto con el resumen y las listas.
- Tras importar: refrescar resumen, listas y conteo.
- Tras contabilizar o descartar: refrescar conteo y resumen.
- Tras guardar un pendiente: actualizar la fila y sus errores.
- Un error de red no debe borrar los datos ya cargados; se muestra un error y se permite reintentar.

### 9.5 Categoría de ingresos

Según D-002 aprobada:

- Añadir el campo opcional al formulario de ingresos.
- Mostrarlo en el listado.
- Actualizar tipos, API client, formularios, listados y pruebas.

## 10. Dependencias e infraestructura

### Backend

- `python-multipart`: necesario para `UploadFile` y `multipart/form-data`.
- `openpyxl`: lectura de `.xlsx`.

No se usa `pandas`, `xlrd` ni `python-calamine`. Las versiones se fijan en `pyproject.toml` y `uv.lock`, y se justifican en la tarea correspondiente.

### Nginx

Añadir:

```nginx
client_max_body_size 12m;
```

El límite debe ser mayor que el máximo de archivo permitido y coherente con el límite del backend. No se cambia el proxy `/api`.

### Docker

- La imagen de desarrollo instala las nuevas dependencias al reconstruirse.
- La imagen de producción usa `uv sync --frozen --no-dev`; las dependencias deben estar en el grupo de ejecución, no en `dev`.
- No se añaden servicios.

## 11. Estrategia de pruebas

### Backend unitarias

- Detección de delimitador CSV.
- Decodificación UTF-8 con BOM y rechazo de otras codificaciones.
- Alias de cabeceras y cabeceras faltantes.
- Conversión de fechas y valores.
- Normalización de categorías de gasto.
- Validación de descripción y límites.
- Huella de duplicados.
- Límites de tamaño y filas.
- Formato de errores.

### Backend API

- Carga CSV y XLSX con `TestClient`.
- Respuestas `201`, `413`, `415`, `422`.
- Listado y conteo de pendientes.
- Actualización, contabilización y descarte.
- `404`, `409`, `422`.
- OpenAPI de las rutas nuevas.

### Backend integración

- Persistencia de lote y filas.
- Pendientes tras reinicio.
- Importación parcial.
- Resumen sin cambios por pendientes.
- Transacción y rollback.
- Doble contabilización y concurrencia.
- Migración `0004`/`0005` y downgrade.
- Categoría de ingresos (D-002 aprobada).

### Frontend

- Cliente API con `fetch` simulado.
- `ImportView`: archivo, tipo, carga, resultado y error.
- `PendingView`: edición, guardado, contabilización, descarte y errores.
- Badge: aparece, desaparece y es accesible.
- `App`: navegación entre vistas y refresco.
- Estado vacío y error.
- Formato COP y fechas.

### Comandos

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
docker compose exec api uv run pytest
```

```bash
WEB_PORT=3001 ./scripts/smoke.sh
```

## 12. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Categorías ambiguas | D-002/D-003 y pendientes con corrección manual. |
| Duplicados legítimos bloqueados | Huella advisory, no restricción única. |
| Duplicados contabilizados dos veces | Bloqueo y estado `IMPORTADO`; `409`. |
| Pendientes contaminan totales | Tablas separadas y pruebas de resumen. |
| Archivos grandes o maliciosos | Límites, extensiones, MIME, solo lectura y sin macros. |
| Excel devuelve fórmulas sin valor | Tratar como inválido y dejar pendiente. |
| Codificación CSV desconocida | Rechazo claro con `422`. |
| Nginx rechaza el archivo | `client_max_body_size` coherente y prueba de carga. |
| Fallo a mitad de importación | Transacción única y rollback. |
| Migración destructiva | `upgrade`/`downgrade` revisados y pruebas en base de test. |
| Interfaz compleja | Componentes pequeños, estado local y reutilización de estilos. |
| Contrato existente roto | Campos aditivos y pruebas de regresión de ingresos/gastos/resumen. |
| Datos financieros en logs | Logs solo con IDs, conteos y estados. |

## 13. Trazabilidad requisitos → plan → tareas

| Requisito | Secciones del plan | Tareas |
|---|---|---|
| FR-001 | 5.1, 7.1, 9.2 | T-006, T-010, T-013, T-014 |
| FR-002 | 7.2, 7.3, 7.4 | T-003, T-004, T-005, T-006 |
| FR-003 | 7.5 | T-003, T-004, T-005, T-014 |
| FR-004 | 7.4, 7.5, 4.3 | T-002, T-003, T-006 |
| FR-005 | 7.5, 8 | T-006, T-014 |
| FR-006 | 4.1, 4.2, 8 | T-001, T-006, T-014 |
| FR-007 | 8 | T-006, T-014 |
| FR-008 | 5.2, 9.3 | T-007, T-011, T-012 |
| FR-009 | 5.4, 8, 9.3 | T-008, T-011 |
| FR-010 | 5.5, 8, 9.3 | T-008, T-011 |
| FR-011 | 5.6, 8, 9.3 | T-008, T-011 |
| FR-012 | 5.3, 9.1, 9.4 | T-007, T-012, T-015 |
| FR-013 | 8, 11 | T-008, T-014 |
| FR-014 | 7.6 | T-003, T-006, T-014 |
| FR-015 | 7.1, 8, 5 | T-006, T-014 |
| FR-016 | 7.1, 10 | T-006, T-013, T-014 |
| FR-017 | 9 | T-010, T-011, T-012, T-015 |
| NFR-001 | 4.2, 7.5 | T-001, T-003, T-014 |
| NFR-002 | 8 | T-001, T-006, T-008, T-014 |
| NFR-003 | 7.1, 10 | T-006, T-013, T-014 |
| NFR-004 | 7.1, 10 | T-006, T-013, T-014 |
| NFR-005 | 9 | T-010, T-011, T-012, T-015 |
| NFR-006 | 3, 4 | T-001 a T-016 |
| NFR-007 | 7, 8, 12 | T-006, T-008, T-014 |
| NFR-008 | 4.3, 5, 11 | T-002, T-009, T-014 |
| NFR-009 | 10 | T-013 |
| NFR-010 | 11 | T-014, T-015, T-016 |

## 14. Aprobación y siguiente paso

Las decisiones D-001 a D-012 y el plan están aprobados. La implementación avanza por las tareas de `tasks.md`.

El historial de importaciones queda fuera de alcance de la especificación 007. Según D-012, en una especificación posterior mostrará los lotes ordenados por fecha descendente, con nombre de archivo, tipo de movimiento, total de filas, importadas, pendientes y descartadas; permitirá abrir un lote para consultar sus filas y volver a los pendientes abiertos.

Después de la aprobación se ejecutarán las tareas de `tasks.md` en el orden indicado. No se modifica `legacy/`, no se altera el resumen existente y no se exponen datos pendientes en los cálculos financieros.
