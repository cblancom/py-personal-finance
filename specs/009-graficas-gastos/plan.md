# Plan técnico 009 — Gráficas de gastos mensuales

- Estado: aprobado (implementado y validado).
- Especificación: [`spec.md`](spec.md).
- Fase: 7.
- Iteración: versión 1.0.

## 1. Resumen de la solución

Se añade una sección de gráficas en la pantalla principal, entre el resumen y las pestañas de movimientos.

La sección:

- Consulta los gastos de un año agrupados por mes y tipo.
- Muestra barras apiladas por defecto.
- Permite cambiar a tres líneas continuas.
- Incluye selector de año, leyenda, tooltips, estado vacío y tabla de datos accesible.
- Usa Recharts.
- No crea tablas ni migraciones.
- No modifica las APIs existentes.

## 2. Arquitectura y flujo

```text
App
  ├── SummaryPanel
  ├── ChartSection
  │     ├── GET /api/graficos/gastos-mensuales?anio=2026
  │     ├── selector de año
  │     ├── toggle Barras / Líneas
  │     └── ExpenseChart (Recharts)
  └── tabs + formularios
```

Flujo:

1. `ChartSection` carga los años disponibles.
2. Selecciona el año actual por defecto.
3. Consulta la serie mensual.
4. Convierte los importes a números solo para las coordenadas de Recharts.
5. Renderiza `BarChart` o `LineChart` según el modo.
6. Se refresca cuando `App` cambia `loadVersion` después de una mutación.

## 3. Componentes y responsabilidades

| Archivo | Responsabilidad |
|---|---|
| `backend/app/services/charts.py` | Agregación mensual por tipo y año. |
| `backend/app/api/schemas/charts.py` | DTOs de la serie mensual. |
| `backend/app/api/routes/charts.py` | Endpoint `/graficos/gastos-mensuales`. |
| `backend/app/main.py` | Registro del router. |
| `frontend/src/types/charts.ts` | Tipos del contrato. |
| `frontend/src/api/charts.ts` | Cliente de la serie mensual. |
| `frontend/src/components/ChartSection.tsx` | Selector de año, toggle, carga y estados. |
| `frontend/src/components/ExpenseChart.tsx` | Renderizado Recharts de barras/líneas. |
| `frontend/src/components/ChartDataTable.tsx` | Tabla accesible alternativa. |
| `frontend/src/App.tsx` | Posición de la sección y refresco. |
| `frontend/src/index.css` | Estilos de la sección y la tabla. |

## 4. Contrato de API

### `GET /api/graficos/gastos-mensuales`

Parámetro opcional:

| Parámetro | Tipo | Regla |
|---|---|---|
| `anio` | entero | 1900–2100; si falta, año actual. |

Respuesta `200`:

```json
{
  "anio": 2026,
  "meses": [
    {
      "mes": 1,
      "gastos_por_tipo": {
        "NECESARIO": "100.00",
        "NO_NECESARIO": "50.00",
        "INVERSION": "20.00"
      }
    },
    {
      "mes": 2,
      "gastos_por_tipo": {
        "NECESARIO": "0.00",
        "NO_NECESARIO": "0.00",
        "INVERSION": "0.00"
      }
    }
  ]
}
```

Reglas:

- Siempre contiene los doce meses.
- `gastos_por_tipo` contiene siempre los tres tipos.
- Los importes son strings con dos decimales.
- No incluye ingresos.
- `422` si `anio` está fuera de rango.

## 5. Agregación backend

El servicio `get_monthly_expense_series`:

1. Calcula el rango `[1 de enero, 1 de enero del año siguiente)`.
2. Ejecuta una consulta:

```python
select(
    func.extract("month", Expense.date),
    Expense.expense_type,
    func.sum(Expense.amount),
).where(
    Expense.date >= start,
    Expense.date < end,
).group_by(
    func.extract("month", Expense.date),
    Expense.expense_type,
)
```

3. Inicializa los doce meses con los tres tipos en `0.00`.
4. Rellena los valores agregados.
5. Devuelve la serie ordenada de enero a diciembre.

No se cargan gastos individuales en memoria para calcular la gráfica.

## 6. Frontend

### 6.1 `ChartSection`

Responsabilidades:

- Cargar años con `getPeriods` de la spec 008.
- Mantener el año seleccionado.
- Mantener el modo `bars` o `lines`.
- Consultar `getMonthlyExpenseSeries(anio)`.
- Mostrar carga, error con reintento y estado vacío.
- Mostrar selector de año.
- Mostrar toggle `Barras` / `Líneas`.
- Pasar los datos a `ExpenseChart`.
- Mostrar u ocultar la tabla de datos.
- Refrescar cuando cambie `refreshKey`.

### 6.2 `ExpenseChart`

Usa Recharts:

- `ResponsiveContainer` con altura fija.
- `CartesianGrid`.
- `XAxis` con meses abreviados.
- `YAxis` con formato compacto de COP.
- `Tooltip` con valor completo en COP.
- `Legend`.

Modo barras:

```tsx
<BarChart data={data}>
  <Bar dataKey="NECESARIO" stackId="gastos" fill="var(--chart-necessary)" />
  <Bar dataKey="NO_NECESARIO" stackId="gastos" fill="var(--chart-non-necessary)" />
  <Bar dataKey="INVERSION" stackId="gastos" fill="var(--chart-investment)" />
</BarChart>
```

Modo líneas:

```tsx
<LineChart data={data}>
  <Line type="monotone" dataKey="NECESARIO" stroke="var(--chart-necessary)" />
  <Line type="monotone" dataKey="NO_NECESARIO" stroke="var(--chart-non-necessary)" />
  <Line type="monotone" dataKey="INVERSION" stroke="var(--chart-investment)" />
</LineChart>
```

Los datos de Recharts usan números para las coordenadas. Los strings originales se conservan en el contrato y en la tabla de datos.

### 6.3 `ChartDataTable`

- Tabla con mes y los tres tipos.
- Importes formateados con `formatMoney`.
- Visible bajo `Ver datos`.
- Sirve como alternativa accesible a la gráfica.

### 6.4 Integración en `App`

- Insertar `ChartSection` después de `SummaryPanel` y antes del tablist.
- Pasar `refreshKey={loadVersion}`.
- La gráfica no bloquea el resto de la pantalla si falla su carga.

### 6.5 Estilos

- Mantener la estética editorial existente: reglas finas, sin sombras ni gradientes.
- Colores de series desde tokens CSS.
- Leyenda y tooltips legibles.
- Responsive con `ResponsiveContainer`.
- Respetar `prefers-reduced-motion`.

## 7. Dependencias frontend

Añadir:

- `recharts@3.10.1`.
- `react-is@19.3.1` para satisfacer el peer dependency de Recharts con React 19.

Actualizar `package-lock.json` con `npm install`.

No se añaden dependencias backend.

## 8. Pruebas

### Backend

- Schema de la serie mensual.
- OpenAPI.
- Agregación con varios meses y tipos.
- Meses sin datos en cero.
- Filtro por año.
- Año inválido `422`.
- Una sola consulta agregada, sin cargar gastos individuales.

### Frontend

- Cliente API.
- `ChartSection`: carga, error, vacío, selector y toggle.
- `ExpenseChart`: barras y líneas con datos.
- Tabla accesible.
- `App`: posición y refresco.
- Mock de `ResizeObserver` para Recharts en Vitest.

## 9. Metadatos y release 1.0.0

Actualizar de forma coordinada:

| Archivo | Cambio |
|---|---|
| `frontend/package.json` | `version: "1.0.0"`, `recharts`, `react-is` |
| `frontend/package-lock.json` | Versión y dependencias actualizadas con `npm install` |
| `backend/pyproject.toml` | `version = "1.0.0"` |
| `backend/uv.lock` | Versión del paquete actualizada con `uv lock` |
| `backend/app/main.py` | `FastAPI(..., version="1.0.0")` |
| `README.md` | Uso, API de gráficas y release 1.0.0 |

No se crea un archivo `VERSION` ni un `CHANGELOG.md` salvo que se solicite.

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Recharts no renderiza en jsdom | Mock de `ResizeObserver` y pruebas centradas en datos/estado. |
| Importes como strings en Recharts | Convertir solo para coordenadas; tabla y tooltip usan strings formateados. |
| Gráfica vacía por año sin datos | Estado vacío explícito. |
| Muchos gastos | Agregación SQL por mes y tipo. |
| Cambio de año durante carga | AbortController y cancelación de la petición anterior. |
| Dependencia nueva | Versión aprobada y justificada; sin dependencias backend. |
| Regresión del resumen | No modificar APIs existentes; pruebas completas. |

## 11. Trazabilidad requisitos → plan → tareas

| Requisito | Secciones del plan | Tareas |
|---|---|---|
| FR-001 | 6.4 | T-005 |
| FR-002 | 4, 5 | T-001, T-002 |
| FR-003 | 5 | T-001, T-002 |
| FR-004 | 6.2 | T-003 |
| FR-005 | 6.2 | T-003 |
| FR-006 | 6.1, 6.2 | T-003, T-004 |
| FR-007 | 6.1 | T-004 |
| FR-008 | 6.2 | T-003 |
| FR-009 | 6.3 | T-004 |
| FR-010 | 6.1 | T-004 |
| FR-011 | 6.4 | T-005 |
| FR-012 | 2, 8 | T-006 |
| FR-013 | 9 | T-007 |
| NFR-001 | 5, 6.2 | T-001, T-003 |
| NFR-002 | 5 | T-001 |
| NFR-003 | 7 | T-007 |
| NFR-004 | 6.2, 6.3 | T-003, T-004 |
| NFR-005 | 6.5 | T-003, T-005 |
| NFR-006 | 1, 5 | T-001, T-006 |
| NFR-007 | 8 | T-006 |
| NFR-008 | 1 | T-007 |

## 12. Aprobación y siguiente paso

Las decisiones D-001 a D-005 y el plan están aprobados. La implementación avanza por las tareas de `tasks.md`.

No se modifica `legacy/`, no se altera el resumen global y no se añaden dependencias backend.
