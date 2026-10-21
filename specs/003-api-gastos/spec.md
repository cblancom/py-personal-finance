# Especificación 003 — API de gastos

- Estado: aprobada; supuestos aceptados.
- Fase: 1.
- Iteración: MVP.
- Dependencias: `specs/001-fundaciones/` y `specs/002-api-ingresos/` (infraestructura de pruebas y patrones de API).
- Plan: `plan.md` (aprobado).
- Tareas: `tasks.md` (aprobadas).

## 1. Contexto y problema

La API de ingresos (`002-api-ingresos`) ya permite registrar movimientos de entrada. Falta la segunda mitad del dominio financiero: los gastos, que además deben clasificarse como necesarios, no necesarios o inversiones.

Esta iteración incorpora la entidad `Expense` y expone un CRUD completo bajo `/api/gastos`. El `tipo` de gasto será la base para el resumen por categoría de la especificación 004 y para los formularios de la interfaz en la especificación 005.

## 2. Usuarios y actores

- **Usuario propietario:** único usuario local; registra y corrige sus gastos.
- **Frontend:** futuro consumidor de `/api/gastos`.
- **Desarrollador/agente:** implementa y valida el contrato.
- **PostgreSQL:** fuente de verdad para la persistencia.

No hay autenticación, roles ni multiusuario en el MVP.

## 3. Historias de usuario y flujos

### US-001 — Registrar un gasto

Como usuario, quiero registrar un gasto con fecha, descripción, tipo y valor para incorporarlo a mi historial.

**Flujo:**

1. El cliente envía `POST /api/gastos` con un payload válido.
2. La API valida fecha, descripción, tipo y valor.
3. La API persiste el gasto y responde `201` con el objeto creado, incluido su `id`.

### US-002 — Consultar gastos

Como usuario, quiero ver todos mis gastos y consultar uno concreto.

**Flujo:**

1. El cliente solicita `GET /api/gastos`.
2. La API responde la lista ordenada por `fecha` descendente y, en empate, por `id` descendente.
3. El cliente puede solicitar `GET /api/gastos/{expense_id}`.
4. Si no existe, la API responde `404`.

### US-003 — Editar un gasto

Como usuario, quiero corregir cualquiera de los cuatro campos de un gasto existente.

**Flujo:**

1. El cliente envía `PUT /api/gastos/{expense_id}` con el objeto completo.
2. La API valida y reemplaza fecha, descripción, tipo y valor.
3. La API responde `200` con el gasto actualizado.
4. Si no existe, responde `404`; si el payload es inválido, `422`.

### US-004 — Eliminar un gasto

Como usuario, quiero eliminar un gasto registrado por error.

**Flujo:**

1. El cliente envía `DELETE /api/gastos/{expense_id}`.
2. Si existe, la API lo elimina y responde `204` sin cuerpo.
3. Si no existe, responde `404`.

### US-005 — Clasificar correctamente

Como usuario, quiero que el sistema rechace tipos de gasto desconocidos y valores inválidos para mantener la clasificación consistente.

## 4. Requisitos funcionales

### FR-001 — Modelo y tabla `gastos`

Debe existir una tabla `gastos` con:

- `id`: entero, clave primaria, autoincremental.
- `fecha`: `DATE`, obligatoria.
- `descripcion`: `VARCHAR(200)`, obligatoria.
- `tipo`: `VARCHAR(20)`, obligatorio.
- `valor`: `NUMERIC(12,2)`, obligatorio.

Debe existir un índice sobre `fecha`.

Debe existir un modelo SQLAlchemy `Expense` con atributos internos en inglés (`id`, `date`, `description`, `expense_type`, `amount`) mapeados explícitamente a las columnas en español.

**Verificación:** la tabla y el modelo existen; la migración crea la estructura y el índice.

### FR-002 — Migración reversible

Debe existir una migración Alembic `0003` con `down_revision = "0002"` que cree la tabla, las restricciones y el índice.

- `upgrade` crea la estructura.
- `downgrade` elimina índice y tabla.
- La migración debe poder aplicarse sobre una base que ya tiene la revisión `0002`.

**Verificación:** `alembic upgrade head`, `alembic downgrade 0002` y un nuevo `upgrade head` funcionan; `alembic current` reporta `0003`.

### FR-003 — Crear gastos

`POST /api/gastos` debe aceptar `fecha`, `descripcion`, `tipo` y `valor`, validarlos, persistirlos y responder `201` con el objeto creado, incluido `id`.

**Verificación:** un payload válido devuelve `201`; el registro puede consultarse después.

### FR-004 — Listar gastos

`GET /api/gastos` debe devolver `200` con una lista ordenada por `fecha` descendente y, para fechas iguales, por `id` descendente.

Si no hay registros, debe devolver `[]`.

**Verificación:** con varios registros, el orden es el esperado; sin registros, la respuesta es `[]`.

### FR-005 — Consultar un gasto

`GET /api/gastos/{expense_id}` debe devolver `200` con el gasto solicitado o `404` con detalle `"Gasto no encontrado"` si no existe.

**Verificación:** se cubren ambos casos.

### FR-006 — Editar gastos

`PUT /api/gastos/{expense_id}` debe reemplazar fecha, descripción, tipo y valor con el payload recibido.

- Éxito: `200` con el objeto actualizado.
- Inexistente: `404`.
- Payload inválido: `422`.

El reemplazo es completo; no se aceptan actualizaciones parciales en esta iteración.

**Verificación:** se actualizan los cuatro campos y se cubren `404` y `422`.

### FR-007 — Eliminar gastos

`DELETE /api/gastos/{expense_id}` debe eliminar el registro y responder `204` sin cuerpo.

Si no existe, debe responder `404`.

**Verificación:** tras eliminar, el recurso ya no se encuentra; se cubre el `404`.

### FR-008 — Validación del valor

`valor` debe:

- Ser obligatorio.
- Ser mayor que cero.
- Tener como máximo 12 dígitos en total.
- Tener como máximo 2 decimales.

Se almacena como `Decimal`/`NUMERIC`. No se usa `float` en ninguna capa.

**Verificación:** cero, negativo, exceso de dígitos, exceso de decimales y valor ausente devuelven `422`.

### FR-009 — Validación de la descripción

`descripcion` debe:

- Ser obligatoria.
- Recortarse antes de validar y almacenar.
- Tener entre 1 y 200 caracteres después del recorte.

Una descripción vacía o compuesta solo por espacios devuelve `422`.

**Verificación:** se cubren descripción válida, vacía, solo espacios y mayor de 200 caracteres.

### FR-010 — Validación de la fecha

`fecha` debe ser obligatoria y una fecha ISO 8601 válida (`YYYY-MM-DD`).

Las fechas futuras se permiten en el MVP.

**Verificación:** fecha válida aceptada; fecha ausente o inválida rechazada con `422`.

### FR-011 — Validación del tipo

`tipo` debe ser obligatorio y uno de los siguientes valores exactos:

- `NECESARIO`
- `NO_NECESARIO`
- `INVERSION`

Cualquier otro valor, incluido un valor en minúsculas o con espacios, devuelve `422`.

**Verificación:** los tres valores válidos se aceptan; un valor desconocido se rechaza con `422`; la base de datos también rechaza valores fuera del conjunto.

### FR-012 — Contrato de respuesta

Las respuestas de gastos deben usar los nombres del contrato en español:

```json
{
  "id": 1,
  "fecha": "2026-10-21",
  "descripcion": "Mercado",
  "tipo": "NECESARIO",
  "valor": "120.50"
}
```

- `fecha` se transporta como fecha ISO.
- `tipo` se transporta como string con uno de los tres valores permitidos.
- `valor` se transporta como string decimal con dos decimales para preservar precisión.
- La entrada acepta `valor` como string o número; el frontend enviará string.

**Verificación:** las respuestas contienen los cinco campos, `tipo` es válido y `valor` es un string.

### FR-013 — Semántica de errores

- `422`: payload inválido, campo ausente, tipo desconocido o restricción incumplida.
- `404`: recurso inexistente con `{"detail": "Gasto no encontrado"}`.
- `204`: eliminación sin cuerpo.
- Un fallo inesperado de base de datos no se oculta; se registra y devuelve un error 5xx.

**Verificación:** pruebas para `404`, `422` y `204`; los mensajes no exponen datos de conexión.

### FR-014 — Documentación OpenAPI

Todos los endpoints y schemas deben aparecer en `/docs` y en el esquema OpenAPI, con los códigos de estado principales documentados.

**Verificación:** `/api/gastos` y `/api/gastos/{expense_id}` aparecen en `app.openapi()["paths"]`.

## 5. Requisitos no funcionales

### NFR-001 — Precisión monetaria

Los importes se almacenan y calculan con `Decimal`/`NUMERIC(12,2)`. Nunca se usa `float` para transportar o persistir dinero.

### NFR-002 — Validación en servidor y base de datos

Las reglas críticas se validan en Pydantic y se refuerzan en PostgreSQL mediante restricciones `CHECK`.

### NFR-003 — Convenciones de nombres

Las rutas, los campos externos y los valores de `tipo` usan español. Las clases, funciones, variables y nombres de pruebas usan inglés. Los DTO de frontera conservan los nombres del contrato.

### NFR-004 — Pruebas

Debe haber pruebas unitarias sin base de datos y pruebas de integración contra PostgreSQL.

Las pruebas de integración reutilizan `personal_finance_test`, ejecutan la migración `0003` y truncan tanto `ingresos` como `gastos` entre casos. No deben modificar la base de desarrollo.

### NFR-005 — Seguridad y privacidad

La API es local y no tiene autenticación. No se registran secretos ni cadenas de conexión en logs. Los errores no exponen detalles internos.

### NFR-006 — Rendimiento y alcance del listado

El listado devuelve todos los registros del MVP, sin paginación. El índice sobre `fecha` prepara el filtro mensual futuro.

### NFR-007 — Reversibilidad de migraciones

La migración `0003` debe poder revertirse sin afectar `0001`, `0002` ni las tablas de ingresos.

### NFR-008 — Compatibilidad con el entorno existente

La API debe seguir funcionando con Docker Compose, el frontend y las pruebas de las especificaciones anteriores. No se introducen dependencias nuevas.

### NFR-009 — Aislamiento de las pruebas

El fixture compartido debe limpiar tanto ingresos como gastos antes de cada prueba. La prueba de humo de la base debe verificar la revisión `0003` y la existencia de ambas tablas.

## 6. Reglas de negocio

- **BR-001:** el MVP maneja una sola moneda; no se almacena código ni símbolo de moneda.
- **BR-002:** un gasto siempre tiene valor positivo.
- **BR-003:** la descripción es obligatoria y no puede quedar vacía tras el recorte.
- **BR-004:** la fecha es obligatoria; se permiten fechas futuras.
- **BR-005:** el tipo es obligatorio y pertenece al conjunto `NECESARIO`, `NO_NECESARIO`, `INVERSION`.
- **BR-006:** se permiten gastos duplicados; no hay restricción de unicidad.
- **BR-007:** la edición reemplaza el objeto completo mediante `PUT`.
- **BR-008:** la eliminación es física; no hay borrado lógico.
- **BR-009:** el MVP es de un solo usuario y no requiere autenticación.
- **BR-010:** las pruebas de integración nunca usan la base de desarrollo.

## 7. Casos límite y errores

- Lista vacía: `GET /api/gastos` devuelve `[]`.
- Dos gastos con la misma fecha: se ordenan por `id` descendente.
- Gasto inexistente: `404` en `GET`, `PUT` y `DELETE`.
- `expense_id` no entero: `422` por validación de ruta.
- Valor `0`, negativo, ausente, con más de 12 dígitos o más de 2 decimales: `422`.
- Descripción vacía, solo espacios o mayor de 200 caracteres: `422`.
- Fecha ausente o con formato inválido: `422`.
- Tipo ausente, desconocido, en minúsculas o con espacios: `422`.
- Payload con campos adicionales: se ignoran por defecto de Pydantic; no se persisten.
- Dos ediciones concurrentes: prevalece la última escritura; no hay bloqueo optimista.
- PostgreSQL no disponible: el endpoint falla con 5xx; el estado se refleja en `/api/health`.
- La base de test que ya contiene ingresos debe seguir funcionando; el fixture limpia ambas tablas.
- La migración `0003` sobre una base en `0002` debe aplicar sin recrear `ingresos`.
- `TEST_DATABASE_URL` ausente: las pruebas de integración se omiten con un mensaje claro.

## 8. Fuera de alcance

- Formularios, listados y totales en React.
- Endpoint de resumen y desglose por tipo (spec 004).
- Filtro o vista mensual.
- Autenticación y multiusuario.
- Tabla de categorías configurables.
- Paginación, búsqueda y ordenamientos configurables.
- Importación/exportación CSV.
- Borrado lógico, auditoría o historial de cambios.
- Múltiples monedas.
- Edición parcial con `PATCH`.
- Carga masiva.

## 9. Criterios de aceptación verificables

| ID | Criterio | Evidencia |
|---|---|---|
| AC-001 | La tabla `gastos` existe con columnas, checks e índice. | Migración aplicada e inspección de la tabla. |
| AC-002 | La migración `0003` sube y baja correctamente. | `upgrade head`, `downgrade 0002`, `upgrade head`, `alembic current`. |
| AC-003 | `POST /api/gastos` crea un gasto y responde `201`. | Prueba de integración. |
| AC-004 | `GET /api/gastos` devuelve la lista ordenada. | Prueba con varios registros. |
| AC-005 | `GET /api/gastos/{expense_id}` devuelve `200` o `404`. | Pruebas de ambos casos. |
| AC-006 | `PUT /api/gastos/{expense_id}` actualiza los cuatro campos. | Prueba de actualización completa. |
| AC-007 | `DELETE /api/gastos/{expense_id}` responde `204` o `404`. | Pruebas de ambos casos. |
| AC-008 | Los payloads inválidos devuelven `422`. | Pruebas de valor, descripción, fecha y tipo. |
| AC-009 | Las restricciones de base de datos rechazan datos inválidos. | Pruebas directas contra PostgreSQL. |
| AC-010 | El importe se conserva como decimal exacto y se serializa como string. | Prueba de ida y vuelta con dos decimales. |
| AC-011 | Las pruebas unitarias pasan sin PostgreSQL. | `uv run pytest` sin `TEST_DATABASE_URL`. |
| AC-012 | Las pruebas de integración pasan contra `personal_finance_test`. | `docker compose exec api uv run pytest`. |
| AC-013 | OpenAPI documenta los endpoints y schemas. | Inspección de `/docs` y `app.openapi()`. |
| AC-014 | No hay regresiones en ingresos, salud, frontend ni Docker. | Suite completa y `docker compose up --build`. |

## 10. Preguntas abiertas y supuestos

### Supuestos aceptados

- Los valores de `tipo` son `NECESARIO`, `NO_NECESARIO` e `INVERSION`.
- El tipo se almacena como `VARCHAR(20)` con un `CHECK` de valores, no como un enum nativo de PostgreSQL, para simplificar la migración y su reversión.
- `valor` se devuelve como string decimal; la entrada acepta string o número y el frontend enviará string.
- La edición usa `PUT` con reemplazo completo.
- Se permiten fechas futuras.
- La precisión es `NUMERIC(12,2)` y el valor debe ser positivo.
- La eliminación responde `204`.
- Las pruebas de integración comparten `personal_finance_test` con la API de ingresos y limpian ambas tablas.
- Los mensajes de validación de FastAPI permanecen en inglés técnico; el frontend mostrará mensajes en español en la especificación 005.
- No se añade paginación en el MVP.

### Preguntas pendientes

Ninguna bloqueante para elaborar el plan técnico.

## 11. Resultado de validación

Pendiente de implementación.
