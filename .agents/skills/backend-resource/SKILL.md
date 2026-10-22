---
name: backend-resource
description: Implementa o modifica recursos del backend de Py Personal Finance con modelo SQLAlchemy, migración Alembic, schemas Pydantic, rutas FastAPI, pruebas y OpenAPI. Úsala para añadir endpoints, tablas, CRUD o cambiar el contrato de la API.
---

# Skill: Backend resource

## Propósito

Guía la implementación de un recurso del backend respetando las convenciones de Py Personal Finance y el patrón ya usado por ingresos, gastos y resumen.

Esta skill cubre la implementación. El flujo de especificación, plan y tareas sigue gobernado por `spec-driven-development`.

## Cuándo usarla

Actívala cuando la tarea implique:

- Añadir una tabla o un modelo SQLAlchemy.
- Crear o modificar endpoints CRUD.
- Añadir o cambiar schemas Pydantic.
- Crear una migración Alembic.
- Cambiar el contrato externo de la API.
- Añadir pruebas de API, integración u OpenAPI para un recurso.

## Reglas no negociables

- Contrato externo en español: rutas, campos JSON, tablas y columnas.
- Código interno en inglés: clases, funciones, variables y nombres de pruebas.
- Dinero con `Decimal` y `NUMERIC(12, 2)`. Nunca `float`.
- Fechas ISO 8601.
- Alembic es la única vía para modificar el esquema. No usar `Base.metadata.create_all()`.
- Toda migración debe tener `upgrade` y `downgrade` funcionales.
- No añadir dependencias sin justificarlo en el plan.
- No registrar secretos, URLs de conexión ni datos financieros identificables.
- No tocar `legacy/`.
- No cambiar el contrato fuera de la especificación aprobada.

## Lectura previa obligatoria

Antes de escribir código:

1. Lee `constitution.md`, `AGENTS.md` y la especificación, plan y tarea correspondientes.
2. Inspecciona el recurso existente más parecido:
   - `backend/app/db/models/income.py`
   - `backend/app/db/models/expense.py`
   - `backend/app/api/schemas/income.py`
   - `backend/app/api/schemas/expense.py`
   - `backend/app/api/routes/incomes.py`
   - `backend/app/api/routes/expenses.py`
3. Revisa las migraciones `0002_create_ingresos.py` y `0003_create_gastos.py`.
4. Revisa las pruebas de `backend/tests/api/` y `backend/tests/integration/`.
5. Confirma los nombres exactos del contrato. No los inventes.

## Flujo de implementación

### 1. Fijar el contrato

Antes de codificar, deja claro:

- Ruta base, por ejemplo `/api/recursos`.
- Métodos y códigos: `201`, `200`, `204`, `404`, `422`.
- Campos JSON exactos en español.
- Reglas de validación.
- Orden de listado. El patrón actual es `fecha DESC, id DESC`.
- Mensajes de error visibles, en español.
- Si el recurso necesita un enum, sus valores externos y su representación interna.

Si falta una decisión de negocio o el contrato es ambiguo, detente y pregunta. No la resuelvas solo en el código.

### 2. Crear el modelo

Ubicación: `backend/app/db/models/<resource>.py`.

Sigue el patrón existente:

- Clase SQLAlchemy 2 con `Mapped` y `mapped_column`.
- `__tablename__` en español.
- Atributos internos en inglés con nombre de columna explícito en español.
- Tipos: `Date`, `String(200)`, `Numeric(12, 2)`, `Integer`.
- Restricciones en `__table_args__`:
  - `valor > 0`.
  - Descripción no vacía después de `trim`.
  - Enum válido, si aplica.
  - Índice sobre `fecha`, si aplica.
- Exporta el modelo desde `backend/app/db/models/__init__.py`.

No dupliques lógica de negocio en el modelo si ya está expresada con restricciones de base de datos.

### 3. Crear la migración

Con el Compose de desarrollo levantado:

```bash
docker compose exec api uv run alembic revision --autogenerate -m "create <recurso>"
```

Después:

1. Revisa el archivo generado. No lo aceptes a ciegas.
2. Comprueba que el nombre de la revisión continúa la cadena.
3. Verifica que `upgrade` crea tabla, constraints e índices.
4. Verifica que `downgrade` elimina índice y tabla en orden correcto.
5. Comprueba que no haya cambios ajenos al recurso.
6. Aplica la migración en la base de test mediante la suite de integración.

Comandos útiles:

```bash
docker compose exec api uv run alembic current
docker compose exec api uv run alembic history
docker compose exec api uv run alembic upgrade head
```

No uses `alembic downgrade` sobre la base de desarrollo con datos sin autorización.

### 4. Crear los schemas

Ubicación: `backend/app/api/schemas/<resource>.py`.

Sigue el patrón `Write` / `Create` / `Update` / `Read`:

- Los campos de frontera conservan los nombres en español.
- Usa `Annotated` para validaciones reutilizables.
- Descripción: `strip_whitespace=True`, mínimo 1 y máximo 200.
- Importe: `Decimal`, mayor que 0, máximo 12 dígitos y 2 decimales.
- Enum externo si aplica.
- `Read` añade `id`.

Evita crear una abstracción nueva si el patrón local ya es suficiente.

### 5. Crear la ruta

Ubicación: `backend/app/api/routes/<resource>.py`.

Sigue el patrón existente:

- `APIRouter(prefix="/<ruta>", tags=["<ruta>"])`.
- `get_db` mediante `Annotated[Session, Depends(get_db)]`.
- Helper `to_<resource>_read` para mapear modelo → schema.
- Helper `get_<resource>_or_404` con detalle en español.
- `POST` con `201`.
- `GET` de lista con orden `fecha DESC, id DESC`.
- `GET` por id.
- `PUT` con reemplazo completo.
- `DELETE` con `204` y `Response`.
- No dupliques el prefijo `/api` dentro del router.

Registra el router en `backend/app/main.py` con `prefix="/api"`.

### 6. Añadir pruebas

Sigue la separación existente.

#### Pruebas de API

En `backend/tests/api/`:

- Validación de schemas.
- Presencia de rutas y métodos en OpenAPI.
- Casos límite de Pydantic.

#### Pruebas de integración

En `backend/tests/integration/`:

- Marca el módulo con `pytest.mark.integration`.
- Usa los fixtures `client`, `test_engine` y `test_session_factory`.
- Cubre creación, listado, orden, obtención, `404`, actualización, eliminación y validación.
- Comprueba las restricciones de base de datos cuando aporten valor.
- Si añades una tabla nueva, actualiza `backend/tests/integration/conftest.py` para incluirla en el `TRUNCATE` de `reset_movements`.

#### Base de datos de pruebas

La suite completa requiere PostgreSQL y `TEST_DATABASE_URL`. El fixture:

- Crea la base si no existe.
- Aplica Alembic.
- Se niega a usar la misma base que `DATABASE_URL`.
- Limpia las tablas entre pruebas.

Usa el Compose de desarrollo para ejecutar la suite completa:

```bash
docker compose exec api uv run pytest
```

`uv run pytest` sin `TEST_DATABASE_URL` solo ejecuta unitarias y omite integración.

### 7. Actualizar documentación y trazabilidad

- Si cambia el contrato, actualiza la sección de API correspondiente del README.
- No documentes endpoints que todavía no existen.
- Actualiza la tarea y la matriz de cobertura cuando corresponda.
- Registra la evidencia real de las pruebas ejecutadas.

## Checklist de salida

- [ ] Modelo con tabla y columnas en español.
- [ ] Restricciones de integridad en modelo y migración.
- [ ] Migración con `upgrade` y `downgrade`.
- [ ] Schemas con validación y nombres de contrato.
- [ ] Ruta registrada en `main.py`.
- [ ] Códigos `201`, `200`, `204`, `404` y `422` correctos.
- [ ] Listados ordenados de forma consistente.
- [ ] Pruebas de schemas, OpenAPI e integración.
- [ ] Tabla nueva incluida en el fixture de limpieza.
- [ ] Sin `float`, sin `create_all`, sin secretos.
- [ ] Ruff, format, suite unitaria y suite completa pasan.
- [ ] Diff limitado al recurso y su documentación.

## Errores frecuentes

- Olvidar exportar el modelo en `models/__init__.py`.
- Generar una migración sin `downgrade` o con índices huérfanos.
- Usar `float` o `Numeric` sin escala 2.
- Duplicar `/api` en el router y en `main.py`.
- Devolver `200` en un `POST` que debe ser `201`.
- Olvidar el `Response(status_code=204)` en `DELETE`.
- No actualizar el `TRUNCATE` de integración al añadir una tabla.
- Confiar solo en la suite unitaria y no ejecutar integración.
- Cambiar la base de desarrollo para “probar rápido”.
- Añadir una dependencia o una capa nueva sin justificación.

## Verificación

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Con el Compose de desarrollo levantado:

```bash
docker compose exec api uv run pytest
docker compose exec api uv run alembic current
```

Si la suite completa no puede ejecutarse, indícalo explícitamente y no la declares superada.
