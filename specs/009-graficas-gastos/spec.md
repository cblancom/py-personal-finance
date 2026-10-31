# Especificación 009 — Gráficas de gastos mensuales

- Estado: validada.
- Fase: 7.
- Iteración: versión 1.0.
- Dependencias: `specs/003-api-gastos/`, `specs/005-interfaz-mvp/`, `specs/008-balance-mensual/`.
- Plan: `plan.md` (aprobado; implementado y validado).
- Tareas: `tasks.md` (T-001 a T-007 completadas).

## 1. Contexto y problema

La aplicación ya permite registrar gastos, clasificarlos por tipo, consultar un resumen global y revisar el balance mensual. Falta una lectura visual de la evolución mensual de los gastos que permita comparar de un vistazo los gastos necesarios, los no necesarios y las inversiones.

La gráfica debe vivir en la pantalla principal, entre el resumen y las pestañas/formularios de movimientos, para que el usuario vea primero la evolución y después registre o edite datos.

Esta es la última funcionalidad prevista para declarar la versión 1.0.0.

## 2. Usuarios y actores

- **Usuario propietario:** consulta la evolución mensual de sus gastos y cambia la forma de visualizarla.
- **Frontend:** carga las series, renderiza las gráficas y controla el año y el tipo de vista.
- **Backend:** agrega los gastos por mes y tipo.
- **PostgreSQL:** ejecuta la agregación.

No hay autenticación, roles ni multiusuario.

## 3. Historias de usuario y flujos

### US-001 — Ver la evolución mensual en barras

Como usuario, quiero ver una gráfica de barras apiladas mes a mes para comparar mis tres categorías de gasto.

**Flujo:**

1. El usuario abre la pantalla principal.
2. Debajo del resumen aparece la gráfica del año seleccionado.
3. El eje X muestra los doce meses.
4. Cada mes apila los gastos necesarios, no necesarios e inversión.
5. La leyenda identifica cada categoría.

### US-002 — Cambiar a líneas

Como usuario, quiero cambiar la gráfica a tres líneas continuas para comparar la evolución de cada categoría.

**Flujo:**

1. El usuario pulsa el botón `Líneas`.
2. La gráfica cambia sin recargar la página.
3. Se muestran tres líneas: necesarios, no necesarios e inversión.
4. El usuario puede volver a `Barras`.

### US-003 — Cambiar el año

Como usuario, quiero seleccionar el año de la gráfica.

**Flujo:**

1. El usuario despliega el selector de año.
2. Selecciona un año disponible.
3. La gráfica se actualiza con los datos de ese año.
4. Si el año no tiene gastos, se muestra un estado vacío.

### US-004 — Consultar valores exactos

Como usuario, quiero ver el valor de cada categoría en un mes.

**Flujo:**

1. El usuario pasa el cursor o enfoca un segmento o punto.
2. Aparece un tooltip con mes, categoría y valor en COP.
3. También puede abrir una tabla de datos accesible.

## 4. Requisitos funcionales

### FR-001 — Ubicación de la gráfica

La gráfica debe mostrarse en la pantalla principal, después del resumen y antes de las pestañas/formularios de ingresos y gastos.

**Verificación:** la gráfica aparece entre `SummaryPanel` y el tablist.

### FR-002 — Endpoint de series mensuales

Debe existir `GET /api/graficos/gastos-mensuales?anio=2026`, con `anio` opcional. Si no se envía, se usa el año actual.

La respuesta debe incluir los doce meses, incluso si no tienen movimientos, con los tres tipos de gasto.

**Verificación:** OpenAPI y pruebas de API.

### FR-003 — Agregación por mes y tipo

Los valores se calculan con `SUM` y `GROUP BY` en PostgreSQL sobre `gastos`, agrupando por mes y tipo dentro del año solicitado.

**Verificación:** pruebas con movimientos de varios meses y tipos.

### FR-004 — Barras apiladas

La vista por defecto debe ser un gráfico de barras apiladas:

- Eje X: enero a diciembre.
- Eje Y: importe en COP.
- Cada barra representa un mes.
- Cada barra contiene tres segmentos: `NECESARIO`, `NO_NECESARIO` e `INVERSION`.
- La leyenda muestra las tres categorías.

**Verificación:** prueba de componente y revisión visual.

### FR-005 — Líneas continuas

La vista alternativa debe ser un gráfico de líneas con tres series continuas:

- Gastos necesarios.
- Gastos no necesarios.
- Inversión.

Cada serie debe mostrar los doce meses, incluyendo valores en cero.

**Verificación:** prueba de componente y revisión visual.

### FR-006 — Cambio de vista

Debe existir un control `Barras` / `Líneas` que cambie la visualización sin recargar la página.

**Verificación:** prueba de interacción con `aria-pressed` o control equivalente.

### FR-007 — Selector de año

La gráfica debe incluir un selector de año alimentado por los años disponibles de la aplicación. El año actual es el valor inicial.

**Verificación:** el selector cambia la consulta y actualiza la gráfica.

### FR-008 — Tooltip y leyenda

Cada segmento o punto debe exponer su valor completo en COP mediante tooltip o interacción equivalente. La leyenda debe identificar las tres categorías.

**Verificación:** prueba de tooltip/leyenda y revisión visual.

### FR-009 — Tabla de datos accesible

Debe existir una alternativa textual, por ejemplo `Ver datos`, que muestre una tabla con mes, necesario, no necesario e inversión.

**Verificación:** tabla accesible y navegable.

### FR-010 — Estados de carga, error y vacío

La gráfica debe manejar:

- Carga.
- Error con reintento.
- Año sin gastos.
- Datos parciales con meses en cero.

**Verificación:** pruebas de componentes.

### FR-011 — Actualización después de mutaciones

La gráfica debe refrescarse cuando se crea, edita, elimina o importa un gasto.

**Verificación:** prueba de integración en `App` y refresco con `loadVersion`.

### FR-012 — Independencia del resumen

La nueva funcionalidad no debe modificar el resumen global, el balance mensual ni las APIs existentes.

**Verificación:** suites existentes y pruebas de regresión.

### FR-013 — Metadatos de versión 1.0.0

La entrega debe actualizar la versión a `1.0.0` en los metadatos del proyecto y en la documentación de release.

**Verificación:** `package.json`, `package-lock.json`, `pyproject.toml`, `uv.lock`, `main.py` y README coherentes.

## 5. Requisitos no funcionales

### NFR-001 — Precisión monetaria

Los importes se calculan con `Decimal`/`NUMERIC` en backend. El frontend solo convierte a número para escalar la gráfica; no realiza cálculos financieros.

### NFR-002 — Rendimiento

La API debe usar una sola agregación SQL por año. No debe consultar doce veces ni cargar todos los gastos individuales.

### NFR-003 — Dependencia aprobada

Se aprueba añadir `recharts@3.10.1` y `react-is@19.3.1` para las gráficas. No se añaden dependencias backend.

### NFR-004 — Accesibilidad

La gráfica debe tener título, leyenda, tooltip o tabla alternativa, foco visible y una descripción textual.

### NFR-005 — Responsive

La gráfica debe adaptarse al ancho disponible y mantener legibilidad en móvil.

### NFR-006 — Sin migración

No se crean tablas ni migraciones. Se reutiliza `gastos`.

### NFR-007 — Compatibilidad

No se deben romper las APIs, el frontend, Docker Compose ni las pruebas existentes.

### NFR-008 — Local y sin autenticación

La funcionalidad es local y no se expone a Internet.

## 6. Reglas de negocio

- **BR-001:** solo se grafican gastos e inversión; no se grafican ingresos.
- **BR-002:** el eje X contiene los doce meses del año seleccionado.
- **BR-003:** los meses sin gastos valen `"0.00"`.
- **BR-004:** las barras se apilan por tipo de gasto.
- **BR-005:** las líneas usan los mismos datos mensuales que las barras.
- **BR-006:** la vista inicial es barras.
- **BR-007:** el año inicial es el actual.
- **BR-008:** el cambio de vista no realiza una nueva petición.
- **BR-009:** los valores mostrados son los gastos reales, no montos presupuestados.
- **BR-010:** la gráfica incluye gastos manuales e importados.
- **BR-011:** la versión 1.0.0 se declara al completar y validar esta especificación.

## 7. Casos límite y errores

- Año sin gastos: estado vacío.
- Mes sin gastos: valor cero.
- Solo un tipo de gasto: las otras series valen cero.
- Muchos gastos: la agregación se hace en SQL.
- Error de red: gráfica con reintento sin romper el resto de la pantalla.
- Año inválido: `422`.
- Cambio de año durante la carga: se cancela la petición anterior.
- Cambio de vista: no se vuelve a consultar la API.
- Pantalla estrecha: la gráfica se adapta sin desbordar el contenedor.

## 8. Fuera de alcance

- Gráficas de ingresos.
- Filtros por categoría, descripción o rango de fechas.
- Comparación entre años.
- Exportación de gráficas.
- Gráficos de torta, área o dispersión.
- Análisis predictivo.

## 9. Criterios de aceptación

| Criterio | Descripción | Verificación |
|---|---|---|
| AC-001 | La gráfica aparece entre el resumen y los formularios. | Prueba de `App`. |
| AC-002 | El endpoint devuelve los doce meses y los tres tipos. | Prueba de API. |
| AC-003 | Las barras se apilan por categoría. | Prueba de componente y revisión visual. |
| AC-004 | La vista de líneas muestra tres series continuas. | Prueba de componente y revisión visual. |
| AC-005 | El toggle cambia entre barras y líneas. | Prueba de interacción. |
| AC-006 | El selector de año actualiza la gráfica. | Prueba de componente. |
| AC-007 | Los meses sin gastos aparecen en cero. | Prueba de API y componente. |
| AC-008 | La gráfica muestra tooltip/leyenda y tabla accesible. | Prueba de accesibilidad. |
| AC-009 | La gráfica se refresca tras mutaciones de gastos. | Prueba de `App`. |
| AC-010 | La API usa una agregación SQL. | Revisión y prueba de integración. |
| AC-011 | Los estados de carga, error y vacío funcionan. | Pruebas de componentes. |
| AC-012 | Las rutas y schemas aparecen en OpenAPI. | Prueba de OpenAPI. |
| AC-013 | Las suites y el build pasan. | Comandos canónicos. |
| AC-014 | La versión 1.0.0 está sincronizada. | Revisión de metadatos. |

## 10. Decisiones de negocio y supuestos

### D-001 — Eje X mensual y categorías apiladas

**Propuesta:** el eje X son los doce meses; cada barra apila las tres categorías.

**Alternativas:** agrupar por categoría y apilar meses; una barra por categoría.

**Impacto:** contrato de datos y componente de gráfica.

**Decisión aprobada:** se usa el eje X mensual y las categorías se apilan.

### D-002 — Selector de año

**Propuesta:** incluir selector de año con el año actual por defecto.

**Alternativas:** mostrar solo el año actual; mostrar todos los años.

**Impacto:** consulta, selector y estado de la gráfica.

**Decisión aprobada:** se incluye selector de año.

### D-003 — Recharts

**Propuesta:** usar `recharts@3.10.1` y `react-is@19.3.1`.

**Alternativas:** SVG propio sin dependencias; otra librería.

**Impacto:** dependencias frontend, bundle y pruebas.

**Decisión aprobada:** se usa Recharts.

### D-004 — Solo gastos e inversión

**Propuesta:** graficar únicamente gastos necesarios, no necesarios e inversión.

**Alternativas:** incluir ingresos; incluir balance neto.

**Impacto:** series y leyenda.

**Decisión aprobada:** solo se grafican gastos e inversión.

### D-005 — Versión 1.0.0

**Propuesta:** declarar la versión 1.0.0 al validar esta especificación.

**Alternativas:** mantener 0.1.0; posponer la versión.

**Impacto:** metadatos, README y release.

**Decisión aprobada:** se actualiza a 1.0.0.

## 11. Resultado de validación

La especificación fue validada el 2026-10-31 con 265 pruebas de backend y 99 de frontend, migración `0007`, versión 1.0.0 y smoke test de producción. La gráfica de barras apiladas, las tres líneas, el selector de año, la tabla accesible y el refresco tras mutaciones quedaron cubiertos.

## 12. Historial de revisiones

- Revisión 1: especificación inicial aprobada.
