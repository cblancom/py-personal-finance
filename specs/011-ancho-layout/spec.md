# Especificación 011 — Ajuste de ancho y layout responsive

- Estado: validada.
- Fase: 9.
- Iteración: 1.2.1.
- Dependencias: `specs/005-interfaz-mvp/`, `specs/008-balance-mensual/`.
- Plan: `plan.md` (aprobado; T-001 a T-004 completadas).
- Tareas: `tasks.md` (T-001 a T-004 completadas).

## 1. Contexto y problema

La aplicación se muestra centrada con un ancho máximo de `1080px`. En monitores grandes quedan márgenes laterales muy amplios, aunque el contenido no los necesita.

El problema es más visible en la vista mensual de `Balance mensual`:

- `main` tiene `max-width: 1080px` y padding lateral asimétrico.
- El contenido útil queda en unos `992px`.
- Las cuatro columnas del balance se reparten en unos `236px` cada una.
- Cada columna añade `padding: 0 1rem`, dejando unos `204px` para la tabla.
- `.balance-table` tiene `min-width: 15rem` (`240px`).

El resultado es que cada tabla mensual necesita más ancho del disponible y aparece un scroll horizontal dentro de la columna, incluso en escritorio. Al mismo tiempo, el contenedor global deja cientos de píxeles sin usar a los lados.

## 2. Usuarios y actores

- **Usuario propietario:** consulta la aplicación y el balance mensual en escritorio y móvil.
- **Frontend:** aplica el layout y los breakpoints responsive.
- **Desarrollador/agente:** ajusta CSS y valida el resultado visual.

No hay cambios de backend, API, base de datos ni dependencias.

## 3. Historias de usuario y flujos

### US-001 — Aprovechar mejor el ancho en escritorio

Como usuario, quiero que el contenido use más ancho de la pantalla para no ver márgenes laterales tan grandes.

**Flujo:**

1. El usuario abre la aplicación en un monitor de escritorio.
2. El contenedor principal ocupa hasta `1440px`.
3. Los márgenes laterales se reducen de forma proporcional.
4. El contenido sigue centrado y legible.

### US-002 — Ver el balance mensual sin scroll horizontal

Como usuario, quiero ver las descripciones y los valores del balance mensual sin usar las barras de scroll horizontales.

**Flujo:**

1. El usuario abre `Balance mensual` y selecciona un mes.
2. La vista muestra las cuatro columnas en escritorio.
3. Cada columna dispone de ancho suficiente para fecha, descripción y valor.
4. No aparece scroll horizontal en la tabla de la columna.
5. En pantallas estrechas, las columnas se apilan y el scroll horizontal queda solo como respaldo.

## 4. Requisitos funcionales

### FR-001 — Ancho máximo global de 1440px

El contenedor principal debe usar `max-width: 1440px`, manteniendo `margin: 0 auto` para seguir centrado.

El ancho debe incluir el padding lateral, de acuerdo con `box-sizing: border-box`.

**Verificación:** en una pantalla de 1920px, el contenido principal mide 1440px como máximo y los márgenes laterales son menores que con 1080px.

### FR-002 — Padding lateral reducido y consistente

El padding horizontal de `main` debe reducirse y usar valores fluidos:

- Lado izquierdo: entre `2rem` y `3rem`.
- Lado derecho: entre `1.25rem` y `2rem`.

La línea decorativa izquierda debe permanecer alineada con el nuevo padding. En móvil se mantiene el ajuste existente.

**Verificación:** la línea vertical no se solapa con el contenido y el espacio lateral es menor en escritorio.

### FR-003 — Columnas del balance con más espacio útil

La vista mensual debe conservar cuatro columnas en escritorio, pero con menos espacio perdido:

- `.balance-columns`: `gap` de `0.75rem`.
- `.balance-column`: padding horizontal de `0.75rem`.
- La primera columna conserva `padding-left: 0` y sin borde izquierdo.

**Verificación:** las cuatro columnas se mantienen alineadas y los bordes separadores siguen visibles.

### FR-004 — Tabla mensual sin desbordamiento en escritorio

`.balance-table` debe reducir su `min-width` de `15rem` a `13rem`.

La tabla debe seguir usando `width: 100%`, `border-collapse: collapse` y `white-space: nowrap` solo en la columna de valor. La descripción puede envolver en varias líneas.

**Verificación:** con las cuatro columnas visibles en escritorio, no aparece scroll horizontal en `.balance-column__table-wrap`.

### FR-005 — Breakpoints responsive

La vista del balance debe usar estos rangos:

- Más de `1100px`: cuatro columnas.
- Entre `720px` y `1100px`: dos columnas.
- Menos de `720px`: una columna.

El breakpoint actual de `900px` para pasar a dos columnas debe sustituirse por `1100px`.

**Verificación:** a 1024px se ven dos columnas; a 1280px se ven cuatro; a 375px se ve una.

### FR-006 — Scroll horizontal como respaldo

Los contenedores `.balance-column__table-wrap` y `.balance-table-wrap` deben conservar `overflow-x: auto` para pantallas muy estrechas.

El scroll horizontal no debe aparecer en escritorio cuando las cuatro columnas estén visibles.

**Verificación:** en móvil, una tabla que no quepa puede desplazarse; en escritorio no hay scroll horizontal en el balance.

### FR-007 — Sin regresiones en otras vistas

El cambio no debe romper:

- La tabla anual del balance.
- La gráfica de gastos.
- Los formularios de ingresos, gastos e importación.
- Los listados y las pestañas.
- La navegación por teclado y el foco visible.

**Verificación:** las suites de frontend pasan y la revisión visual de las vistas principales no muestra desbordes ni solapamientos.

### FR-008 — Cambio limitado al frontend

La corrección debe implementarse únicamente en `frontend/src/index.css`.

No se modifican componentes React, APIs, schemas, migraciones ni datos.

**Verificación:** el diff de implementación se limita a CSS y, si aplica, a documentación de evidencia.

## 5. Requisitos no funcionales

### NFR-001 — Responsive

El layout debe adaptarse sin desbordar la página en anchos de 375px, 768px, 1024px, 1280px, 1440px y 1920px.

### NFR-002 — Legibilidad

Las descripciones del balance pueden envolver, pero los valores monetarios deben permanecer completos y alineados a la derecha.

### NFR-003 — Accesibilidad

No se eliminan etiquetas, roles ni focos visibles. La tabla debe seguir siendo navegable y comprensible.

### NFR-004 — Sin dependencias nuevas

No se añaden librerías ni cambios de infraestructura.

### NFR-005 — Compatibilidad

No se modifican el contrato de la API, la importación, el balance calculado ni los datos persistidos.

## 6. Reglas de negocio y decisiones

- **BR-001:** el ancho máximo del contenido es `1440px`.
- **BR-002:** el contenido sigue centrado.
- **BR-003:** la vista mensual conserva cuatro columnas en escritorio.
- **BR-004:** el scroll horizontal es solo un respaldo para pantallas estrechas.
- **BR-005:** no se cambia el cálculo financiero ni el contrato de datos.

### D-001 — Ancho máximo de 1440px

**Propuesta:** aumentar `main` de `1080px` a `1440px`.

**Alternativas:** 1600px, ancho completo, mantener 1080px y reducir solo el padding interno.

**Impacto:** menos espacio lateral, más ancho útil para el balance y la gráfica.

**Decisión aprobada:** se usa `1440px`.

### D-002 — Breakpoint de dos columnas en 1100px

**Propuesta:** mostrar cuatro columnas por encima de `1100px` y dos columnas por debajo.

**Alternativas:** mantener `900px` y reducir más la tabla; usar tres columnas intermedias.

**Impacto:** evita el scroll en portátiles y tablets sin sacrificar las cuatro columnas en escritorio.

**Decisión aprobada:** se usa `1100px`.

### D-003 — Tabla mensual de 13rem

**Propuesta:** reducir el `min-width` de `.balance-table` a `13rem` y permitir que la descripción envuelva.

**Alternativas:** eliminar el `min-width`; usar `table-layout: fixed`; ocultar la fecha en pantallas estrechas.

**Impacto:** la tabla cabe en la columna sin scroll en escritorio.

**Decisión aprobada:** se usa `13rem`.

## 7. Casos límite

- Pantalla de 1920px: el contenido no supera 1440px y los márgenes laterales se reducen.
- Pantalla de 1440px: el contenido ocupa el ancho disponible con padding lateral.
- Pantalla de 1280px: se mantienen cuatro columnas sin scroll.
- Pantalla de 1024px: se muestran dos columnas.
- Pantalla de 375px: se muestra una columna y el scroll horizontal queda como respaldo.
- Descripción muy larga: envuelve dentro de la celda sin desbordar la columna.
- Valor monetario largo: permanece alineado a la derecha y no se recorta.
- Balance anual: conserva su tabla y su scroll horizontal en móvil.
- Gráfica y formularios: no se estiran de forma incómoda.

## 8. Fuera de alcance

- Exportación de ingresos y gastos a CSV/XLSX.
- Cambios de diseño visual, tipografía, colores o componentes.
- Cambios en el cálculo del balance.
- Cambios en la API o en la base de datos.
- Nuevas dependencias.
- Pruebas visuales automatizadas con navegador.

## 9. Criterios de aceptación

| Criterio | Descripción | Verificación |
|---|---|---|
| AC-001 | `main` usa `max-width: 1440px` y sigue centrado. | Revisión CSS y visual a 1920px. |
| AC-002 | El padding lateral se reduce y la línea decorativa sigue alineada. | Revisión visual a 1440px y 1920px. |
| AC-003 | La vista mensual muestra cuatro columnas por encima de 1100px. | Revisión a 1280px y 1440px. |
| AC-004 | La vista mensual muestra dos columnas entre 720px y 1100px. | Revisión a 1024px. |
| AC-005 | La vista mensual muestra una columna por debajo de 720px. | Revisión a 375px. |
| AC-006 | No aparece scroll horizontal en el balance mensual de escritorio. | Revisión a 1280px, 1440px y 1920px. |
| AC-007 | Las descripciones y los valores se ven completos en escritorio. | Revisión visual con descripciones largas. |
| AC-008 | El balance anual, la gráfica y los formularios no presentan regresiones. | Suites de frontend y revisión visual. |
| AC-009 | El cambio se limita a CSS y documentación. | Revisión del diff. |

## 10. Resultado de validación

La revisión 1 fue validada el 2026-11-05 con 100/100 pruebas de frontend, lint, typecheck y build correctos. La revisión visual se realizó a 375px, 1024px, 1280px, 1440px y 1920px: una columna en móvil, dos columnas a 1024px, cuatro columnas desde 1280px y sin scroll horizontal en el balance de escritorio.

## 11. Historial de revisiones

- Revisión 1: ancho máximo de 1440px, reducción de padding y corrección del scroll horizontal del balance mensual.
