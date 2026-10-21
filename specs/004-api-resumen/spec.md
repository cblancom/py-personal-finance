# Especificación 004 — API de resumen

- Estado: validada.
- Fase: 2.
- Iteración: MVP.
- Dependencias: `specs/002-api-ingresos/` y `specs/003-api-gastos/`.
- Plan: `plan.md` (aprobado).
- Tareas: `tasks.md` (aprobadas).

## 1. Contexto y problema

Las APIs de ingresos y gastos ya permiten registrar y consultar movimientos. El MVP exige además una **suma global** de ambos grupos y la clasificación de los gastos por tipo.

Esta especificación define un endpoint de solo lectura que devuelve:

- Total de ingresos.
- Total de gastos.
- Balance.
- Desglose de gastos por tipo.

El resumen es global; el filtro mensual queda para una iteración posterior. La interfaz que consumirá este endpoint se implementa en la especificación 005.

## 2. Usuarios y actores

- **Usuario propietario:** consulta el estado global de sus finanzas.
- **Frontend:** futuro consumidor de `/api/resumen`.
- **Desarrollador/agente:** implementa y valida el contrato.
- **PostgreSQL:** ejecuta las agregaciones.

No hay autenticación, roles ni multiusuario en el MVP.

## 3. Historias de usuario y flujos

### US-001 — Consultar totales

Como usuario, quiero ver cuánto he ingresado y cuánto he gastado en total.

**Flujo:**

1. El cliente solicita `GET /api/resumen`.
2. La API agrega los movimientos existentes.
3. La API responde `200` con los totales y el balance.

### US-002 — Consultar el desglose de gastos

Como usuario, quiero ver cuánto corresponde a gastos necesarios, no necesarios e inversiones.

**Flujo:**

1. La API agrupa los gastos por `tipo` y suma sus valores.
2. La respuesta incluye los tres tipos, incluso si alguno es cero.

### US-003 — Consultar un resumen vacío

Como usuario, quiero que el resumen funcione incluso sin movimientos registrados.

**Flujo:**

1. Sin ingresos ni gastos, la API responde `200`.
2. Todos los totales y el desglose valen `"0.00"`.

### US-004 — Ver un balance negativo

Como usuario, quiero que el balance refleje correctamente los gastos mayores que los ingresos.

**Flujo:**

1. La API calcula `total_ingresos - total_gastos`.
2. Si el resultado es negativo, se devuelve con signo negativo.

## 4. Requisitos funcionales

### FR-001 — Endpoint de resumen

Debe existir `GET /api/resumen`, sin parámetros ni autenticación, que devuelva `200` con el resumen financiero global.

**Verificación:** el endpoint aparece en OpenAPI y responde `200` con base disponible.

### FR-002 — Total de ingresos

El resumen debe incluir `total_ingresos` como la suma de todos los valores de la tabla `ingresos`.

Si no hay ingresos, el valor debe ser `"0.00"`.

**Verificación:** pruebas con cero, uno y varios ingresos.

### FR-003 — Total de gastos

El resumen debe incluir `total_gastos` como la suma de todos los valores de la tabla `gastos`.

Si no hay gastos, el valor debe ser `"0.00"`.

**Verificación:** pruebas con cero, uno y varios gastos.

### FR-004 — Balance

El resumen debe incluir `balance` calculado como:

```text
total_ingresos - total_gastos
```

El balance puede ser negativo.

**Verificación:** pruebas con balance positivo, cero y negativo.

### FR-005 — Desglose por tipo

El resumen debe incluir `gastos_por_tipo` con los tres tipos:

- `NECESARIO`
- `NO_NECESARIO`
- `INVERSION`

Cada valor es la suma de los gastos de ese tipo. Los tipos sin movimientos deben aparecer con `"0.00"`.

**Verificación:** pruebas con uno, varios y ningún gasto de cada tipo.

### FR-006 — Contrato de respuesta

La respuesta debe usar los nombres del contrato en español:

```json
{
  "total_ingresos": "5000.00",
  "total_gastos": "1500.50",
  "balance": "3499.50",
  "gastos_por_tipo": {
    "NECESARIO": "1000.00",
    "NO_NECESARIO": "300.50",
    "INVERSION": "200.00"
  }
}
```

Todos los importes se transportan como strings decimales con dos decimales.

**Verificación:** las claves y los tipos son los esperados; los importes tienen dos decimales.

### FR-007 — Resumen vacío

Sin ingresos ni gastos, la respuesta debe ser:

```json
{
  "total_ingresos": "0.00",
  "total_gastos": "0.00",
  "balance": "0.00",
  "gastos_por_tipo": {
    "NECESARIO": "0.00",
    "NO_NECESARIO": "0.00",
    "INVERSION": "0.00"
  }
}
```

**Verificación:** prueba de integración con las tablas truncadas.

### FR-008 — Consistencia entre total y desglose

`total_gastos` debe ser igual a la suma de los tres valores de `gastos_por_tipo`.

**Verificación:** la prueba de integración compara ambos valores.

### FR-009 — Agregación en servidor

Los totales y el desglose deben calcularse con agregaciones SQL en PostgreSQL. No se deben cargar todos los movimientos en memoria para sumarlos.

**Verificación:** revisión de la consulta y pruebas de integración.

### FR-010 — Semántica de errores

- `200` con el resumen cuando la base está disponible.
- Un fallo inesperado de base de datos devuelve 5xx y no expone detalles de conexión.
- El endpoint no devuelve `404` por ausencia de movimientos.

**Verificación:** prueba del caso vacío y revisión del manejo de errores.

### FR-011 — Documentación OpenAPI

El endpoint y el schema de respuesta deben aparecer en `/docs` y en el esquema OpenAPI.

**Verificación:** `/api/resumen` aparece en `app.openapi()["paths"]`.

## 5. Requisitos no funcionales

### NFR-001 — Precisión monetaria

Los importes se calculan con `Decimal`/`NUMERIC`. Nunca se usa `float`.

### NFR-002 — Eficiencia de la agregación

La API debe usar `SUM` y `GROUP BY` en PostgreSQL. No debe iterar todos los movimientos en Python para calcular totales.

### NFR-003 — Convenciones de nombres

La ruta y los campos externos usan español. Las clases, funciones y variables internas usan inglés. Los DTO de frontera conservan los nombres del contrato.

### NFR-004 — Pruebas

Debe haber pruebas de integración contra `personal_finance_test` con datos creados a través de las APIs de ingresos y gastos.

No se requieren pruebas unitarias de cálculo si la lógica se delega a SQL, pero sí una prueba de serialización del schema.

### NFR-005 — Seguridad y privacidad

La API es local y no tiene autenticación. No se registran secretos ni cadenas de conexión en logs. Los errores no exponen detalles internos.

### NFR-006 — Alcance del resumen

El resumen es global, sin filtro mensual, paginación ni parámetros de consulta en el MVP.

### NFR-007 — Sin cambios de esquema

Esta funcionalidad no crea tablas ni migraciones. Reutiliza `ingresos` y `gastos`.

### NFR-008 — Compatibilidad

No debe romper las APIs de ingresos, gastos, salud, el frontend ni Docker Compose. No se añaden dependencias nuevas.

## 6. Reglas de negocio

- **BR-001:** el MVP maneja una sola moneda; no se incluye símbolo ni código.
- **BR-002:** `balance = total_ingresos - total_gastos`; puede ser negativo.
- **BR-003:** `gastos_por_tipo` siempre contiene los tres tipos, con cero cuando no hay movimientos.
- **BR-004:** `total_gastos` es la suma de los tres valores del desglose.
- **BR-005:** el resumen es global; no se filtra por mes.
- **BR-006:** el MVP es de un solo usuario y no requiere autenticación.
- **BR-007:** los importes se devuelven como strings con dos decimales.

## 7. Casos límite y errores

- Base vacía: todos los valores son `"0.00"`.
- Solo ingresos: `total_gastos` y el desglose son cero.
- Solo gastos: `total_ingresos` es cero.
- Gastos mayores que ingresos: `balance` negativo.
- Varios movimientos del mismo tipo: se suman correctamente.
- Un tipo sin movimientos: aparece con `"0.00"`.
- Importes con decimales: se conservan y se serializan como strings.
- PostgreSQL no disponible: 5xx; el estado se refleja en `/api/health`.
- Escrituras concurrentes: el resumen es de mejor esfuerzo; el MVP es de un solo usuario y no garantiza una foto transaccional estricta.
- Parámetros de consulta no soportados: no forman parte del contrato.

## 8. Fuera de alcance

- Formularios, tarjetas y gráficos en React (spec 005).
- Filtro o vista mensual.
- Resumen por rango de fechas.
- Autenticación y multiusuario.
- Presupuestos, metas o comparaciones.
- Categorías configurables.
- Caché de resultados.
- Exportación o importación.
- Paginación o desglose por movimiento.
- Múltiples monedas.

## 9. Criterios de aceptación verificables

| ID | Criterio | Evidencia |
|---|---|---|
| AC-001 | `GET /api/resumen` existe y responde `200`. | Prueba de integración y OpenAPI. |
| AC-002 | Suma correctamente los ingresos. | Prueba con varios ingresos. |
| AC-003 | Suma correctamente los gastos. | Prueba con varios gastos. |
| AC-004 | Calcula el balance con signo correcto. | Pruebas con balance positivo y negativo. |
| AC-005 | Devuelve los tres tipos en el desglose. | Prueba de claves y valores. |
| AC-006 | Incluye tipos sin movimientos con cero. | Prueba con un solo tipo. |
| AC-007 | `total_gastos` coincide con la suma del desglose. | Comparación en la prueba. |
| AC-008 | La base vacía devuelve todo en cero. | Prueba sin movimientos. |
| AC-009 | Los importes se serializan como strings con dos decimales. | Prueba del contrato JSON. |
| AC-010 | La agregación se ejecuta en PostgreSQL. | Revisión de consultas y pruebas. |
| AC-011 | Las pruebas de ingresos y gastos siguen pasando. | Suite completa. |
| AC-012 | OpenAPI documenta el endpoint. | Inspección de `/docs` y `app.openapi()`. |

## 10. Preguntas abiertas y supuestos

### Supuestos aceptados

- El resumen es global; no se implementa filtro mensual en el MVP.
- Los importes se devuelven como strings con dos decimales.
- `gastos_por_tipo` usa las claves `NECESARIO`, `NO_NECESARIO` e `INVERSION`.
- `total_gastos` se obtiene sumando el desglose para mantener consistencia.
- No se crean tablas ni migraciones.
- No se añaden dependencias.
- Las pruebas de integración reutilizan `personal_finance_test` y el fixture que trunca `ingresos` y `gastos`.
- Los mensajes técnicos permanecen en inglés; la interfaz los traducirá en spec 005.
- No se añade caché en el MVP.

### Preguntas pendientes

Ninguna bloqueante para elaborar el plan técnico.

## 11. Resultado de validación

- Fecha: 2026-10-21.
- Veredicto: **cumplida**.
- Evidencia: tabla de validación en [`tasks.md`](tasks.md). Suite completa en Docker con 135 pruebas, contrato verificado con 3 pruebas de schema, 5 pruebas de integración y 1 prueba de OpenAPI; frontend sin regresiones.
