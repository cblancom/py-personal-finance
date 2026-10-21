# Py Personal Finance

Aplicación local para registrar ingresos y gastos personales, clasificar los gastos como necesarios, no necesarios o inversiones y consultar totales.

El MVP es de un solo usuario, funciona en local y no incluye autenticación.

## Estado

La Fase 0 (`001-fundaciones`) está implementada y validada (T-001 a T-012). El backend, el frontend y el entorno Docker de desarrollo están operativos.

La aplicación todavía no permite registrar movimientos financieros. Por ahora la pantalla inicial muestra el estado de la API y el endpoint `/api/health` verifica la conexión con PostgreSQL. El registro de ingresos y gastos comienza en las especificaciones 002 y 003.

El estado detallado está en [`specs/001-fundaciones/tasks.md`](specs/001-fundaciones/tasks.md).

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

La pantalla inicial muestra:

- El nombre del proyecto.
- Un mensaje de que la interfaz está en construcción.
- El estado de la API: consultando, disponible o no disponible.

El endpoint de salud responde:

```json
{
  "status": "ok",
  "database": "ok"
}
```

Si PostgreSQL no está disponible, responde `503` con `status: degraded` y `database: unavailable`.

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

Las pruebas del backend no necesitan PostgreSQL: la dependencia de base de datos se sustituye en las pruebas unitarias.

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
| `VITE_API_PROXY_TARGET` | `http://localhost:8000` | Proxy de Vite; Compose usa `http://api:8000` |

No uses los valores de ejemplo en producción.

## Estructura

```text
.
├── backend/
│   ├── app/                # FastAPI, configuración, sesión y rutas
│   ├── alembic/            # Migraciones
│   ├── tests/              # Pruebas unitarias
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

### La interfaz muestra "API no disponible"

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

### Se perdió la base de datos

Evita `docker compose down -v` salvo que quieras borrar el volumen. `docker compose down` conserva los datos.

## Documentación SDD

- [`constitution.md`](constitution.md): principios del proyecto.
- [`AGENTS.md`](AGENTS.md): instrucciones operativas y comandos.
- [`specs/README.md`](specs/README.md): índice y plan por fases.
- [`specs/001-fundaciones/`](specs/001-fundaciones/): especificación, plan y tareas de la Fase 0.

El flujo es: especificación → clarificación → plan → tareas → implementación → validación.
