# Plan técnico 008 — Balance mensual

- Estado: aprobado (revisión 2 implementada y validada).
- Especificación: [`spec.md`](spec.md).
- Fase: 6.
- Iteración: post-MVP.

## 1. Resumen de la solución

Se añade una pestaña `Balance mensual` que consulta los ingresos y gastos de un periodo y los compara con los porcentajes asignados por el usuario.

La solución incluye:

- Una tabla `asignaciones_mensuales` con una fila por año y mes.
- Una migración Alembic `0007`.
- Endpoints de consulta mensual/anual y de guardado de porcentajes.
- Cálculos monetarios con `Decimal`.
- Una vista React con selectores, cuatro columnas de movimientos, edición de porcentajes y monto sin asignar.
- Pruebas de cálculos, API, integración, OpenAPI y componentes.

No se añaden dependencias.

## 2. Arquitectura y flujo de datos

```text
Frontend: MonthlyBalanceView
        │
        │ GET /api/balance-mensual?anio=2026&mes=10
        │ GET /api/balance-mensual?anio=2026
        │ PUT /api/balance-mensual/asignaciones/2026/10
        ▼
FastAPI: router /balance-mensual
        │
        │ consultas agregadas y lectura/upsert de asignaciones
        ▼
PostgreSQL: ingresos, gastos, asignaciones_mensuales
        │
        ▼
MonthlyBalanceRead
  ├── anio
  ├── mes
  ├── ingresos
  ├── sin_asignar
  ├── rubros[NECESARIO, NO_NECESARIO, INVERSION]
  └── movimientos[INGRESOS, NECESARIO, NO_NECESARIO, INVERSION]
```

Flujo mensual:

1. El frontend selecciona año y mes.
2. El backend suma ingresos del mes.
3. Agrupa gastos del mes por tipo.
4. Lee la asignación del mes; si no existe, usa 0% en los tres rubros.
5. Calcula asignado y restante por rubro.
6. Calcula el monto sin asignar.
7. Carga los movimientos del mes agrupados por columna.
8. Devuelve el contrato mensual.

Flujo anual:

1. El frontend selecciona un año y el mes `Todos`.
2. El backend agrega los doce meses.
3. Suma los montos asignados de cada mes.
4. Calcula el porcentaje ponderado por los ingresos anuales.
5. Devuelve el contrato anual con `mes: null`.

## 3. Componentes y responsabilidades

| Archivo | Responsabilidad |
|---|---|
| `backend/app/db/models/monthly_allocation.py` | Modelo `MonthlyAllocation` y tabla `asignaciones_mensuales`. |
| `backend/app/services/monthly_balance.py` | Consultas agregadas, cálculos y upsert de asignaciones. |
| `backend/app/api/schemas/monthly_balance.py` | DTOs de lectura, rubros, periodos y actualización. |
| `backend/app/api/routes/monthly_balance.py` | Endpoints `/balance-mensual` y `/balance-mensual/asignaciones/...`. |
| `backend/app/main.py` | Registro del router bajo `/api`. |
| `backend/alembic/versions/0007_create_monthly_allocations.py` | Migración de la nueva tabla. |
| `frontend/src/types/monthlyBalance.ts` | Tipos del contrato. |
| `frontend/src/api/monthlyBalance.ts` | Cliente de consulta y guardado. |
| `frontend/src/components/MonthlyBalanceView.tsx` | Selectores, tabla, porcentajes y estados. |
| `frontend/src/App.tsx` | Tercera pestaña y montaje de la vista. |
| `frontend/src/index.css` | Estilos de la tabla y del formulario. |

No se modifica `legacy/`.

## 4. Modelo de datos y migración

### 4.1 Tabla `asignaciones_mensuales`

Una fila por año y mes:

| Columna | Tipo | Restricción |
|---|---|---|
| `id` | `Integer` | PK. |
| `anio` | `Integer` | No nulo, entre 1900 y 2100. |
| `mes` | `Integer` | No nulo, entre 1 y 12. |
| `porcentaje_necesario` | `Numeric(5, 2)` | No nulo, entre 0 y 100. |
| `porcentaje_no_necesario` | `Numeric(5, 2)` | No nulo, entre 0 y 100. |
| `porcentaje_inversion` | `Numeric(5, 2)` | No nulo, entre 0 y 100. |
| `created_at` | `DateTime(timezone=True)` | `now()`. |
| `updated_at` | `DateTime(timezone=True)` | `now()`. |

Restricciones:

- `UNIQUE (anio, mes)`.
- `CHECK (mes BETWEEN 1 AND 12)`.
- `CHECK (anio BETWEEN 1900 AND 2100)`.
- Cada porcentaje entre 0 y 100.
- `porcentaje_necesario + porcentaje_no_necesario + porcentaje_inversion <= 100`.

La suma menor que 100 es válida y representa dinero sin asignar.

### 4.2 Migración `0007`

`0007_create_monthly_allocations`:

- Crea la tabla con constraints e índice único.
- `downgrade` elimina la tabla.
- La suite de integración actualiza la versión esperada a `0007`.

No se modifican las tablas `ingresos`, `gastos` ni `filas_importacion`.

## 5. Contrato de API

### 5.1 `GET /api/balance-mensual`

Parámetros opcionales:

| Parámetro | Tipo | Regla |
|---|---|---|
| `anio` | entero | 1900–2100; si falta, año actual. |
| `mes` | entero | 1–12; si falta, vista anual. |

Respuesta mensual `200`:

```json
{
  "anio": 2026,
  "mes": 10,
  "ingresos": "5000.00",
  "sin_asignar": "0.00",
  "rubros": {
    "NECESARIO": {
      "porcentaje": "50.00",
      "asignado": "2500.00",
      "gastado": "1000.00",
      "restante": "1500.00"
    },
    "NO_NECESARIO": {
      "porcentaje": "30.00",
      "asignado": "1500.00",
      "gastado": "300.00",
      "restante": "1200.00"
    },
    "INVERSION": {
      "porcentaje": "20.00",
      "asignado": "1000.00",
      "gastado": "200.00",
      "restante": "800.00"
    }
  },
  "movimientos": {
    "INGRESOS": [
      {
        "id": 1,
        "fecha": "2026-10-01",
        "descripcion": "Salario",
        "valor": "5000.00"
      }
    ],
    "NECESARIO": [
      {
        "id": 2,
        "fecha": "2026-10-02",
        "descripcion": "Mercado",
        "valor": "1000.00"
      }
    ],
    "NO_NECESARIO": [
      {
        "id": 3,
        "fecha": "2026-10-03",
        "descripcion": "Cine",
        "valor": "300.00"
      }
    ],
    "INVERSION": [
      {
        "id": 4,
        "fecha": "2026-10-04",
        "descripcion": "Fondo indexado",
        "valor": "200.00"
      }
    ]
  }
}
```

Respuesta anual `200`: misma estructura de `rubros` con `mes: null` y `porcentaje` ponderado. La respuesta anual no incluye `movimientos`.

Reglas:

- `rubros` contiene siempre los tres tipos.
- `movimientos` contiene las cuatro listas del mes, ordenadas por fecha e id.
- Cada item incluye `id`, `fecha`, `descripcion` y `valor`.
- Los importes y porcentajes son strings con dos decimales.
- `sin_asignar` es el remanente de los ingresos no asignados.
- El restante puede ser negativo.

### 5.2 `GET /api/balance-mensual/periodos`

Respuesta `200`:

```json
{
  "anio_actual": 2026,
  "anios": [2026, 2025]
}
```

Los años se obtienen de ingresos, gastos y asignaciones, y siempre incluyen el año actual. Se ordenan de forma descendente.

### 5.3 `PUT /api/balance-mensual/asignaciones/{anio}/{mes}`

Cuerpo:

```json
{
  "porcentajes": {
    "NECESARIO": "50.00",
    "NO_NECESARIO": "30.00",
    "INVERSION": "20.00"
  }
}
```

- Crea o actualiza la fila del mes.
- Responde `200` con el balance mensual actualizado.
- `422` si un porcentaje está fuera de rango, tiene más de dos decimales o la suma supera 100.
- No crea movimientos financieros.

## 6. Cálculos

### 6.1 Ingresos y gastos del periodo

Para un mes:

- Rango `[primer día del mes, primer día del mes siguiente)`.
- Ingresos: `SUM(ingresos.valor)`.
- Gastos: `SUM(gastos.valor) GROUP BY gastos.tipo`.

Para un año:

- Rango `[1 de enero, 1 de enero del año siguiente)`.
- Se agregan los mismos campos.

Se usan rangos de fecha para aprovechar los índices existentes.

### 6.2 Asignaciones

Con ingresos del periodo y porcentajes del mes:

```text
asignado_rubro = (ingresos * porcentaje_rubro / 100).quantize(Decimal("0.01"))
restante_rubro = asignado_rubro - gastado_rubro
sin_asignar = ingresos - suma(asignados)
```

`sin_asignar` se normaliza a `0.00` si el redondeo produce un valor negativo.

### 6.3 Vista anual

Para cada rubro:

```text
asignado_anual = suma(asignados_mensuales)
gastado_anual = suma(gastos_del_tipo_en_el_año)
restante_anual = asignado_anual - gastado_anual
porcentaje_ponderado = asignado_anual / ingresos_anuales * 100
```

Si `ingresos_anuales` es cero, el porcentaje ponderado es `0.00`.

El monto sin asignar anual es:

```text
sin_asignar_anual = ingresos_anuales - suma(asignados_anuales)
```

También se normaliza a `0.00` si el redondeo produce un negativo.

### 6.4 Normalización

- Importes y porcentajes se normalizan con `Decimal.quantize(Decimal("0.01"))`.
- No se usa `float`.
- Los DTOs serializan `Decimal` como string.

## 7. Persistencia y transacciones

- La consulta es de solo lectura.
- El guardado de porcentajes hace un upsert por `(anio, mes)`.
- Si ya existe la fila, actualiza los tres porcentajes.
- Si no existe, la crea.
- El commit se ejecuta después de validar; ante error se hace rollback.
- No se recalculan ni se almacenan montos asignados; se calculan al consultar para reflejar cambios de ingresos.

## 8. Cambios en el frontend

### 8.1 Navegación

`App` añade:

- `activeTab: 'incomes' | 'expenses' | 'monthly'`.
- Pestaña `Balance mensual` en el mismo `tablist`.
- Panel con `role="tabpanel"` y `aria-labelledby`.

### 8.2 `MonthlyBalanceView`

Responsabilidades:

- Cargar periodos disponibles al montar.
- Mantener año seleccionado, mes seleccionado y balance actual.
- Consultar el balance al cambiar de periodo.
- Mostrar selectores de año y mes.
- Mostrar la vista mensual en cuatro columnas: ingresos, gastos necesarios, gastos no necesarios e inversión.
- Mostrar los movimientos de cada columna con fecha, descripción y valor.
- Mostrar el total de cada columna y los restantes de los tres rubros.
- Mostrar el total de ingresos y el monto sin asignar.
- En vista mensual, permitir editar los tres porcentajes.
- Guardar porcentajes con un botón explícito.
- Mostrar carga, error, vacío, validación y confirmación de guardado.
- Reintentar la consulta sin perder los datos ya cargados.

### 8.3 Tablas

Vista mensual: cuatro columnas alineadas.

| Ingresos | Gastos necesarios | Gastos no necesarios | Inversión |
|---|---|---|---|
| Fecha · Descripción · Valor | Fecha · Descripción · Valor | Fecha · Descripción · Valor | Fecha · Descripción · Valor |
| Total ingresos | Total gastos necesarios | Total gastos no necesarios | Total inversión |
| Sin asignar | Presupuesto y restante | Presupuesto y restante | Presupuesto y restante |

La columna de ingresos no tiene porcentaje ni restante propio; muestra su total y el monto sin asignar. Las tres columnas restantes muestran el porcentaje asignado, el monto asignado, el total real y el restante.

Vista anual: tabla agregada.

| Rubro | Porcentaje ponderado | Asignado | Gastado | Restante |
|---|---|---|---|---|

La fila de inversión se etiqueta `Inversión` y usa el tipo `INVERSION`. En pantallas estrechas, las cuatro columnas se apilan verticalmente sin perder los subtotales.

### 8.4 Cliente API

`frontend/src/api/monthlyBalance.ts`:

- `getPeriods(signal?)`.
- `getMonthlyBalance(anio, mes, signal?)`.
- `getAnnualBalance(anio, signal?)`.
- `updateAllocations(anio, mes, porcentajes)`.

Se usa `request` de `client.ts`; no se hardcodean URLs absolutas.

### 8.5 Estilos

Reutilizar:

- `field`, `button`, `form-error`, `status-message`, `empty-state`.
- Estructura de tabla existente con contenedor `overflow-x: auto`.

Añadir solo las clases necesarias para el selector de periodo y la tabla de balance.

## 9. Estrategia de pruebas

### Unitarias backend

- Cálculo de asignado y restante.
- Cálculo de sin asignar.
- Porcentaje ponderado anual.
- Periodo sin ingresos.
- Restante negativo.
- Agrupación y orden de movimientos por fecha e id.
- Serialización de schemas.

### API backend

- `GET /api/balance-mensual` sin parámetros usa año actual.
- `GET` mensual y anual.
- `GET /api/balance-mensual/periodos`.
- `PUT` crea y actualiza asignaciones.
- `422` por porcentajes inválidos o suma mayor que 100.
- OpenAPI de las rutas nuevas.

### Integración backend

- Ingresos y gastos de varios meses y años.
- Listas de movimientos por columna con fecha, descripción y valor.
- Rubros con ceros y columnas vacías.
- Asignaciones independientes por mes.
- Suma menor que 100 y monto sin asignar.
- Restante negativo.
- Inversión con gastos `INVERSION`.
- Porcentaje anual ponderado.
- Año actual y años disponibles.
- Migración `0007` y downgrade.

### Frontend

- Cliente API con `fetch` simulado.
- Selectores y cambio de periodo.
- Vista mensual de cuatro columnas con fecha, descripción y valor.
- Tabla anual agregada.
- Edición y guardado de porcentajes.
- Validación de suma mayor que 100.
- Estado vacío, carga, error y reintento.
- Pestaña en `App`.
- Formato COP.

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Redondeo de centavos al repartir porcentajes. | Normalizar con `Decimal` y ajustar `sin_asignar` a cero si queda negativo. |
| Meses sin ingresos con gastos. | Asignado `0.00` y restante negativo explícito. |
| Porcentajes que suman más de 100. | Validación en schema y en servicio; `422`. |
| Cambios de ingresos posteriores. | Calcular montos al consultar, no almacenarlos. |
| Consultas lentas por año. | Usar rangos de fecha e índices existentes. |
| Duplicados de asignación. | Restricción única `(anio, mes)` y upsert. |
| Regresión del resumen global. | No modificar `/api/resumen`; pruebas existentes. |

## 11. Trazabilidad requisitos → plan → tareas

| Requisito | Secciones del plan | Tareas |
|---|---|---|
| FR-001 | 8.1 | T-008 |
| FR-002 | 5.1, 8.2 | T-007, T-008 |
| FR-003 | 5.1, 8.3 | T-007 |
| FR-004 | 5.3, 8.2 | T-005, T-008 |
| FR-005 | 6.2 | T-002, T-007 |
| FR-006 | 6.2 | T-002, T-007 |
| FR-007 | 6.1, 6.2 | T-002, T-009 |
| FR-008 | 6.2, 8.2 | T-002, T-007 |
| FR-009 | 6.3, 8.3 | T-002, T-004, T-007 |
| FR-010 | 5.1, 8.2 | T-004, T-007 |
| FR-011 | 4.1, 5.3 | T-001, T-005 |
| FR-012 | 5.3, 6.4 | T-003, T-005 |
| FR-013 | 5.2 | T-002, T-004 |
| FR-014 | 5 | T-004, T-005 |
| FR-015 | 5.1 | T-003, T-004 |
| FR-016 | 5.1, 6.3 | T-003, T-004 |
| FR-017 | 8.2 | T-007, T-008 |
| FR-018 | 7, 9 | T-009, T-010 |
| NFR-001 | 6.4 | T-002, T-003 |
| NFR-002 | 6.1 | T-002, T-004 |
| NFR-003 | 3, 5 | T-003, T-004, T-005 |
| NFR-004 | 9 | T-009, T-010 |
| NFR-005 | 8.2, 8.3 | T-007, T-008 |
| NFR-006 | 1, 3 | T-010 |
| NFR-007 | 7, 9 | T-009, T-010 |
| NFR-008 | 1, 7 | T-010 |

## 12. Aprobación y siguiente paso

Las decisiones D-001 a D-006 y el plan están aprobados. La implementación avanza por las tareas de `tasks.md`.

No se modifica `legacy/`, no se altera el resumen global y no se añaden dependencias.
