# Plan técnico 003 — API de gastos

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Fase: 1.
- Iteración: MVP.

## 1. Resumen de la solución

La Fase 1 incorpora la entidad `Expense` y expone un CRUD completo bajo `/api/gastos`.

Se reutilizan los patrones de la API de ingresos:

- SQLAlchemy 2 para el modelo y la persistencia.
- Pydantic v2 para validación y contrato.
- Alembic para la migración `0003`.
- FastAPI para los endpoints.
- PostgreSQL real para las pruebas de integración.

La diferencia principal es el campo obligatorio `tipo`, limitado a `NECESARIO`, `NO_NECESARIO` e `INVERSION`.

No se modifica el frontend en esta especificación. El contrato queda preparado para la interfaz de la especificación 005 y para el resumen de la especificación 004.

## 2. Arquitectura y flujo de datos

```text
Cliente / futuro frontend
        │
        │  /api/gastos
        ▼
FastAPI (router de gastos)
        │
        │  DTO Pydantic en español (tipo validado)
        ▼
Rutas + SQLAlchemy
        │
        │  Expense (atributos en inglés)
        ▼
PostgreSQL: tabla gastos
```

Flujo de creación:

1. FastAPI valida el payload con `ExpenseCreate`.
2. La ruta construye un `Expense` y convierte el enum a su valor string.
3. Se añade a la sesión, se confirma y se refresca.
4. Se mapea el modelo a `ExpenseRead`, convirtiendo el string de vuelta al enum.
5. Se responde `201` con el JSON en español.

Flujo de pruebas:

```text
pytest
  → reutiliza/crea personal_finance_test
  → ejecuta Alembic hasta 0003
  → trunca ingresos y gastos entre pruebas
  → sobrescribe get_db para usar la base de test
  → TestClient contra la API
```

## 3. Componentes y responsabilidades

### Backend

| Ruta | Responsabilidad |
|---|---|
| `backend/app/db/models/expense.py` | `ExpenseType`, modelo `Expense` y mapeo a `gastos`. |
| `backend/app/db/models/__init__.py` | Exportar y registrar `Expense`. |
| `backend/app/api/schemas/expense.py` | `ExpenseWrite`, `ExpenseCreate`, `ExpenseUpdate`, `ExpenseRead`. |
| `backend/app/api/routes/expenses.py` | CRUD y mapeo de modelo a DTO. |
| `backend/app/main.py` | Registrar el router bajo `/api`. |
| `backend/alembic/versions/0003_create_gastos.py` | Crear tabla, checks e índice. |

### Pruebas

| Ruta | Responsabilidad |
|---|---|
| `backend/tests/api/test_expense_schemas.py` | Validación y serialización sin base de datos. |
| `backend/tests/integration/test_expenses.py` | CRUD, errores y restricciones. |
| `backend/tests/integration/conftest.py` | Truncar ingresos y gastos entre pruebas. |
| `backend/tests/integration/test_database.py` | Verificar tablas y revisión `0003`. |

### Infraestructura y documentación

| Ruta | Cambio |
|---|---|
| `README.md` | Documentar `/api/gastos`, valores de `tipo` y pruebas. |
| `AGENTS.md` | Actualizar estado, comandos y verificación. |
| `specs/README.md` | Estado de 003. |

## 4. Modelo de datos

### Tabla `gastos`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `INTEGER` | PK, autoincremental |
| `fecha` | `DATE` | `NOT NULL` |
| `descripcion` | `VARCHAR(200)` | `NOT NULL` |
| `tipo` | `VARCHAR(20)` | `NOT NULL` |
| `valor` | `NUMERIC(12,2)` | `NOT NULL` |

Restricciones:

- `ck_gastos_valor_positivo`: `valor > 0`.
- `ck_gastos_descripcion_no_vacia`: `length(trim(descripcion)) > 0`.
- `ck_gastos_tipo_valido`: `tipo IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')`.
- Índice `ix_gastos_fecha` sobre `fecha`.

### Tipo de gasto

```python
from enum import StrEnum


class ExpenseType(StrEnum):
    NECESSARY = "NECESARIO"
    NON_NECESSARY = "NO_NECESARIO"
    INVESTMENT = "INVERSION"
```

Decisión: `tipo` se almacena como `VARCHAR(20)` con un `CHECK` de valores, no como un tipo ENUM nativo de PostgreSQL.

Motivo:

- La restricción de base de datos sigue existiendo.
- La migración y el `downgrade` son simples: se elimina la tabla y no hay un tipo compartido que limpiar.
- Se evita la ambigüedad de `SQLEnum` almacenando nombres de miembros en vez de valores.
- El enum de Python sigue validando la API y documentando OpenAPI.

El modelo usa `expense_type: Mapped[str]` y la ruta convierte:

- Entrada: `payload.tipo.value` al asignar el modelo.
- Salida: `ExpenseType(expense.expense_type)` al construir el DTO.

### Modelo

```python
class Expense(Base):
    __tablename__ = "gastos"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_gastos_valor_positivo"),
        CheckConstraint(
            "length(trim(descripcion)) > 0",
            name="ck_gastos_descripcion_no_vacia",
        ),
        CheckConstraint(
            "tipo IN ('NECESARIO', 'NO_NECESARIO', 'INVERSION')",
            name="ck_gastos_tipo_valido",
        ),
        Index("ix_gastos_fecha", "fecha"),
    )

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    date: Mapped[DateType] = mapped_column("fecha", Date, nullable=False)
    description: Mapped[str] = mapped_column("descripcion", String(200), nullable=False)
    expense_type: Mapped[str] = mapped_column("tipo", String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column("valor", Numeric(12, 2), nullable=False)
```

### Migración `0003`

- `revision = "0003"`.
- `down_revision = "0002"`.
- `upgrade`: `op.create_table` con columnas, checks e índice; no crea un tipo ENUM nativo.
- `downgrade`: elimina índice y tabla.
- Se generará con autogenerate y se revisará para confirmar los checks.
- Se validará `upgrade head` → `downgrade 0002` → `upgrade head` sobre la base de test.

## 5. Contrato de API

### `POST /api/gastos`

Request:

```json
{
  "fecha": "2026-10-21",
  "descripcion": "Mercado",
  "tipo": "NECESARIO",
  "valor": "120.50"
}
```

Response `201`:

```json
{
  "id": 1,
  "fecha": "2026-10-21",
  "descripcion": "Mercado",
  "tipo": "NECESARIO",
  "valor": "120.50"
}
```

### `GET /api/gastos`

Response `200`:

```json
[
  {
    "id": 2,
    "fecha": "2026-10-22",
    "descripcion": "Curso",
    "tipo": "INVERSION",
    "valor": "300.00"
  }
]
```

Orden: `fecha DESC, id DESC`.

### `GET /api/gastos/{expense_id}`

- `200` con el gasto.
- `404` con `{"detail": "Gasto no encontrado"}`.

### `PUT /api/gastos/{expense_id}`

Request: el objeto completo.

- `200` con el gasto actualizado.
- `404` si no existe.
- `422` si el payload es inválido.

### `DELETE /api/gastos/{expense_id}`

- `204` sin cuerpo.
- `404` si no existe.

### Errores

Los errores de validación usan el formato estándar de FastAPI. Los mensajes técnicos permanecen en inglés; el frontend los traducirá en la especificación 005.

## 6. Validación y DTO

`ExpenseWrite` será la base de creación y edición:

- `fecha: date`.
- `descripcion: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]`.
- `tipo: ExpenseType`.
- `valor: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]`.

`ExpenseCreate` y `ExpenseUpdate` heredan de `ExpenseWrite`. `ExpenseRead` añade `id`.

Los DTO usan campos en español porque son el contrato externo. Las rutas mapean manualmente:

```python
def to_expense_read(expense: Expense) -> ExpenseRead:
    return ExpenseRead(
        id=expense.id,
        fecha=expense.date,
        descripcion=expense.description,
        tipo=ExpenseType(expense.expense_type),
        valor=expense.amount,
    )
```

No se usa `from_attributes` porque los atributos internos están en inglés y los campos del DTO en español. El mapeo explícito evita alias y mantiene el contrato claro.

Pydantic serializa `Decimal` como string en JSON. La respuesta de `valor` será `"120.50"`. La entrada acepta string o número; el frontend enviará string.

## 7. Persistencia y transacciones

- Cada petición recibe una sesión mediante `get_db`.
- Crear: `db.add(expense)`, `db.commit()`, `db.refresh(expense)`.
- Editar: cargar con `db.get(Expense, expense_id)`, asignar los cuatro campos, `commit()` y `refresh()`.
- Eliminar: cargar, `db.delete(expense)`, `commit()`.
- Listar: `db.scalars(select(Expense).order_by(Expense.date.desc(), Expense.id.desc())).all()`.
- No se añade una capa de servicios ni un repositorio; las rutas son proporcionales al MVP.
- Si el registro no existe, se lanza `HTTPException(404, detail="Gasto no encontrado")`.
- No se implementa bloqueo optimista; la última escritura prevalece.

## 8. Estrategia de pruebas

### Unitarias sin PostgreSQL

- `ExpenseCreate` válido para los tres tipos.
- Tipo ausente, desconocido, en minúsculas o con espacios.
- Valor cero, negativo, ausente, con demasiados dígitos o demasiados decimales.
- Descripción vacía, solo espacios o mayor de 200 caracteres.
- Recorte de espacios.
- Fecha ausente o inválida.
- Serialización: `valor` como string con dos decimales, `fecha` ISO y `tipo` con el valor correcto.

### Integración con PostgreSQL

El fixture compartido de `tests/integration/conftest.py` se actualizará para:

- Truncar `ingresos` y `gastos` entre pruebas.
- Mantener la creación y migración de `personal_finance_test`.
- Mantener el guard contra la base de desarrollo.

La prueba de humo `tests/integration/test_database.py` se actualizará para:

- Verificar la revisión `0003`.
- Verificar que existen `ingresos` y `gastos`.

Casos de integración:

- Crear gastos de los tres tipos.
- Lista vacía y orden `fecha DESC, id DESC`.
- Consulta por id y `404`.
- Edición completa y `404`/`422`.
- Eliminación, `204`, `404` y verificación posterior.
- Restricciones de base de datos mediante inserciones directas:
  - `valor <= 0`.
  - Descripción vacía o solo espacios.
  - `tipo` fuera del conjunto permitido.
- Ida y vuelta de importes.
- Descripción recortada.
- Errores `422` por importe, descripción, fecha y tipo.
- No regresión de los tests de ingresos.

### Migración

En la base de test:

```bash
alembic downgrade 0002
alembic upgrade head
```

Después se vuelve a ejecutar la suite completa.

## 9. Infraestructura y documentación

- No se añaden dependencias nuevas.
- `TEST_DATABASE_URL` ya existe desde la especificación 002.
- Actualizar README con:
  - Endpoints de `/api/gastos`.
  - Valores válidos de `tipo`.
  - Ejemplos de request/response.
- Actualizar AGENTS con el estado de la especificación y la verificación.
- Actualizar `specs/README.md`.
- La suite completa se ejecuta con `docker compose exec api uv run pytest`.

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Guardar nombres de miembros del enum en vez de sus valores. | Usar `VARCHAR` y asignar explícitamente `payload.tipo.value`; convertir con `ExpenseType(...)` al responder. |
| El check de tipo y el enum de Python se desincronizan. | Definir los tres valores en un único enum y cubrir válidos/inválidos con pruebas unitarias e integración. |
| El fixture trunca una tabla que aún no existe. | Actualizar el fixture después de la migración `0003`; el fixture migra a `head` antes de truncar. |
| La prueba de humo sigue esperando `0002`. | Actualizarla a `0003` y a la existencia de ambas tablas. |
| Las pruebas de ingresos se rompen por el cambio de fixture. | Ejecutar la suite completa de 002 y 003 tras actualizar el truncado. |
| `SQLEnum` nativo complica el downgrade. | Usar `VARCHAR(20)` + `CHECK`. |
| El contrato de `valor` como string no se refleja en el frontend. | Documentarlo y usarlo en los tipos TypeScript de la spec 005. |
| Sin paginación el listado crece indefinidamente. | Aceptado para el MVP; se abordará post-MVP. |
| Los mensajes de validación están en inglés. | El frontend mostrará mensajes en español en spec 005. |

## 11. Trazabilidad requisitos → plan

| Requisito | Sección del plan | Tareas |
|---|---|---|
| FR-001 | 4 | T-001, T-002 |
| FR-002 | 4 | T-002 |
| FR-003 | 5, 7 | T-005 |
| FR-004 | 5, 7 | T-005 |
| FR-005 | 5, 7 | T-005 |
| FR-006 | 5, 7 | T-006 |
| FR-007 | 5, 7 | T-006 |
| FR-008 | 6, 8 | T-003, T-007 |
| FR-009 | 6, 8 | T-003, T-007 |
| FR-010 | 6, 8 | T-003, T-007 |
| FR-011 | 4, 6, 8 | T-001, T-003, T-007 |
| FR-012 | 5, 6 | T-003, T-005, T-006 |
| FR-013 | 5, 7 | T-005, T-006 |
| FR-014 | 5 | T-005, T-006 |
| NFR-001 | 4, 6 | T-001, T-003 |
| NFR-002 | 4, 6 | T-001, T-003, T-007 |
| NFR-003 | 6 | T-001, T-003, T-005, T-006 |
| NFR-004 | 8 | T-004, T-007, T-008 |
| NFR-005 | 7 | T-005, T-006 |
| NFR-006 | 7 | T-005 |
| NFR-007 | 4 | T-002, T-004, T-007 |
| NFR-008 | 9 | T-008 |
| NFR-009 | 8 | T-004, T-007 |

## 12. Aprobación y siguiente paso

Este plan fue aprobado junto con `tasks.md`.

La implementación comienza por `T-001` y avanza en el orden de dependencias de `tasks.md`.
