# Especificación 012 — Exportación de ingresos y gastos

- Estado: validada.
- Fase: 10.
- Iteración: 1.3.0.
- Dependencias: `specs/002-api-ingresos/`, `specs/003-api-gastos/`, `specs/007-importacion-movimientos/`.
- Plan: `plan.md` (aprobado; T-001 a T-006 completadas).
- Tareas: `tasks.md` (T-001 a T-006 completadas).

## 1. Contexto y problema

La aplicación permite importar movimientos desde CSV/XLSX, pero no existe una forma de exportar los ingresos y gastos guardados. El usuario quiere descargar sus movimientos en un formato que pueda volver a importar, como respaldo manual de la información.

La exportación debe ser compatible con la importación existente:

- Un archivo de ingresos debe poder importarse con `tipo_movimiento=INGRESO`.
- Un archivo de gastos debe poder importarse con `tipo_movimiento=GASTO`.
- No se exportan asignaciones mensuales, pendientes, lotes de importación, IDs ni historial.
- La restauración esperada es sobre una base limpia; reimportar en la misma base duplica movimientos.

## 2. Usuarios y actores

- **Usuario propietario:** descarga un respaldo de sus ingresos o gastos.
- **Frontend:** ofrece el selector de formato y los botones de descarga.
- **Backend:** consulta los movimientos y genera CSV/XLSX.
- **PostgreSQL:** fuente de datos de los movimientos.

No hay autenticación, roles ni multiusuario.

## 3. Historias de usuario y flujos

### US-001 — Exportar ingresos

Como usuario, quiero descargar todos mis ingresos en CSV o XLSX para conservar un respaldo reimportable.

**Flujo:**

1. El usuario abre la vista `Importar/Exportar`.
2. Selecciona el formato `CSV` o `XLSX`.
3. Pulsa `Exportar ingresos`.
4. El navegador descarga un archivo con todos los ingresos guardados.
5. El archivo puede importarse de nuevo como `INGRESO`.

### US-002 — Exportar gastos

Como usuario, quiero descargar todos mis gastos en CSV o XLSX para conservar un respaldo reimportable.

**Flujo:**

1. El usuario abre la vista `Importar/Exportar`.
2. Selecciona el formato `CSV` o `XLSX`.
3. Pulsa `Exportar gastos`.
4. El navegador descarga un archivo con todos los gastos guardados.
5. El archivo puede importarse de nuevo como `GASTO`.

### US-003 — Mantener el flujo de importación

Como usuario, quiero seguir importando desde la misma vista sin perder el flujo actual.

**Flujo:**

1. El botón de la cabecera principal cambia de `Importar` a `Importar/Exportar`.
2. La vista conserva el formulario de importación.
3. La sección de exportación aparece debajo del formulario.
4. Importar y exportar no interfieren entre sí.

## 4. Requisitos funcionales

### FR-001 — Endpoints de exportación

Debe existir:

- `GET /api/exportaciones/ingresos?formato=csv|xlsx`
- `GET /api/exportaciones/gastos?formato=csv|xlsx`

`formato` es obligatorio y acepta `csv` o `xlsx`. Un valor ausente o desconocido devuelve `422`.

**Verificación:** pruebas de API y OpenAPI para ambos recursos y formatos.

### FR-002 — Exportación CSV

El CSV debe:

- Codificarse en UTF-8 con BOM.
- Usar coma como delimitador.
- Usar punto como separador decimal.
- Incluir una cabecera y una fila por movimiento.
- Escapar comas, comillas y saltos de línea según CSV estándar.
- Usar fechas ISO `YYYY-MM-DD`.
- Incluir importes como strings con dos decimales.

Cabeceras:

```text
Ingresos: Fecha,Descripcion,Valor,Categoria
Gastos:   Fecha,Descripcion,Valor,Tipo de gasto
```

En ingresos, `Categoria` contiene el `tipo` o queda vacía. En gastos, `Tipo de gasto` contiene el tipo del gasto.

**Verificación:** el CSV generado se lee con el parser de importación y produce los mismos movimientos.

### FR-003 — Exportación XLSX

El XLSX debe:

- Tener una sola hoja llamada `Ingresos` o `Gastos`.
- Incluir la cabecera en la primera fila.
- Incluir una fila por movimiento.
- Usar las mismas cabeceras y valores que el CSV.
- Preservar fechas ISO y valores con dos decimales.
- Poder leerse con `openpyxl` y con la importación existente.

**Verificación:** el XLSX generado se abre con `openpyxl` y se importa correctamente.

### FR-004 — Nombre y cabeceras de descarga

El archivo debe descargarse como adjunto con un nombre determinista:

```text
ingresos_YYYYMMDD_HHMMSS.csv
ingresos_YYYYMMDD_HHMMSS.xlsx
gastos_YYYYMMDD_HHMMSS.csv
gastos_YYYYMMDD_HHMMSS.xlsx
```

La respuesta debe incluir `Content-Disposition: attachment` y el MIME correspondiente:

- CSV: `text/csv; charset=utf-8`.
- XLSX: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

**Verificación:** pruebas de cabeceras HTTP y descarga desde el navegador.

### FR-005 — Botón y vista de importación/exportación

El botón de la cabecera principal debe cambiar de `Importar` a `Importar/Exportar`.

La vista debe:

- Mantener el formulario de importación actual.
- Añadir una sección `Exportar movimientos`.
- Incluir un selector `Formato` con `CSV` y `XLSX`.
- Incluir los botones `Exportar ingresos` y `Exportar gastos`.
- Mantener el botón `Volver`.

**Verificación:** pruebas de `App` e `ImportView`.

### FR-006 — Estados de descarga

Mientras se genera un archivo, el botón correspondiente debe mostrar `Preparando...` y deshabilitarse.

Si la descarga falla, debe mostrarse un error visible y accesible, sin perder el formulario ni los datos seleccionados.

**Verificación:** pruebas de componente con descarga pendiente, exitosa y fallida.

### FR-007 — Compatibilidad de ida y vuelta

Los archivos exportados deben poder importarse de nuevo en una base limpia y producir movimientos equivalentes:

- Misma fecha.
- Misma descripción.
- Mismo valor.
- Mismo tipo de ingreso o gasto.

Las descripciones con acentos, comas, comillas y saltos de línea deben conservarse.

**Verificación:** prueba de integración exportar → importar → comparar.

### FR-008 — Alcance del respaldo

La exportación incluye solo ingresos y gastos guardados.

No incluye:

- Asignaciones mensuales.
- Pendientes de importación.
- Lotes o filas de importación.
- IDs.
- Fechas de creación o actualización.

**Verificación:** los archivos contienen solo las columnas definidas y no dependen de tablas auxiliares.

### FR-009 — Sin dependencias nuevas

La exportación CSV usa la biblioteca estándar. La exportación XLSX usa `openpyxl`, ya presente en el backend.

No se añaden dependencias de frontend ni backend.

**Verificación:** `pyproject.toml` y `package.json` no cambian.

## 5. Requisitos no funcionales

### NFR-001 — Precisión monetaria

Los importes se leen como `Decimal` y se serializan como strings con dos decimales. No se usa `float` para dinero.

### NFR-002 — Codificación y compatibilidad

CSV en UTF-8 con BOM y XLSX legible por Excel y por la importación existente.

### NFR-003 — Rendimiento

La exportación se genera en memoria y se resuelve con una consulta por recurso. El MVP no requiere streaming ni paginación.

### NFR-004 — Seguridad

No se registran datos financieros ni rutas internas. La descarga es local y usa el mismo origen `/api`.

### NFR-005 — Accesibilidad

El selector y los botones tienen etiquetas asociadas. Los estados de carga y error son visibles y accesibles.

### NFR-006 — Compatibilidad

No se modifican los endpoints de importación, ingresos, gastos, resumen, balance ni gráficas.

## 6. Reglas de negocio

- **BR-001:** se exportan todos los movimientos guardados, sin filtro por fecha.
- **BR-002:** ingresos y gastos se exportan en archivos separados.
- **BR-003:** el archivo de ingresos usa `Categoria` para el tipo opcional.
- **BR-004:** el archivo de gastos usa `Tipo de gasto`.
- **BR-005:** el orden de exportación es `fecha ASC, id ASC`.
- **BR-006:** una exportación vacía genera un archivo solo con cabeceras.
- **BR-007:** reimportar en la misma base duplica movimientos; la restauración esperada es sobre una base limpia.
- **BR-008:** la exportación no sustituye un backup completo de PostgreSQL.

## 7. Casos límite y errores

- Sin ingresos: CSV/XLSX con cabecera y sin filas.
- Sin gastos: CSV/XLSX con cabecera y sin filas.
- Descripción con coma o comillas: se conserva mediante el escape CSV.
- Descripción con salto de línea: se conserva.
- Descripción con acentos: se conserva en UTF-8.
- Ingreso sin tipo: `Categoria` vacía.
- Gasto con tipo: `Tipo de gasto` con el enum correspondiente.
- Formato inválido o ausente: `422`.
- Error de red o servidor: mensaje visible en la UI.
- Muchos movimientos: se genera en memoria; el MVP no impone paginación.

## 8. Fuera de alcance

- Exportación de asignaciones mensuales, pendientes o historial de importación.
- Backup completo de PostgreSQL.
- Exportación combinada en un solo archivo o ZIP.
- Filtros por año, mes, tipo o texto.
- Programación automática de respaldos.
- Nuevas dependencias.
- Autenticación o exposición a Internet.

## 9. Criterios de aceptación

| Criterio | Descripción | Verificación |
|---|---|---|
| AC-001 | Existen endpoints de exportación para ingresos y gastos en CSV y XLSX. | Pruebas de API y OpenAPI. |
| AC-002 | El CSV usa UTF-8 con BOM, coma y punto decimal. | Pruebas de bytes y parser. |
| AC-003 | El XLSX contiene una hoja y la cabecera correcta. | Pruebas con `openpyxl`. |
| AC-004 | Los nombres de archivo y `Content-Disposition` son correctos. | Pruebas de cabeceras HTTP. |
| AC-005 | El botón principal se llama `Importar/Exportar`. | Prueba de `App`. |
| AC-006 | La vista muestra selector de formato y ambos botones. | Pruebas de `ImportView`. |
| AC-007 | La descarga muestra estado y errores accesibles. | Pruebas de componente. |
| AC-008 | Exportar e importar conserva fecha, descripción, valor y tipo. | Prueba de integración de ida y vuelta. |
| AC-009 | Una exportación vacía contiene solo cabeceras. | Pruebas de CSV y XLSX. |
| AC-010 | No se añaden dependencias ni se modifica el contrato existente. | Revisión de metadatos y suites. |

## 10. Decisiones de negocio y supuestos

### D-001 — Archivos separados por tipo

**Propuesta:** exportar ingresos y gastos en archivos independientes.

**Alternativas:** un ZIP con dos archivos; un archivo combinado con columna de tipo de movimiento.

**Decisión aprobada:** archivos separados, porque la importación actual procesa un solo tipo por archivo.

### D-002 — CSV con coma y punto decimal

**Propuesta:** delimitador coma y decimal con punto.

**Alternativas:** punto y coma con coma decimal.

**Decisión aprobada:** coma y punto decimal.

### D-003 — Exportación dentro de ImportView

**Propuesta:** añadir la sección de exportación dentro de la vista actual y renombrar el botón principal a `Importar/Exportar`.

**Alternativas:** botón independiente en la cabecera; nueva pestaña.

**Decisión aprobada:** se usa la vista existente y el botón `Importar/Exportar`.

### D-004 — Exportar todos los movimientos

**Propuesta:** exportar todos los ingresos o gastos guardados.

**Alternativas:** filtro por año o rango de fechas.

**Decisión aprobada:** exportar todo en esta versión.

### D-005 — Backup de movimientos

**Propuesta:** limitar la exportación a ingresos y gastos reimportables.

**Alternativas:** incluir asignaciones, pendientes e historial para un backup completo.

**Decisión aprobada:** solo movimientos. Un backup completo de PostgreSQL queda fuera de alcance.

## 11. Resultado de validación

La revisión 1 fue validada el 2026-11-06 con 310 pruebas de backend y 109 de frontend, versión 1.3.0 y smoke test de producción. La exportación CSV/XLSX, la ida y vuelta con la importación, los botones en `Importar/Exportar` y la descarga desde producción quedaron cubiertos.

## 12. Historial de revisiones

- Revisión 1: exportación de ingresos y gastos en CSV/XLSX, botones en ImportView y compatibilidad con la importación.
