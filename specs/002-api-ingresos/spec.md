# Especificación 002 — API de ingresos

- Estado: validada.
- Fase: 1.
- Iteración: MVP.
- Dependencias: `specs/001-fundaciones/`.
- Plan: `plan.md` (aprobado).
- Tareas: `tasks.md` (aprobadas).

## 1. Contexto y problema

La Fase 0 dejó operativos el backend, el frontend, PostgreSQL, Alembic y Docker Compose, pero todavía no existe ninguna funcionalidad financiera.

Esta iteración incorpora la primera entidad del dominio: los ingresos. El objetivo es disponer de una API completa y verificable para crear, listar, consultar, editar y eliminar ingresos, con validación en servidor y persistencia exacta de importes.

La interfaz de usuario se implementará en la especificación 005. Esta especificación define el contrato que esa interfaz consumirá.

## 2. Usuarios y actores

- **Usuario propietario:** único usuario local; registra y corrige sus ingresos.
- **Frontend:** consumidor de la API mediante `/api/ingresos`.
- **Desarrollador/agente:** implementa y valida el contrato.
- **PostgreSQL:** fuente de verdad para la persistencia.

No hay autenticación, roles ni multiusuario en el MVP.

## 3. Historias de usuario y flujos

### US-001 — Registrar un ingreso

Como usuario, quiero registrar un ingreso con fecha, descripción y valor para incorporarlo a mi historial.

**Flujo:**

1. El cliente envía `POST /api/ingresos` con un payload válido.
2. La API valida los datos y los persiste.
3. La API responde `201` con el ingreso creado, incluido su `id`.

### US-002 — Consultar ingresos

Como usuario, quiero ver todos mis ingresos y consultar uno concreto para revisar la información registrada.

**Flujo:**

1. El cliente solicita `GET /api/ingresos`.
2. La API responde una lista ordenada por fecha descendente y, en empate, por `id` descendente.
3. El cliente puede solicitar `GET /api/ingresos/{income_id}`.
4. Si el ingreso no existe, la API responde `404`.

### US-003 — Editar un ingreso

Como usuario, quiero corregir la fecha, la descripción o el valor de un ingreso existente.

**Flujo:**

1. El cliente envía `PUT /api/ingresos/{income_id}` con el objeto completo.
2. La API valida y reemplaza los campos.
3. La API responde `200` con el ingreso actualizado.
4. Si el ingreso no existe, responde `404`; si el payload es inválido, `422`.

### US-004 — Eliminar un ingreso

Como usuario, quiero eliminar un ingreso registrado por error.

**Flujo:**

1. El cliente envía `DELETE /api/ingresos/{income_id}`.
2. Si existe, la API lo elimina y responde `204` sin cuerpo.
3. Si no existe, responde `404`.

### US-005 — Recibir errores claros

Como consumidor de la API, quiero que los datos inválidos se rechacen con `422` y que los recursos inexistentes devuelvan `404`, sin efectos parciales.

## 4. Requisitos funcionales

### FR-001 — Modelo y tabla `ingresos`

Debe existir una tabla `ingresos` con:

- `id`: entero, clave primaria, autoincremental.
- `fecha`: `DATE`, obligatoria.
- `descripcion`: `VARCHAR(200)`, obligatoria.
- `valor`: `NUMERIC(12,2)`, obligatorio.

Debe existir un índice sobre `fecha`.

Debe existir un modelo SQLAlchemy `Income` con atributos internos en inglés (`id`, `date`, `description`, `amount`) mapeados explícitamente a las columnas en español.

**Verificación:** la tabla y el modelo existen; la migración crea la estructura y el índice.

### FR-002 — Migración reversible

Debe existir una migración Alembic `0002` con `down_revision = "0001"` que cree la tabla, las restricciones y el índice.

- `upgrade` crea la estructura.
- `downgrade` elimina índice y tabla.
- La migración debe poder aplicarse sobre una base que ya tiene la revisión `0001`.

**Verificación:** `alembic upgrade head`, `alembic downgrade 0001` y un nuevo `upgrade head` funcionan; `alembic current` reporta `0002`.

### FR-003 — Crear ingresos

`POST /api/ingresos` debe aceptar un objeto con `fecha`, `descripcion` y `valor`, validarlo, persistirlo y responder `201` con el objeto creado, incluido `id`.

**Verificación:** un payload válido devuelve `201`; el registro puede consultarse después.

### FR-004 — Listar ingresos

`GET /api/ingresos` debe devolver `200` con una lista de ingresos ordenada por `fecha` descendente y, para fechas iguales, por `id` descendente.

Si no hay registros, debe devolver una lista vacía `[]`.

**Verificación:** con varios registros, el orden es el esperado; sin registros, la respuesta es `[]`.

### FR-005 — Consultar un ingreso

`GET /api/ingresos/{income_id}` debe devolver `200` con el ingreso solicitado o `404` con detalle `"Ingreso no encontrado"` si no existe.

**Verificación:** se cubren ambos casos.

### FR-006 — Editar ingresos

`PUT /api/ingresos/{income_id}` debe reemplazar la fecha, la descripción y el valor con el payload recibido.

- Éxito: `200` con el objeto actualizado.
- Inexistente: `404`.
- Payload inválido: `422`.

El reemplazo es completo; no se aceptan actualizaciones parciales en esta iteración.

**Verificación:** se actualizan los tres campos y se cubren `404` y `422`.

### FR-007 — Eliminar ingresos

`DELETE /api/ingresos/{income_id}` debe eliminar el registro y responder `204` sin cuerpo.

Si no existe, debe responder `404`.

**Verificación:** tras eliminar, el recurso ya no se encuentra; se cubre el `404`.

### FR-008 — Validación del valor

`valor` debe:

- Ser obligatorio.
- Ser mayor que cero.
- Tener como máximo 12 dígitos en total.
- Tener como máximo 2 decimales.

El valor se almacena como `Decimal`/`NUMERIC`. No se usa `float` en ninguna capa.

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

Las fechas futuras se permiten en el MVP. La interfaz podrá inicializar el campo con la fecha actual.

**Verificación:** fecha válida aceptada; fecha ausente o inválida rechazada con `422`.

### FR-011 — Contrato de respuesta

Las respuestas de ingresos deben usar los nombres del contrato en español:

```json
{
  "id": 1,
  "fecha": "2026-10-21",
  "descripcion": "Salario",
  "valor": "1500.50"
}
```

- `fecha` se transporta como fecha ISO.
- `valor` se transporta como string decimal con dos decimales para preservar precisión.
- La entrada acepta `valor` como string o número; el frontend enviará string.

**Verificación:** las respuestas JSON contienen los cuatro campos y `valor` es un string.

### FR-012 — Semántica de errores

- `422`: payload inválido, campo ausente o restricción incumplida.
- `404`: recurso inexistente con `{"detail": "Ingreso no encontrado"}`.
- `204`: eliminación sin cuerpo.
- Un fallo inesperado de base de datos no se oculta; se registra y devuelve un error 5xx.

**Verificación:** pruebas para `404`, `422` y `204`; los mensajes no exponen datos de conexión.

### FR-013 — Documentación OpenAPI

Todos los endpoints y schemas deben aparecer en `/docs` y en el esquema OpenAPI, con los códigos de estado principales documentados.

**Verificación:** `/api/ingresos` y `/api/ingresos/{income_id}` aparecen en `app.openapi()["paths"]`.

## 5. Requisitos no funcionales

### NFR-001 — Precisión monetaria

Los importes se almacenan y calculan con `Decimal`/`NUMERIC(12,2)`. Nunca se usa `float` para transportar o persistir dinero.

### NFR-002 — Validación en servidor y base de datos

Las reglas críticas se validan en Pydantic y se refuerzan en PostgreSQL mediante restricciones `CHECK`.

### NFR-003 — Convenciones de nombres

Las rutas y los campos externos usan español. Las clases, funciones, variables y nombres de pruebas usan inglés. Los DTO de frontera conservan los nombres del contrato.

### NFR-004 — Pruebas

Debe haber pruebas unitarias sin base de datos y pruebas de integración contra PostgreSQL.

Las pruebas de integración usan una base dedicada `personal_finance_test`, creada por el fixture, migrada con Alembic y truncada entre casos. No deben modificar la base de desarrollo.

### NFR-005 — Seguridad y privacidad

La API es local y no tiene autenticación. No se registran secretos ni cadenas de conexión en logs. Los errores no exponen detalles internos.

### NFR-006 — Rendimiento y alcance del listado

El listado devuelve todos los registros del MVP, sin paginación. El índice sobre `fecha` prepara el filtro mensual futuro.

### NFR-007 — Reversibilidad de migraciones

La migración `0002` debe poder revertirse sin afectar la revisión base ni otras tablas.

### NFR-008 — Compatibilidad con el entorno existente

La API debe seguir funcionando con Docker Compose y con las pruebas de la Fase 0. No se introducen dependencias nuevas para esta funcionalidad.

## 6. Reglas de negocio

- **BR-001:** el MVP maneja una sola moneda; no se almacena código ni símbolo de moneda.
- **BR-002:** un ingreso siempre tiene valor positivo.
- **BR-003:** la descripción es obligatoria y no puede quedar vacía tras el recorte.
- **BR-004:** la fecha es obligatoria; se permiten fechas futuras.
- **BR-005:** se permiten ingresos duplicados; no hay restricción de unicidad.
- **BR-006:** la edición reemplaza el objeto completo mediante `PUT`.
- **BR-007:** la eliminación es física; no hay borrado lógico.
- **BR-008:** el MVP es de un solo usuario y no requiere autenticación.
- **BR-009:** las pruebas de integración nunca usan la base de desarrollo.

## 7. Casos límite y errores

- Lista vacía: `GET /api/ingresos` devuelve `[]`.
- Dos ingresos con la misma fecha: se ordenan por `id` descendente.
- Ingreso inexistente: `404` en `GET`, `PUT` y `DELETE`.
- `income_id` no entero: `422` por validación de ruta.
- Valor `0`, negativo, ausente, con más de 12 dígitos o más de 2 decimales: `422`.
- Descripción vacía, solo espacios o mayor de 200 caracteres: `422`.
- Fecha ausente o con formato inválido: `422`.
- Payload con campos adicionales: se ignoran por defecto de Pydantic; no se persisten.
- Dos ediciones concurrentes: prevalece la última escritura; no hay bloqueo optimista.
- PostgreSQL no disponible: el endpoint falla con 5xx; el estado se refleja en `/api/health`.
- `TEST_DATABASE_URL` ausente: las pruebas de integración se omiten con un mensaje claro; las unitarias siguen ejecutándose.
- `TEST_DATABASE_URL` apunta a la misma base que `DATABASE_URL`: el fixture debe abortar para evitar pérdida de datos.

## 8. Fuera de alcance

- Formularios, listados y totales en React.
- Filtro o vista mensual.
- Endpoint de resumen.
- Autenticación y multiusuario.
- Categorías, etiquetas o tipos de ingreso.
- Paginación, búsqueda y ordenamientos configurables.
- Importación/exportación CSV.
- Borrado lógico, auditoría o historial de cambios.
- Múltiples monedas.
- Edición parcial con `PATCH`.
- Carga masiva.

## 9. Criterios de aceptación verificables

| ID | Criterio | Evidencia |
|---|---|---|
| AC-001 | La tabla `ingresos` existe con columnas, checks e índice. | Migración aplicada e inspección de la tabla. |
| AC-002 | La migración `0002` sube y baja correctamente. | `upgrade head`, `downgrade 0001`, `upgrade head`, `alembic current`. |
| AC-003 | `POST /api/ingresos` crea un ingreso y responde `201`. | Prueba de integración y ejemplo OpenAPI. |
| AC-004 | `GET /api/ingresos` devuelve la lista ordenada. | Prueba con varios registros. |
| AC-005 | `GET /api/ingresos/{income_id}` devuelve `200` o `404`. | Pruebas de ambos casos. |
| AC-006 | `PUT /api/ingresos/{income_id}` actualiza los tres campos. | Prueba de actualización completa. |
| AC-007 | `DELETE /api/ingresos/{income_id}` responde `204` o `404`. | Pruebas de ambos casos. |
| AC-008 | Los payloads inválidos devuelven `422`. | Pruebas de valor, descripción y fecha. |
| AC-009 | Las restricciones de base de datos rechazan datos inválidos. | Pruebas directas contra PostgreSQL. |
| AC-010 | El importe se conserva como decimal exacto y se serializa como string. | Prueba de ida y vuelta con dos decimales. |
| AC-011 | Las pruebas unitarias pasan sin PostgreSQL. | `uv run pytest` sin `TEST_DATABASE_URL`. |
| AC-012 | Las pruebas de integración pasan contra `personal_finance_test`. | `docker compose exec api uv run pytest` o `uv run --env-file ../.env pytest`. |
| AC-013 | OpenAPI documenta los endpoints y schemas. | Inspección de `/docs` y `app.openapi()`. |
| AC-014 | No hay regresiones en salud, Docker ni pruebas existentes. | Suite completa y `docker compose up --build`. |

## 10. Preguntas abiertas y supuestos

### Supuestos aceptados

- `valor` se devuelve como string decimal; la entrada acepta string o número y el frontend enviará string.
- La edición usa `PUT` con reemplazo completo.
- Se permiten fechas futuras.
- La precisión es `NUMERIC(12,2)` y el valor debe ser positivo.
- La eliminación responde `204`.
- Las pruebas de integración usan una base dedicada `personal_finance_test`.
- Los mensajes de validación de FastAPI permanecen en inglés técnico; el frontend mostrará mensajes en español en la especificación 005.
- No se añade paginación en el MVP.

### Preguntas pendientes

Ninguna bloqueante para elaborar el plan técnico.

## 11. Resultado de validación

- Fecha: 2026-10-21.
- Veredicto: **cumplida**.
- Evidencia: tabla de validación en [`tasks.md`](tasks.md). Suite completa en Docker con 62 pruebas, migración reversible en la base de test, frontend sin regresiones y documentación actualizada.
