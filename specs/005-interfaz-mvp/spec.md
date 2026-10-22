# Especificación 005 — Interfaz MVP

- Estado: validada.
- Fase: 3.
- Iteración: MVP.
- Dependencias: `specs/002-api-ingresos/`, `specs/003-api-gastos/` y `specs/004-api-resumen/`.
- Plan: `plan.md` (aprobado).
- Tareas: `tasks.md` (aprobadas).

## 1. Contexto y problema

El backend ya expone el CRUD de ingresos y gastos y el resumen global. El frontend actual solo muestra el estado técnico de la API.

Esta especificación construye una interfaz local, sencilla y usable para:

- Registrar ingresos.
- Registrar gastos y clasificarlos.
- Editar y eliminar movimientos.
- Consultar el total de ingresos, el total de gastos, el balance y el desglose por tipo.

La interfaz es de una sola página, en español, sin autenticación y sin dependencias nuevas de frontend.

## 2. Usuarios y actores

- **Usuario propietario:** único usuario local; registra y consulta sus finanzas.
- **Backend FastAPI:** fuente de verdad y cálculo de totales.
- **Desarrollador/agente:** implementa y valida la interfaz.

No hay roles, multiusuario ni autenticación.

## 3. Historias de usuario y flujos

### US-001 — Ver el estado financiero

Como usuario, quiero ver al abrir la aplicación el total de ingresos, el total de gastos, el balance y el desglose de gastos.

**Flujo:**

1. La aplicación carga el resumen y las listas.
2. Mientras carga, muestra un estado visible.
3. Al terminar, muestra las tarjetas de totales y el desglose.
4. Si falla la carga, muestra un error comprensible y permite reintentar.

### US-002 — Registrar un ingreso

Como usuario, quiero registrar un ingreso con fecha, descripción y valor.

**Flujo:**

1. El usuario abre la pestaña Ingresos.
2. Completa fecha, descripción y valor.
3. La aplicación valida y envía `POST /api/ingresos`.
4. Al confirmar, limpia el formulario, actualiza la lista y el resumen.

### US-003 — Registrar un gasto

Como usuario, quiero registrar un gasto con fecha, descripción, tipo y valor.

**Flujo:**

1. El usuario abre la pestaña Gastos.
2. Selecciona uno de los tres tipos.
3. La aplicación envía `POST /api/gastos`.
4. Al confirmar, limpia el formulario, actualiza la lista y el resumen.

### US-004 — Editar un movimiento

Como usuario, quiero editar un movimiento existente sin eliminarlo y volver a crearlo.

**Flujo:**

1. El usuario pulsa Editar en un registro.
2. El formulario se rellena con los datos actuales y cambia a modo edición.
3. Al guardar, envía `PUT` con el objeto completo.
4. La lista y el resumen se actualizan.
5. El usuario puede cancelar y volver al formulario de creación.

### US-005 — Eliminar un movimiento

Como usuario, quiero eliminar un movimiento registrado por error.

**Flujo:**

1. El usuario pulsa Eliminar.
2. La aplicación pide confirmación.
3. Si acepta, envía `DELETE`.
4. La lista y el resumen se actualizan.
5. Si cancela, no se modifica nada.

## 4. Requisitos funcionales

### FR-001 — Pantalla única

La aplicación debe renderizar una sola página con:

- Encabezado con el nombre del proyecto.
- Panel de resumen.
- Pestañas Ingresos y Gastos.
- Contenido de la pestaña activa.

No se añade router ni navegación entre páginas.

### FR-002 — Carga inicial

Al montar la aplicación, debe cargar:

- El resumen desde `GET /api/resumen`.
- Los ingresos desde `GET /api/ingresos`.
- Los gastos desde `GET /api/gastos`.

La carga debe mostrar un estado visible y no romper la página si una petición falla.

### FR-003 — Panel de resumen

El panel debe mostrar:

- Total de ingresos.
- Total de gastos.
- Balance.
- Desglose de gastos: necesario, no necesario e inversión.

Los importes se formatean para lectura. El balance puede ser negativo.

### FR-004 — Formulario de ingreso

Debe permitir crear un ingreso con:

- Fecha.
- Descripción.
- Valor.

Al enviar, debe llamar a `POST /api/ingresos` con `valor` como string decimal.

### FR-005 — Formulario de gasto

Debe permitir crear un gasto con:

- Fecha.
- Descripción.
- Tipo: necesario, no necesario o inversión.
- Valor.

Al enviar, debe llamar a `POST /api/gastos` con `tipo` y `valor` como strings válidos.

### FR-006 — Listados

Cada pestaña debe mostrar los movimientos existentes con:

- Fecha.
- Descripción.
- Tipo, solo en gastos.
- Valor formateado.
- Acciones Editar y Eliminar.

El orden es el devuelto por la API: `fecha DESC, id DESC`.

### FR-007 — Edición

Editar un movimiento debe:

- Rellenar el formulario correspondiente.
- Enviar `PUT` con el objeto completo.
- Actualizar la lista y el resumen.
- Permitir cancelar la edición.

No se implementa edición parcial.

### FR-008 — Eliminación

Eliminar un movimiento debe:

- Pedir confirmación al usuario.
- Enviar `DELETE`.
- Actualizar la lista y el resumen si se confirma.
- No modificar nada si se cancela.

### FR-009 — Actualización tras mutaciones

Después de crear, editar o eliminar, la aplicación debe volver a cargar la lista afectada y el resumen. Si la recarga falla, debe mostrarse un error y conservar la mayor cantidad de datos posible.

### FR-010 — Formato de presentación

- Los importes se muestran en pesos colombianos (COP) con separador de miles y dos decimales en formato `es-CO`.
- El símbolo `$` se muestra como parte del formato de moneda `COP`.
- Las fechas se muestran en formato local legible sin desplazar el día.
- Los tipos se muestran como `Necesario`, `No necesario` e `Inversión`.
- Los valores internos de la API siguen siendo `NECESARIO`, `NO_NECESARIO` e `INVERSION`.

### FR-011 — Validación y errores

Antes de enviar, la interfaz debe validar:

- Fecha obligatoria.
- Descripción obligatoria, recortada, máximo 200 caracteres.
- Valor mayor que 0, máximo 12 dígitos y 2 decimales.
- Tipo obligatorio en gastos.

Los errores del API (`422`, `404`, red) deben mostrarse con un mensaje comprensible. No se muestran trazas ni detalles técnicos.

### FR-012 — Estados de carga, error y vacío

- Carga: indicador visible y controles deshabilitados cuando corresponda.
- Error: banner con mensaje y opción de reintentar la carga.
- Vacío: mensaje claro cuando no hay ingresos o gastos.

### FR-013 — Accesibilidad

- Etiquetas asociadas a cada campo.
- Botones con texto comprensible.
- Errores anunciados con `role="alert"` o `aria-live`.
- Foco visible.
- Estado de la pestaña activa comunicado con atributos ARIA.
- No depender solo del color para transmitir el estado.

### FR-014 — Responsive

La interfaz debe funcionar en escritorio y móvil:

- Las tarjetas se apilan en pantallas estrechas.
- Las listas no generan desbordes horizontales.
- Los formularios y botones siguen siendo utilizables.

### FR-015 — Pruebas de frontend

Debe haber pruebas de:

- Cliente API: rutas, métodos, cuerpos, errores y respuesta `204`.
- Formularios: creación, edición, validación y cancelación.
- Listados: renderizado, edición y eliminación con confirmación.
- Resumen: valores, desglose y balance negativo.
- Estados de carga, error y vacío.
- Actualización de listas/resumen después de mutaciones.

### FR-016 — Reemplazo del estado técnico de salud

La pantalla deja de mostrar el estado técnico de `/api/health`. El endpoint permanece en el backend para operaciones. Los fallos de carga de datos se comunican mediante el estado de error de la interfaz.

## 5. Requisitos no funcionales

### NFR-001 — Sin dependencias nuevas

La interfaz usa React, TypeScript, CSS y `fetch`. No se añaden routers, librerías de estado, librerías de formularios, frameworks CSS ni clientes HTTP.

### NFR-002 — Calidad

El frontend debe pasar `lint`, `typecheck`, `test` y `build`. TypeScript permanece en modo estricto.

### NFR-003 — Contrato de API

La interfaz consume exactamente:

- `/api/ingresos`
- `/api/gastos`
- `/api/resumen`

No accede directamente a PostgreSQL ni duplica cálculos financieros; los totales provienen del backend.

### NFR-004 — Nombres

La interfaz se escribe en español. Los componentes, funciones, variables y pruebas internas usan inglés. Los DTO de frontera conservan los campos en español.

### NFR-005 — Simplicidad

La aplicación es de una sola página. El estado se gestiona con React local; no se introduce una capa global innecesaria.

### NFR-006 — Rendimiento

Las listas del MVP son pequeñas y no se paginan. Se evitan peticiones duplicadas innecesarias y se deshabilitan envíos concurrentes del mismo formulario.

### NFR-007 — Seguridad

No se registran secretos ni datos financieros en consola. No se usa `dangerouslySetInnerHTML`. No se exponen detalles técnicos de los errores.

### NFR-008 — Compatibilidad

No se modifican los contratos del backend. Las suites de ingresos, gastos y resumen deben seguir pasando.

## 6. Reglas de negocio

- **BR-001:** el MVP es de un solo usuario y no usa autenticación.
- **BR-002:** los importes se envían y reciben como strings; la UI no los usa para cálculos financieros.
- **BR-003:** el resumen es global; no se filtra por mes.
- **BR-004:** la fecha por defecto de un formulario nuevo es la fecha local actual.
- **BR-005:** la edición reemplaza el objeto completo.
- **BR-006:** la eliminación requiere confirmación.
- **BR-007:** los tipos de gasto se muestran con etiquetas en español, pero se envían con sus valores de API.
- **BR-008:** el formato de importes es `es-CO`, con dos decimales y moneda COP (`$`). La moneda es fija; no hay selector.

## 7. Casos límite y errores

- Sin ingresos o gastos: mensaje de lista vacía.
- Balance negativo: se muestra con signo menos y texto/estilo accesible.
- API caída al cargar: banner de error y botón de reintento.
- API caída al guardar o eliminar: mensaje de error y formulario conserva los datos.
- `422`: mensaje que invita a revisar los datos.
- `404` al editar o eliminar: mensaje de que el movimiento ya no existe y recarga de listas.
- Edición cancelada: se vuelve al formulario de creación sin modificar datos.
- Eliminación cancelada: no se envía ninguna petición.
- Envío doble: el botón se deshabilita mientras hay una petición en curso.
- Descripción con espacios: se recorta antes de enviar.
- Valor con coma decimal: se normaliza si el campo lo permite; el API recibe un decimal válido.
- Fecha inválida o futura: se permite si es una fecha válida; no se impone una regla adicional.
- Pantalla estrecha: tarjetas y listas se adaptan sin desbordamiento.
- Error de red al refrescar el resumen después de una mutación: se muestra el error; no se afirma que los totales estén actualizados.

## 8. Fuera de alcance

- Vista o filtro mensual.
- Gráficos y tendencias.
- Autenticación y multiusuario.
- Categorías configurables.
- Paginación, búsqueda y filtros.
- Importación/exportación CSV.
- Múltiples monedas o selector de moneda.
- Modo oscuro, i18n o temas.
- Router, librería de estado global o librería de formularios.
- Pruebas E2E con navegador; la validación de Docker se cubre en la especificación 006.
- Cambios en el backend.
- Indicador técnico de `/api/health` en la interfaz.

## 9. Criterios de aceptación verificables

| ID | Criterio | Evidencia |
|---|---|---|
| AC-001 | La aplicación carga resumen, ingresos y gastos al abrirse. | Prueba de App con API simulada. |
| AC-002 | El panel muestra totales, balance y desglose. | Prueba de `SummaryPanel`. |
| AC-003 | Se puede crear un ingreso desde la pestaña Ingresos. | Prueba de formulario y API simulada. |
| AC-004 | Se puede crear un gasto con tipo desde la pestaña Gastos. | Prueba de formulario y API simulada. |
| AC-005 | Los listados muestran fecha, descripción, tipo y valor. | Pruebas de listados. |
| AC-006 | Se puede editar un ingreso y un gasto. | Pruebas del flujo de edición. |
| AC-007 | Se puede eliminar con confirmación y cancelar sin efectos. | Pruebas de eliminación. |
| AC-008 | Listas y resumen se actualizan después de cada mutación. | Prueba de App/refresco. |
| AC-009 | Los errores de validación y de API se muestran en español. | Pruebas de formularios y errores. |
| AC-010 | Se cubren estados de carga, error y vacío. | Pruebas de App y listados. |
| AC-011 | La interfaz es accesible con etiquetas, roles y foco. | Revisión y pruebas de roles/atributos. |
| AC-012 | La interfaz se adapta a móvil y escritorio. | Revisión visual y CSS responsive. |
| AC-013 | `lint`, `typecheck`, `test` y `build` pasan. | Comandos de frontend. |
| AC-014 | No hay regresiones en backend, resumen ni Docker. | Suite completa y Compose. |

## 10. Preguntas abiertas y supuestos

### Supuestos aceptados

- Los importes se muestran en formato `es-CO`, con dos decimales y moneda COP (`$`), que es fija.
- La fecha por defecto es la fecha local actual.
- La eliminación usa `window.confirm`.
- La interfaz se escribe en español.
- No se añaden router, estado global, formularios ni frameworks CSS.
- Los importes se envían como strings; la UI no realiza sumas financieras.
- El resumen es global.
- El estado técnico de salud se elimina de la pantalla; el endpoint permanece en el backend.
- Las pruebas de frontend simulan la API; no requieren el backend en ejecución.
- No se implementan pruebas E2E de navegador en esta especificación.
- No se modifican los contratos del backend.

### Preguntas pendientes

Ninguna bloqueante para elaborar el plan técnico.

## 11. Resultado de validación

Pendiente de implementación.
