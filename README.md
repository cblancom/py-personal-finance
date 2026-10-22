# Py Personal Finance

Aplicación local para registrar ingresos y gastos personales, clasificar los gastos como necesarios, no necesarios o inversiones y consultar totales.

El MVP es de un solo usuario, funciona en local y no incluye autenticación.

## Estado

La Fase 0 (`001-fundaciones`) está implementada y validada. Las APIs de ingresos (`002-api-ingresos`), gastos (`003-api-gastos`) y resumen (`004-api-resumen`), y la interfaz MVP (`005-interfaz-mvp`), están implementadas y validadas. El backend, el frontend y el entorno Docker de desarrollo están operativos.

La interfaz permite registrar, listar, editar y eliminar ingresos y gastos, consultar el resumen y muestra los importes en pesos colombianos (COP). La especificación 006 (entrega Docker de producción) está pendiente.

El estado detallado está en [`specs/README.md`](specs/README.md) y en los `tasks.md` de cada especificación.

## Stack

- Backend: Python 3.13, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2.
- Base de datos: PostgreSQL 16.
- Frontend: React 19, TypeScript, Vite.
- Pruebas: pytest, Vitest y Testing Library.
- Infraestructura: Docker y Docker Compose.

## Requisitos

Para el flujo principal solo se necesita Docker con Docker Compose.

Para desarrollo local sin contenedores para la API o la interfaz:

- Python 3.13 y `uv`.
- Node.js 20 y `npm`.

## Inicio rápido con Docker

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Los tres servicios deben aparecer como `healthy`.

Servicios disponibles:

| Servicio | URL |
|---|---|
| Interfaz web | http://localhost:3001 |
| API | http://localhost:8000 |
| Documentación OpenAPI | http://localhost:8000/docs |
| Salud de la API | http://localhost:8000/api/health |
| PostgreSQL | `localhost:5433` (solo localhost) |

La base de datos solo se publica en `127.0.0.1` para desarrollo.

Para detener los servicios sin borrar datos:

```bash
docker compose down
```

`docker compose down -v` elimina el volumen de PostgreSQL y requiere autorización explícita.

## Uso actual

La interfaz de una sola página permite:

- Consultar el balance, el total de ingresos, el total de gastos y el desglose por tipo.
- Crear, editar y eliminar ingresos desde la pestaña `Ingresos`.
- Crear, editar y eliminar gastos con tipo desde la pestaña `Gastos`.
- Ver estados de carga, error con reintento, listas vacías y confirmación antes de eliminar.
- Leer importes en COP con formato `es-CO` y fechas en formato local.

Los formularios validan los datos antes de enviarlos. Los errores se muestran en español sin detalles técnicos.

El endpoint de salud sigue disponible en el backend y responde:

```json
{
  "status": "ok",
  "database": "ok"
}
```

Si PostgreSQL no está disponible, responde `503` con `status: degraded` y `database: unavailable`.

## API de ingresos

Base: `/api/ingresos`. La documentación interactiva está en `/docs`.

| Método | Ruta | Resultado |
|---|---|---|
| `POST` | `/api/ingresos` | `201` con el ingreso creado |
| `GET` | `/api/ingresos` | `200` con la lista, ordenada por `fecha DESC, id DESC` |
| `GET` | `/api/ingresos/{income_id}` | `200` o `404` |
| `PUT` | `/api/ingresos/{income_id}` | `200` con reemplazo completo, `404` o `422` |
| `DELETE` | `/api/ingresos/{income_id}` | `204`, `404` |

Ejemplo de creación:

```bash
curl -X POST http://localhost:8000/api/ingresos \
  -H 'Content-Type: application/json' \
  -d '{"fecha":"2026-10-21","descripcion":"Salario","valor":"1500.50"}'
```

Respuesta:

```json
{
  "fecha": "2026-10-21",
  "descripcion": "Salario",
  "valor": "1500.50",
  "id": 1
}
```

`valor` se transporta como string decimal para preservar la precisión. La entrada acepta string o número; el frontend enviará string. `descripcion` se recorta y debe tener entre 1 y 200 caracteres. `fecha` usa ISO `YYYY-MM-DD`.

## API de gastos

Base: `/api/gastos`. La documentación interactiva está en `/docs`.

| Método | Ruta | Resultado |
|---|---|---|
| `POST` | `/api/gastos` | `201` con el gasto creado |
| `GET` | `/api/gastos` | `200` con la lista, ordenada por `fecha DESC, id DESC` |
| `GET` | `/api/gastos/{expense_id}` | `200` o `404` |
| `PUT` | `/api/gastos/{expense_id}` | `200` con reemplazo completo, `404` o `422` |
| `DELETE` | `/api/gastos/{expense_id}` | `204`, `404` |

Valores válidos de `tipo`:

- `NECESARIO`
- `NO_NECESARIO`
- `INVERSION`

Ejemplo de creación:

```bash
curl -X POST http://localhost:8000/api/gastos \
  -H 'Content-Type: application/json' \
  -d '{"fecha":"2026-10-21","descripcion":"Mercado","tipo":"NECESARIO","valor":"120.50"}'
```

Respuesta:

```json
{
  "fecha": "2026-10-21",
  "descripcion": "Mercado",
  "tipo": "NECESARIO",
  "valor": "120.50",
  "id": 1
}
```

`tipo` es obligatorio y distingue mayúsculas. `valor` usa la misma representación decimal que en ingresos. La edición reemplaza los cuatro campos.

## API de resumen

`GET /api/resumen` devuelve los totales globales, el balance y el desglose de gastos por tipo. No acepta parámetros ni filtros.

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

- `balance = total_ingresos - total_gastos`; puede ser negativo.
- `gastos_por_tipo` incluye siempre los tres tipos, con `"0.00"` cuando no hay movimientos.
- `total_gastos` coincide con la suma del desglose.
- Todos los importes son strings con dos decimales.

## Desarrollo local

El flujo principal es Docker Compose. Para reemplazar solo la API o el frontend por procesos locales, detén primero los servicios que vayas a sustituir:

```bash
docker compose stop api web
```

### Backend

Con PostgreSQL en Docker y el archivo `.env` en la raíz:

```bash
docker compose up db -d
cp .env.example .env
cd backend
uv sync
uv run --env-file ../.env uvicorn app.main:app --reload --port 8000
```

El comando requiere `DATABASE_URL`. Puedes exportarla directamente en lugar de usar `--env-file`:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance \
  uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Vite escucha en `http://localhost:5173` y redirige `/api` a `http://localhost:8000` por defecto. Para apuntar a otro backend:

```bash
VITE_API_PROXY_TARGET=http://localhost:8001 npm run dev
```

Dentro de Docker Compose el proxy apunta a `http://api:8000`.

## Pruebas y calidad

### Backend

```bash
cd backend
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Las pruebas unitarias no necesitan PostgreSQL. Las de integración cubren ingresos, gastos y resumen; usan `TEST_DATABASE_URL`, crean o reutilizan `personal_finance_test`, ejecutan migraciones, limpian `ingresos` y `gastos` entre casos y se omiten si la variable no está configurada.

Suite completa con Docker Compose:

```bash
docker compose exec api uv run pytest
```

Suite completa en local, usando el `.env` de la raíz:

```bash
cd backend
uv run --env-file ../.env pytest
```

Sin `TEST_DATABASE_URL`, `uv run pytest` ejecuta solo las unitarias y omite las de integración.

### Frontend

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test
npm run build
```

Las pruebas del frontend simulan `fetch`; no requieren la API en ejecución.

## Migraciones

Alembic es la única vía para modificar el esquema. La revisión base `0001` no crea tablas de dominio; solo registra la versión en `alembic_version`.

Con Docker Compose:

```bash
docker compose exec api uv run alembic upgrade head
docker compose exec api uv run alembic current
docker compose exec api uv run alembic downgrade -1
```

Para crear una migración después de modificar modelos:

```bash
docker compose exec api uv run alembic revision --autogenerate -m "describe change"
docker compose exec api uv run alembic upgrade head
```

Revisa siempre el archivo generado antes de aplicarlo.

En local:

```bash
cd backend
uv run --env-file ../.env alembic upgrade head
```

No se usa `Base.metadata.create_all()`.

## Variables de entorno

`.env` está ignorado por Git. `.env.example` contiene únicamente valores de desarrollo.

| Variable | Valor por defecto | Uso |
|---|---|---|
| `POSTGRES_DB` | `personal_finance` | Nombre de la base de datos |
| `POSTGRES_USER` | `postgres` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `postgres` | Contraseña local de desarrollo |
| `DB_PORT` | `5433` | Puerto de PostgreSQL en localhost |
| `API_PORT` | `8000` | Puerto de la API en localhost |
| `WEB_PORT` | `3001` | Puerto de la interfaz en localhost |
| `DATABASE_URL` | URL a `localhost:5433` | Backend ejecutado fuera de Docker |
| `TEST_DATABASE_URL` | URL a `localhost:5433/personal_finance_test` | Base aislada para pruebas de integración; se crea automáticamente |
| `VITE_API_PROXY_TARGET` | `http://localhost:8000` | Proxy de Vite; Compose usa `http://api:8000` |

No uses los valores de ejemplo en producción.

## Estructura

```text
.
├── backend/
│   ├── app/                # FastAPI, configuración, sesión y rutas
│   ├── alembic/            # Migraciones
│   ├── tests/              # Pruebas unitarias e integración
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/                # Componentes, cliente API y tipos
│   ├── package.json
│   └── package-lock.json
├── docker/
│   └── Dockerfile.api
├── specs/                  # Especificaciones SDD
├── compose.yaml
├── .env.example
├── .dockerignore
├── constitution.md
└── AGENTS.md
```

`legacy/` contiene una implementación anterior y está fuera de alcance.

## Solución de problemas

### La interfaz muestra "No se pudieron cargar los datos"

```bash
docker compose ps
curl -i http://localhost:8000/api/health
docker compose logs api
```

Si PostgreSQL está detenido, la API responde `503`; es el comportamiento esperado.

### Un puerto está ocupado

Cambia `API_PORT`, `WEB_PORT` o `DB_PORT` en `.env` y vuelve a levantar:

```bash
docker compose up -d
```

### El backend local indica que falta `DATABASE_URL`

Copia `.env.example` a `.env` o pasa el archivo explícitamente:

```bash
uv run --env-file ../.env uvicorn app.main:app --reload --port 8000
```

### `npm ci` falla

El `package-lock.json` no coincide con `package.json`. Actualiza el lock y revisa el diff:

```bash
cd frontend
npm install
```

### Las pruebas de integración se omiten

Configura `TEST_DATABASE_URL` o ejecuta la suite dentro de Docker:

```bash
docker compose exec api uv run pytest
```

La base de test no debe ser la misma que `DATABASE_URL`; el fixture aborta si coinciden.

### Se perdió la base de datos

Evita `docker compose down -v` salvo que quieras borrar el volumen. `docker compose down` conserva los datos.

## Documentación SDD

- [`constitution.md`](constitution.md): principios del proyecto.
- [`AGENTS.md`](AGENTS.md): instrucciones operativas y comandos.
- [`specs/README.md`](specs/README.md): índice y plan por fases.
- [`specs/001-fundaciones/`](specs/001-fundaciones/): especificación, plan y tareas de la Fase 0.
- [`specs/002-api-ingresos/`](specs/002-api-ingresos/): especificación, plan y tareas de la API de ingresos.
- [`specs/003-api-gastos/`](specs/003-api-gastos/): especificación, plan y tareas de la API de gastos.
- [`specs/004-api-resumen/`](specs/004-api-resumen/): especificación, plan y tareas de la API de resumen.
- [`specs/005-interfaz-mvp/`](specs/005-interfaz-mvp/): especificación, plan y tareas de la interfaz MVP.

El flujo es: especificación → clarificación → plan → tareas → implementación → validación.
