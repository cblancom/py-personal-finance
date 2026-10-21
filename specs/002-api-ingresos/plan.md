# Plan técnico 002 — API de ingresos

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Fase: 1.
- Iteración: MVP.

## 1. Resumen de la solución

La Fase 1 incorpora la entidad `Income` y expone un CRUD completo bajo `/api/ingresos`.

El backend usará:

- SQLAlchemy 2 para el modelo y la persistencia.
- Pydantic v2 para validación y contrato.
- Alembic para crear la tabla mediante una migración reversible.
- FastAPI para los endpoints.
- PostgreSQL real para las pruebas de integración.

No se modifica el frontend en esta especificación. El contrato queda preparado para que la interfaz de la especificación 005 consuma `valor` como string decimal.

## 2. Arquitectura y flujo de datos

```text
Cliente / futuro frontend
        │
        │  /api/ingresos
        ▼
FastAPI (router de ingresos)
        │
        │  DTO Pydantic en español
        ▼
Rutas + SQLAlchemy
        │
        │  Income (atributos en inglés)
        ▼
PostgreSQL: tabla ingresos
```

Flujo de creación:

1. FastAPI valida el payload con `IncomeCreate`.
2. La ruta construye un `Income` con los valores validados.
3. Se añade a la sesión, se confirma y se refresca.
4. Se mapea el modelo al DTO `IncomeRead`.
5. Se responde `201` con el JSON en español.

Flujo de pruebas de integración:

```text
pytest
  → crea/verifica personal_finance_test
  → ejecuta Alembic hasta head
  → trunca ingresos entre pruebas
  → sobrescribe get_db para usar la base de test
  → TestClient contra la API
```

## 3. Componentes y responsabilidades

### Backend

| Ruta | Responsabilidad |
|---|---|
| `backend/app/db/models/income.py` | Modelo `Income` y mapeo a `ingresos`. |
| `backend/app/db/models/__init__.py` | Registrar el modelo para `Base.metadata`. |
| `backend/app/api/schemas/income.py` | `IncomeWrite`, `IncomeCreate`, `IncomeUpdate`, `IncomeRead`. |
| `backend/app/api/routes/incomes.py` | Endpoints CRUD y mapeo de modelo a DTO. |
| `backend/app/main.py` | Registrar el router con prefijo `/api`. |
| `backend/alembic/env.py` | Importar modelos y aceptar URL configurada para tests. |
| `backend/alembic/versions/0002_ingresos.py` | Crear tabla, checks e índice. |

### Pruebas

| Ruta | Responsabilidad |
|---|---|
| `backend/tests/api/test_income_schemas.py` | Validación y serialización sin base de datos. |
| `backend/tests/integration/conftest.py` | Base de test, migraciones, truncado y cliente. |
| `backend/tests/integration/test_incomes.py` | CRUD, errores y restricciones contra PostgreSQL. |

### Infraestructura y documentación

| Ruta | Cambio |
|---|---|
| `backend/pyproject.toml` | Registrar el marcador `integration`. |
| `compose.yaml` | Añadir `TEST_DATABASE_URL` al servicio `api`. |
| `.env.example` | Documentar `TEST_DATABASE_URL` para ejecución local. |
| `README.md` | Documentar endpoints, contrato y pruebas de integración. |
| `AGENTS.md` | Actualizar la verificación completa y el estado de la fase. |
| `specs/README.md` | Actualizar el estado de 002. |

## 4. Modelo de datos

### Tabla `ingresos`

| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `INTEGER` | PK, autoincremental |
| `fecha` | `DATE` | `NOT NULL` |
| `descripcion` | `VARCHAR(200)` | `NOT NULL` |
| `valor` | `NUMERIC(12,2)` | `NOT NULL` |

Restricciones:

- `ck_ingresos_valor_positivo`: `valor > 0`.
- `ck_ingresos_descripcion_no_vacia`: `length(trim(descripcion)) > 0`.
- Índice `ix_ingresos_fecha` sobre `fecha`.

### Modelo

```python
class Income(Base):
    __tablename__ = "ingresos"

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column("fecha", Date, nullable=False)
    description: Mapped[str] = mapped_column("descripcion", String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column("valor", Numeric(12, 2), nullable=False)
```

`Income` se importa en `app/db/models/__init__.py`. `alembic/env.py` importa ese paquete para que el modelo se registre en `Base.metadata`.

### Migración `0002`

- `revision = "0002"`.
- `down_revision = "0001"`.
- `upgrade`: `op.create_table` con columnas, PK y checks; `op.create_index`.
- `downgrade`: `op.drop_index` y `op.drop_table`.
- Se generará con autogenerate y se revisará para confirmar checks, índice y tipos.
- Se validará `upgrade head` → `downgrade 0001` → `upgrade head` sobre la base de test.

## 5. Contrato de API

### `POST /api/ingresos`

Request:

```json
{
  "fecha": "2026-10-21",
  "descripcion": "Salario",
  "valor": "1500.50"
}
```

Response `201`:

```json
{
  "id": 1,
  "fecha": "2026-10-21",
  "descripcion": "Salario",
  "valor": "1500.50"
}
```

### `GET /api/ingresos`

Response `200`:

```json
[
  {
    "id": 2,
    "fecha": "2026-10-22",
    "descripcion": "Consultoría",
    "valor": "800.00"
  }
]
```

Orden: `fecha DESC, id DESC`.

### `GET /api/ingresos/{income_id}`

- `200` con el ingreso.
- `404` con `{"detail": "Ingreso no encontrado"}`.

### `PUT /api/ingresos/{income_id}`

Request: el mismo objeto completo que en creación.

- `200` con el ingreso actualizado.
- `404` si no existe.
- `422` si el payload es inválido.

### `DELETE /api/ingresos/{income_id}`

- `204` sin cuerpo.
- `404` si no existe.

### Errores

Los errores de validación usan el formato estándar de FastAPI:

```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "valor"],
      "msg": "Input should be greater than 0",
      "input": "0"
    }
  ]
}
```

Los mensajes técnicos permanecen en inglés; el frontend los traducirá en la especificación 005.

## 6. Validación y DTO

`IncomeWrite` será la base de creación y edición:

- `fecha: date`.
- `descripcion: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]`.
- `valor: Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]`.

`IncomeCreate` e `IncomeUpdate` heredan de `IncomeWrite`. `IncomeRead` añade `id`.

Los DTO usan campos en español porque son el contrato externo. Las rutas mapean manualmente:

```python
def to_income_read(income: Income) -> IncomeRead:
    return IncomeRead(
        id=income.id,
        fecha=income.date,
        descripcion=income.description,
        valor=income.amount,
    )
```

No se usa `from_attributes` porque los atributos internos están en inglés y los campos del DTO en español. El mapeo explícito evita alias y mantiene el contrato claro.

Pydantic serializa `Decimal` como string en JSON. La respuesta de `valor` será `"1500.50"`. La entrada acepta string o número; el frontend enviará string.

## 7. Persistencia y transacciones

- Cada petición recibe una sesión mediante `get_db`.
- Crear: `db.add(income)`, `db.commit()`, `db.refresh(income)`.
- Editar: cargar con `db.get(Income, income_id)`, asignar los tres campos, `commit()` y `refresh()`.
- Eliminar: cargar, `db.delete(income)`, `commit()`.
- Listar: `db.scalars(select(Income).order_by(Income.date.desc(), Income.id.desc())).all()`.
- No se añade una capa de servicios ni un repositorio; las rutas son proporcionales al MVP.
- Si el registro no existe, se lanza `HTTPException(404, detail="Ingreso no encontrado")`.
- No se implementa bloqueo optimista; la última escritura prevalece.

## 8. Estrategia de pruebas

### Unitarias sin PostgreSQL

- `IncomeCreate` válido.
- Valor cero, negativo, ausente, con demasiados dígitos o demasiados decimales.
- Descripción vacía, solo espacios o mayor de 200 caracteres.
- Recorte de espacios.
- Fecha ausente o inválida.
- Serialización: `valor` sale como string con dos decimales y `fecha` como ISO.

### Integración con PostgreSQL

`TEST_DATABASE_URL` apunta a una base dedicada, por defecto:

```text
postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance_test
```

El fixture de sesión:

1. Lee `TEST_DATABASE_URL`; si no existe, omite las pruebas de integración con un mensaje claro.
2. Comprueba que la base de test no sea la misma que `DATABASE_URL`; si coincide, aborta.
3. Conecta a la base de mantenimiento `postgres` con `AUTOCOMMIT`.
4. Crea `personal_finance_test` si no existe.
5. Ejecuta `alembic.command.upgrade(config, "head")` con la URL de test.
6. Expone un `sessionmaker` contra la base de test.

El fixture de función:

1. Trunca `ingresos` con `RESTART IDENTITY CASCADE`.
2. Sobrescribe `get_db` con la sesión de test.
3. Limpia las sobrescrituras al terminar.

Casos:

- Crear y consultar.
- Lista vacía y orden `fecha DESC, id DESC`.
- Consulta por id y `404`.
- Edición completa y `404`/`422`.
- Eliminación, `204`, `404` y verificación posterior.
- Restricciones de base de datos mediante inserciones directas.
- Ida y vuelta de importes con dos decimales.

### Configuración de Alembic para tests

`alembic/env.py` usará la URL configurada en `alembic.ini` si no está vacía; en caso contrario, usará `get_settings().database_url`. Esto permite que el fixture apunte a la base de test con:

```python
config.set_main_option("sqlalchemy.url", test_url.replace("%", "%%"))
```

Para comandos CLI de validación sobre la base de test se usará `DATABASE_URL=<test_url>`, no `TEST_DATABASE_URL`, para evitar que un comando accidental de Alembic apunte a una base distinta de la esperada.

## 9. Infraestructura y documentación

- Añadir `TEST_DATABASE_URL` a `.env.example`.
- Añadir al servicio `api` de Compose:
  `TEST_DATABASE_URL=postgresql+psycopg://...@db:5432/personal_finance_test`.
- Registrar el marcador `integration` en `pyproject.toml`.
- Documentar:
  - `docker compose exec api uv run pytest` para la suite completa.
  - `uv run --env-file ../.env pytest` para local con base de test.
  - `uv run pytest` ejecuta unitarias y omite integración si falta `TEST_DATABASE_URL`.
- Actualizar `README.md`, `AGENTS.md` y `specs/README.md`.

No se añaden dependencias nuevas. La creación de la base de test usa SQLAlchemy y psycopg ya presentes.

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| El contrato de `valor` como string no se refleja en el frontend. | Documentarlo y usarlo en los tipos TypeScript de la spec 005. |
| El fixture apunta por error a la base de desarrollo. | Abortar si `TEST_DATABASE_URL` coincide con `DATABASE_URL`. |
| El usuario no tiene permisos para crear la base de test. | Usar el usuario `postgres` local; documentar el requisito. |
| Alembic usa la base equivocada en tests. | Soportar la URL configurada y escapar `%`. |
| El modelo no se registra en `Base.metadata`. | Importarlo en `app/db/models/__init__.py` y en `alembic/env.py`. |
| Las pruebas de integración se omiten sin avisar. | Mensaje de skip explícito y comando de validación con `TEST_DATABASE_URL`. |
| `PUT` parcial devuelve `422`. | Documentar el reemplazo completo. |
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
| FR-011 | 5, 6 | T-003, T-005, T-006 |
| FR-012 | 5, 7 | T-005, T-006 |
| FR-013 | 5 | T-005, T-006 |
| NFR-001 | 4, 6 | T-001, T-003 |
| NFR-002 | 4, 6 | T-001, T-003, T-007 |
| NFR-003 | 6 | T-001, T-003, T-005, T-006 |
| NFR-004 | 8 | T-004, T-007, T-008 |
| NFR-005 | 7 | T-005, T-006 |
| NFR-006 | 7 | T-005 |
| NFR-007 | 4 | T-002, T-004, T-007 |
| NFR-008 | 9 | T-008 |

## 12. Aprobación y siguiente paso

Este plan fue aprobado junto con `tasks.md`.

La implementación comienza por `T-001` y avanza en el orden de dependencias de `tasks.md`.
