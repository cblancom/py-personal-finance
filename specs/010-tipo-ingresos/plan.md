# Plan técnico 010 — Tipo opcional de ingresos

- Estado: validado (T-001 a T-008 completadas).
- Especificación: [`spec.md`](spec.md).
- Fase: 8.
- Iteración: 1.2.

## 1. Resumen de la solución

La entrega reemplaza `ingresos.categoria` por `ingresos.tipo`, un enum nullable con los mismos valores de gastos. Los ingresos sin tipo mantienen el reparto porcentual actual. Los ingresos tipados se excluyen de la base porcentual y se suman al disponible del rubro correspondiente en el mes de su fecha.

La solución incluye:

- Migración destructiva `0008_add_income_type`.
- Cambio del contrato de ingresos de `categoria` a `tipo`.
- Ajuste de los cálculos mensuales y anuales de balance.
- Nuevo campo `ingresos_tipados` por rubro.
- Formulario, listado y vista de balance actualizados.
- Importación de ingresos con `Categoría`/`Tipo` interpretada como tipo.
- Pruebas unitarias, API, integración, OpenAPI, componentes y regresión.
- Actualización de documentación y versión `1.2.0`.

No se añaden dependencias.

## 2. Relación con las especificaciones existentes

| Especificación | Relación |
|---|---|
| 002-api-ingresos | Cambia el contrato de `categoria` a `tipo`; el resto del CRUD se mantiene. |
| 003-api-gastos | Se reutilizan los valores de tipo; no cambia el contrato de gastos. |
| 007-importacion-movimientos | Sustituye D-002 para ingresos: la categoría importada se interpreta como tipo opcional. |
| 008-balance-mensual | Extiende los cálculos y el contrato de rubros con ingresos tipados. |
| 009-graficas-gastos | Sin cambios. |

Las especificaciones históricas no se reescriben. Esta especificación documenta las cláusulas sustituidas.

## 3. Arquitectura y flujo de datos

```text
Ingreso manual / importación
        │
        │ tipo: null | NECESARIO | NO_NECESARIO | INVERSION
        ▼
PostgreSQL: ingresos.tipo
        │
        ▼
Monthly balance
  ├── ingresos sin tipo ──► base porcentual ──► asignado
  └── ingresos tipados ───────────────────────► ingresos_tipados
                                                 │
                                                 ▼
                                   disponible = asignado + arrastre + ingresos_tipados
                                                 │
                                                 ▼
                                      restante = disponible - gastado
                                                 │
                                                 ▼
                                          arrastre siguiente mes
```

Flujo mensual:

1. Se agregan los ingresos del mes separando `tipo IS NULL` y cada tipo.
2. Se leen los porcentajes mensuales.
3. Se calcula el asignado solo con ingresos sin tipo.
4. Se calcula el arrastre desde el primer mes con datos.
5. Se suma el ingreso tipado al disponible de su rubro.
6. Se calcula el restante y se usa en la cadena del mes siguiente.
7. Se calcula `sin_asignar` solo con ingresos sin tipo.

Flujo anual:

1. Se ejecuta la cadena de los doce meses.
2. Se suman asignados base, ingresos tipados, gastos y restantes.
3. Se calcula el arrastre anual con las reglas de la revisión 3.
4. Se calcula el disponible anual como asignado + arrastre + ingresos tipados.
5. Se calcula el porcentaje ponderado sobre ingresos sin tipo.

## 4. Modelo de datos y migración

### Tabla `ingresos`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `INTEGER` | PK, autoincremental |
| `fecha` | `DATE` | `NOT NULL` |
| `descripcion` | `VARCHAR(200)` | `NOT NULL` |
| `tipo` | `VARCHAR(20)` | `NULL` o uno de los tres tipos |
| `valor` | `NUMERIC(12,2)` | `NOT NULL` |

Restricción:

```text
tipo IS NULL OR tipo IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')
```

La columna `categoria` se elimina.

### Tabla `filas_importacion`

Se añade:

| Columna | Tipo | Restricciones |
|---|---|---|
| `tipo` | `VARCHAR(20)` | `NULL` o uno de los tres tipos |

La columna existente `categoria` se conserva para auditoría del texto original. `tipo_gasto` se mantiene para la importación de gastos.

Restricción:

```text
tipo IS NULL OR tipo IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')
```

### Migración `0008_add_income_type`

`upgrade`:

1. Añadir `ingresos.tipo` nullable.
2. Mapear valores históricos exactos de `categoria`:
   - `necesario` → `NECESARIO`
   - `no necesario` → `NO_NECESARIO`
   - `inversion` → `INVERSION`
   - Cualquier otro valor queda en `NULL`.
3. Eliminar `ingresos.categoria`.
4. Añadir la restricción de `ingresos.tipo`.
5. Añadir `filas_importacion.tipo` nullable.
6. Añadir la restricción de `filas_importacion.tipo`.

`downgrade`:

1. Eliminar `filas_importacion.tipo`.
2. Añadir `ingresos.categoria` como `VARCHAR(100)` nullable.
3. Eliminar `ingresos.tipo`.

La migración es reversible en estructura, pero no recupera las categorías históricas que no coincidían con un tipo. Antes de ejecutarla en producción se debe hacer respaldo y obtener autorización explícita.

### Modelo SQLAlchemy

`Income` cambia `category` por `income_type`:

```python
income_type: Mapped[str | None] = mapped_column("tipo", String(20), nullable=True)
```

`ImportRow` añade `income_type` mapeado a `tipo`, manteniendo `category` y `expense_type`.

## 5. Contrato de API

### Ingresos

Request de creación/edición:

```json
{
  "fecha": "2026-10-01",
  "descripcion": "Salario",
  "tipo": "NO_NECESARIO",
  "valor": "3000.00"
}
```

`tipo` puede omitirse o enviarse como `null`.

Response:

```json
{
  "id": 1,
  "fecha": "2026-10-01",
  "descripcion": "Salario",
  "tipo": "NO_NECESARIO",
  "valor": "3000.00"
}
```

Reglas:

- `tipo` usa el enum de los tres rubros.
- Vacío o solo espacios se normaliza a `null`.
- Un valor desconocido devuelve `422`.
- `categoria` desaparece del schema.

### Balance mensual y anual

Cada rubro añade `ingresos_tipados`:

```json
{
  "porcentaje": "30.00",
  "asignado": "1500.00",
  "arrastre": "0.00",
  "ingresos_tipados": "500.00",
  "disponible": "2000.00",
  "gastado": "300.00",
  "restante": "1700.00"
}
```

Invariante:

```text
disponible = asignado + arrastre + ingresos_tipados
```

`sin_asignar` no incluye ingresos tipados. `incomes` sigue siendo el total de ingresos del periodo.

## 6. Cálculo mensual

```text
ingresos_sin_tipo = suma(ingresos del mes donde tipo IS NULL)
ingresos_tipados[t] = suma(ingresos del mes donde tipo = t)
ingresos_totales = ingresos_sin_tipo + suma(ingresos_tipados)

asignado[t] = ingresos_sin_tipo * porcentaje[t] / 100
disponible[t] = asignado[t] + arrastre[t] + ingresos_tipados[t]
restante[t] = disponible[t] - gastado[t]
sin_asignar = max(ingresos_sin_tipo - suma(asignado), 0)
```

El arrastre se calcula con la misma cadena de la revisión 3:

```text
arrastre[NECESARIO] = 0
arrastre[NO_NECESARIO] = restante[NECESARIO] anterior
                        + restante[NO_NECESARIO] anterior
arrastre[INVERSION] = restante[INVERSION] anterior
```

Los ingresos tipados `NECESARIO` aumentan el restante de necesarios y, por tanto, la transferencia al siguiente mes de no necesarios.

## 7. Cálculo anual

```text
asignado_anual[t] = suma(asignado_mensual[t])
ingresos_tipados_anual[t] = suma(ingresos_tipados_mensual[t])
gastado_anual[t] = suma(gastos del tipo en el año)

disponible_anual[t] = asignado_anual[t]
                    + arrastre_anual[t]
                    + ingresos_tipados_anual[t]

restante_anual[NECESARIO] = asignado_anual[NECESARIO]
                          + ingresos_tipados_anual[NECESARIO]
                          - gastado_anual[NECESARIO]

restante_anual[NO_NECESARIO] = disponible_anual[NO_NECESARIO]
                             - gastado_anual[NO_NECESARIO]

restante_anual[INVERSION] = disponible_anual[INVERSION]
                          - gastado_anual[INVERSION]

porcentaje_ponderado[t] = asignado_anual[t]
                        / ingresos_sin_tipo_anuales
                        * 100
```

Si no hay ingresos sin tipo, el porcentaje ponderado es `0.00`.

El `arrastre_anual` de no necesarios incluye el saldo inicial de enero y las transferencias de necesarios del año, que ahora incluyen los ingresos tipados de necesarios.

## 8. Componentes y responsabilidades

### Backend

| Archivo | Cambio |
|---|---|
| `backend/app/db/models/income.py` | Reemplazar `category` por `income_type` mapeado a `tipo`. |
| `backend/app/db/models/import_row.py` | Añadir `income_type` mapeado a `tipo`. |
| `backend/alembic/versions/0008_add_income_type.py` | Migración destructiva y reversible en estructura. |
| `backend/app/api/schemas/income.py` | `tipo` opcional; eliminar `categoria`. |
| `backend/app/api/routes/incomes.py` | Mapear `income_type` y `tipo`. |
| `backend/app/services/monthly_balance.py` | Separar ingresos tipados, ajustar contrato y cálculos. |
| `backend/app/api/schemas/monthly_balance.py` | Añadir `ingresos_tipados` a `BalanceRubroRead`. |
| `backend/app/api/routes/monthly_balance.py` | Mapear el nuevo campo. |
| `backend/app/services/imports/normalization.py` | Normalizar tipo de ingreso con los alias existentes. |
| `backend/app/services/imports/validation.py` | Validar tipo de ingreso y dejar pendientes los desconocidos. |
| `backend/app/services/imports/importer.py` | Crear `Income` con `income_type`; guardar tipo en la fila. |
| `backend/app/services/imports/pending.py` | Actualizar y contabilizar el tipo de ingreso. |
| `backend/app/api/schemas/imports.py` | Exponer y aceptar `tipo` en pendientes de ingreso. |
| `backend/app/api/routes/imports.py` | Mapear el nuevo campo. |

### Frontend

| Archivo | Cambio |
|---|---|
| `frontend/src/types/income.ts` | `tipo` opcional; eliminar `categoria`. |
| `frontend/src/components/IncomeForm.tsx` | Selector `Tipo (opcional)`. |
| `frontend/src/components/IncomeList.tsx` | Columna `Tipo`. |
| `frontend/src/components/IncomeSection.tsx` | Sin cambios de lógica salvo tipos. |
| `frontend/src/types/monthlyBalance.ts` | Añadir `ingresos_tipados`. |
| `frontend/src/components/MonthlyBalanceView.tsx` | Mostrar ingresos tipados y nota explicativa. |
| `frontend/src/types/import.ts` | Añadir `tipo` a pendientes de ingreso. |
| `frontend/src/components/PendingView.tsx` | Selector de tipo para ingresos. |
| `frontend/src/index.css` | Ajustes de tabla/nota si son necesarios. |

### Pruebas

| Archivo | Cambio |
|---|---|
| `backend/tests/api/test_income_schemas.py` | `tipo` opcional, enum, vacío y errores. |
| `backend/tests/integration/test_incomes.py` | CRUD con tipo y restricción de base. |
| `backend/tests/core/test_monthly_balance.py` | Cálculo con ingresos tipados. |
| `backend/tests/integration/test_monthly_balance.py` | Mensual, anual, arrastre y regresión. |
| `backend/tests/api/test_monthly_balance_schema.py` | Contrato con `ingresos_tipados`. |
| `backend/tests/core/test_import_normalization.py` | Normalización de tipo de ingreso. |
| `backend/tests/core/test_import_validation.py` | Tipo válido, vacío y desconocido. |
| `backend/tests/integration/test_imports_api.py` | Importación y pendientes con tipo. |
| `frontend/src/components/IncomeForm.test.tsx` | Selector y payload. |
| `frontend/src/components/IncomeList.test.tsx` | Columna de tipo. |
| `frontend/src/components/MonthlyBalanceView.test.tsx` | Ingresos tipados y nota. |
| `frontend/src/components/PendingView.test.tsx` | Selector de tipo en ingresos. |
| `frontend/src/api/incomes.test.ts` | Contrato con `tipo`. |
| `frontend/src/api/monthlyBalance.test.ts` | Fixtures con `ingresos_tipados`. |

## 9. Importación de ingresos

La importación de ingresos sigue este flujo:

1. El parser conserva el texto de `Categoría`/`Tipo` en `ParsedRow.categoria`.
2. La validación normaliza el valor con los alias de tipo:
   - `necesario` → `NECESARIO`
   - `no necesario` → `NO_NECESARIO`
   - `inversion` → `INVERSION`
3. Si el valor está vacío, `income_type = None`.
4. Si el valor no es reconocido, se añade un error en `tipo` y la fila queda pendiente.
5. La fila guarda el texto original en `categoria` y el tipo en `tipo`.
6. Al contabilizar, se crea `Income(income_type=...)`.
7. La UI de pendientes muestra `Tipo (opcional)` para ingresos y conserva `Tipo de gasto` para gastos.

La importación de gastos no cambia.

## 10. Pruebas y verificación

### Backend

```bash
cd backend
uv run --env-file ../.env pytest
uv run ruff check .
uv run ruff format --check .
```

Casos mínimos:

- Migración `0008` y `downgrade`.
- `tipo` nullable y restricción de base.
- CRUD de ingresos con tipo.
- Ingresos sin tipo sin regresión.
- Ingresos tipados en balance mensual y anual.
- `sin_asignar` sin ingresos tipados.
- Arrastre con ingresos tipados.
- Importación válida, vacía y desconocida.
- Pendientes y commit de ingresos tipados.
- Resumen y gráficas sin regresión.
- OpenAPI con el nuevo contrato.

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

Casos mínimos:

- Selector de tipo y payload.
- Listado con tipo.
- Balance mensual y anual con ingresos tipados.
- Nota explicativa.
- Pendientes con selector de tipo.
- Fixtures de API actualizados.

### Producción

```bash
docker compose --env-file .env.production -f compose.prod.yaml config -q
docker compose --env-file .env.production -f compose.prod.yaml up --build -d
WEB_PORT=3001 ./scripts/smoke.sh
```

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Pérdida de categorías históricas | Respaldo previo; mapear solo valores exactos; documentar la pérdida. |
| Doble conteo del ingreso tipado | Excluirlo de la base porcentual y de `sin_asignar`; invariante `disponible = asignado + arrastre + ingresos_tipados`. |
| Porcentaje ponderado engañoso | Usar ingresos sin tipo como denominador y documentarlo. |
| Importaciones antiguas con categorías libres | Quedan pendientes para corrección; el texto original se conserva en auditoría. |
| Regresión del balance | Pruebas de ingresos sin tipo y suite completa. |
| Migración destructiva en producción | Respaldo, autorización explícita y validación en base de test. |

## 12. Archivos afectados

- `backend/app/db/models/income.py`
- `backend/app/db/models/import_row.py`
- `backend/alembic/versions/0008_add_income_type.py`
- `backend/app/api/schemas/income.py`
- `backend/app/api/routes/incomes.py`
- `backend/app/services/monthly_balance.py`
- `backend/app/api/schemas/monthly_balance.py`
- `backend/app/api/routes/monthly_balance.py`
- `backend/app/services/imports/normalization.py`
- `backend/app/services/imports/validation.py`
- `backend/app/services/imports/importer.py`
- `backend/app/services/imports/pending.py`
- `backend/app/api/schemas/imports.py`
- `backend/app/api/routes/imports.py`
- `frontend/src/types/income.ts`
- `frontend/src/components/IncomeForm.tsx`
- `frontend/src/components/IncomeList.tsx`
- `frontend/src/types/monthlyBalance.ts`
- `frontend/src/components/MonthlyBalanceView.tsx`
- `frontend/src/types/import.ts`
- `frontend/src/components/PendingView.tsx`
- Pruebas backend y frontend correspondientes.
- `README.md`, `AGENTS.md`, `specs/README.md`, metadatos de versión.

## 13. Aprobación y siguiente paso

La especificación 010 está aprobada en sus decisiones D-001 a D-006. El plan fue aprobado y T-001 a T-008 quedaron completadas y validadas.

No se modifica `legacy/`. No se añaden dependencias. No se altera el resumen global ni las gráficas.
