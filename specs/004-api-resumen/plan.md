# Plan técnico 004 — API de resumen

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Fase: 2.
- Iteración: MVP.

## 1. Resumen de la solución

La Fase 2 añade un endpoint de solo lectura, `GET /api/resumen`, que agrega los datos existentes de `ingresos` y `gastos`.

La implementación:

- Ejecuta `SUM` y `GROUP BY` directamente en PostgreSQL.
- Normaliza los importes a dos decimales.
- Devuelve strings decimales para conservar precisión.
- Incluye los tres tipos de gasto, incluso con valor cero.
- No crea tablas, migraciones ni dependencias nuevas.

El endpoint es global. El filtro mensual queda para una iteración posterior.

## 2. Arquitectura y flujo de datos

```text
Cliente / futuro frontend
        │
        │  GET /api/resumen
        ▼
FastAPI (router de resumen)
        │
        │  SQL: SUM(ingresos), SUM(gastos) GROUP BY tipo
        ▼
PostgreSQL
        │
        ▼
SummaryResponse
  ├── total_ingresos
  ├── total_gastos
  ├── balance
  └── gastos_por_tipo
```

Flujo:

1. La ruta recibe la sesión de base de datos.
2. Suma todos los ingresos con `func.sum`.
3. Agrupa los gastos por `tipo` y suma `valor`.
4. Completa los tipos ausentes con cero.
5. Calcula `total_gastos` como la suma del desglose.
6. Calcula `balance = total_ingresos - total_gastos`.
7. Normaliza los importes y construye el DTO.
8. Responde `200` con strings decimales.

## 3. Componentes y responsabilidades

| Ruta | Responsabilidad |
|---|---|
| `backend/app/api/schemas/summary.py` | `SummaryResponse` y contrato de salida. |
| `backend/app/api/routes/summary.py` | Agregaciones, normalización y endpoint `/resumen`. |
| `backend/app/main.py` | Registrar el router del resumen bajo `/api`. |
| `backend/tests/api/test_summary_schema.py` | Serialización del contrato sin base de datos. |
| `backend/tests/api/test_summary_openapi.py` | Presencia del endpoint en OpenAPI. |
| `backend/tests/integration/test_summary.py` | Totales, balance, desglose y casos vacíos. |

No se modifica el modelo de datos.

## 4. Modelo de datos

No hay tablas nuevas.

Se reutilizan:

- `ingresos`: `id`, `fecha`, `descripcion`, `valor`.
- `gastos`: `id`, `fecha`, `descripcion`, `tipo`, `valor`.

No hay migración `0004`. La base de test permanece en la revisión `0003`.

## 5. Contrato de API

### `GET /api/resumen`

Sin parámetros, sin autenticación.

Respuesta `200`:

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

Reglas:

- `balance = total_ingresos - total_gastos`.
- `gastos_por_tipo` contiene siempre `NECESARIO`, `NO_NECESARIO` e `INVERSION`.
- Los tipos sin movimientos valen `"0.00"`.
- `total_gastos` es la suma de los tres valores del desglose.
- Todos los importes son strings con dos decimales.
- El balance puede ser negativo.

### Errores

- `200` con la base disponible.
- 5xx si PostgreSQL falla de forma inesperada.
- No se devuelve `404` por ausencia de movimientos.

## 6. Agregación y normalización

El esquema de respuesta será:

```python
class SummaryResponse(BaseModel):
    total_ingresos: Decimal
    total_gastos: Decimal
    balance: Decimal
    gastos_por_tipo: dict[ExpenseType, Decimal]
```

La ruta seguirá este flujo:

```python
total_incomes = db.scalar(select(func.sum(Income.amount)))
expense_rows = db.execute(
    select(Expense.expense_type, func.sum(Expense.amount)).group_by(
        Expense.expense_type
    )
).all()
```

Se construirá el desglose inicializando los tres tipos en cero:

```python
breakdown = {expense_type: Decimal("0.00") for expense_type in ExpenseType}
for expense_type, total in expense_rows:
    breakdown[ExpenseType(expense_type)] = as_money(total)
```

Luego:

```python
total_expenses = sum(breakdown.values(), Decimal("0.00"))
balance = as_money(total_incomes) - total_expenses
```

La función `as_money`:

- Convierte `None` a `Decimal("0.00")`.
- Normaliza a dos decimales con `.quantize(Decimal("0.01"))`.
- Nunca usa `float`.

Pydantic serializa:

- `Decimal` como string.
- Las claves `ExpenseType` como sus valores `NECESARIO`, `NO_NECESARIO` e `INVERSION`.

La serialización de `dict[ExpenseType, Decimal]` ya se verificó con Pydantic: produce las claves y strings esperados.

## 7. Persistencia y transacciones

- La ruta recibe una sesión mediante `get_db`.
- Solo ejecuta lecturas; no hace `commit`.
- La sesión se cierra al terminar la petición.
- No se implementa caché.
- No se implementa bloqueo ni una foto transaccional estricta; el MVP es de un solo usuario.
- No se cargan movimientos individuales en memoria.

## 8. Estrategia de pruebas

### Unitarias

- Serialización de `SummaryResponse`:
  - Claves en español.
  - Valores decimales como strings.
  - Desglose con los tres tipos.
  - Balance negativo.
- OpenAPI:
  - `/api/resumen` presente.

### Integración

Se crean datos a través de las APIs de ingresos y gastos y se consulta el resumen.

Casos:

- Base vacía: todos los valores `"0.00"`.
- Solo ingresos: `total_gastos` y desglose en cero.
- Solo gastos: `total_ingresos` en cero.
- Mezcla de ingresos y gastos: totales y balance correctos.
- Balance negativo.
- Varios movimientos del mismo tipo.
- Un solo tipo de gasto: los otros dos en cero.
- Importes con decimales.
- `total_gastos` igual a la suma del desglose.
- Respuesta con todas las claves y tipos de dato esperados.

La suite reutiliza `personal_finance_test`, el fixture `reset_movements` y las rutas existentes. No se modifica el esquema.

## 9. Infraestructura y documentación

- No se añaden dependencias.
- No se crean migraciones.
- Actualizar README con:
  - Endpoint `/api/resumen`.
  - Ejemplo de respuesta.
  - Reglas del balance y del desglose.
- Actualizar AGENTS y `specs/README.md`.
- La validación final ejecuta la suite completa, el frontend y Docker Compose.

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| `SUM` devuelve `None` sin movimientos. | Normalizar `None` a `Decimal("0.00")`. |
| Los importes pierden los dos decimales. | `quantize(Decimal("0.01"))` antes de responder. |
| Un tipo de gasto falta en el resultado. | Inicializar los tres valores del enum en cero. |
| `total_gastos` no coincide con el desglose. | Calcularlo sumando el desglose. |
| Conversión incorrecta del tipo almacenado. | Convertir con `ExpenseType(value)`; el check de base impide valores inválidos. |
| Lecturas concurrentes inconsistentes. | Aceptado para un MVP de un solo usuario. |
| Agregación costosa con muchos datos. | `SUM`/`GROUP BY` en PostgreSQL; el volumen del MVP es pequeño. |
| Se espera filtro mensual. | Documentar que el resumen es global; el filtro llega post-MVP. |

## 11. Trazabilidad requisitos → plan

| Requisito | Sección del plan | Tareas |
|---|---|---|
| FR-001 | 2, 5 | T-002 |
| FR-002 | 5, 6 | T-002 |
| FR-003 | 5, 6 | T-002 |
| FR-004 | 5, 6 | T-002 |
| FR-005 | 5, 6 | T-001, T-002 |
| FR-006 | 5, 6 | T-001, T-002 |
| FR-007 | 5, 6 | T-002, T-003 |
| FR-008 | 6 | T-002, T-003 |
| FR-009 | 6, 7 | T-002 |
| FR-010 | 5, 7 | T-002, T-003 |
| FR-011 | 5 | T-003 |
| NFR-001 | 6 | T-001, T-002 |
| NFR-002 | 6, 7 | T-002 |
| NFR-003 | 6 | T-001, T-002 |
| NFR-004 | 8 | T-003, T-004 |
| NFR-005 | 7 | T-002 |
| NFR-006 | 5, 7 | T-002 |
| NFR-007 | 4 | T-002, T-004 |
| NFR-008 | 8, 9 | T-003, T-004 |

## 12. Aprobación y siguiente paso

Este plan fue aprobado junto con `tasks.md`.

La implementación comienza por `T-001` y avanza en el orden de dependencias de `tasks.md`.
