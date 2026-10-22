# Py Personal Finance

Aplicación local para registrar ingresos y gastos personales, clasificar los gastos como necesarios, no necesarios o inversiones y consultar totales.

El MVP es de un solo usuario, funciona en local y no incluye autenticación.

## Estado

La Fase 0 (`001-fundaciones`) está implementada y validada. Las APIs de ingresos (`002-api-ingresos`), gastos (`003-api-gastos`) y resumen (`004-api-resumen`), y la interfaz MVP (`005-interfaz-mvp`), están implementadas y validadas. El backend, el frontend y el entorno Docker de desarrollo están operativos.

La interfaz permite registrar, listar, editar y eliminar ingresos y gastos, consultar el resumen y muestra los importes en pesos colombianos (COP). La entrega Docker de producción (`006-entrega-docker`) está implementada y validada.

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

## Desarrollo con Docker

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Los tres servicios deben aparecer como `healthy`.

Este flujo usa `compose.yaml` y publica la API, OpenAPI y PostgreSQL en localhost. No lo ejecutes mientras la entrega de producción está levantada: ambos usan el puerto `3001`.

Servicios disponibles en desarrollo:

| Servicio | URL |
|---|---|
| Interfaz web | http://localhost:3001 |
| API | http://localhost:8000 |
| Documentación OpenAPI | http://localhost:8000/docs |
| Salud de la API | http://localhost:8000/api/health |
| PostgreSQL | `localhost:5433` (solo localhost) |

OpenAPI, el puerto `8000` de la API y el puerto `5433` de PostgreSQL existen solo en desarrollo. En producción, la API se consulta a través de Nginx en `http://127.0.0.1:3001/api/...` y OpenAPI no se publica.

Para detener los servicios sin borrar datos:

```bash
docker compose down
```

`docker compose down -v` elimina el volumen de PostgreSQL y requiere autorización explícita.

## Entrega de producción local

La entrega de producción usa `compose.prod.yaml`: compila el frontend, lo sirve con Nginx y publica únicamente la web en `127.0.0.1:3001`. La API y PostgreSQL quedan dentro de la red de Docker.

Servicios disponibles en producción:

| Servicio | URL |
|---|---|
| Interfaz web | http://127.0.0.1:3001 |
| API a través de Nginx | http://127.0.0.1:3001/api/... |
| Salud de Nginx | http://127.0.0.1:3001/healthz |
| Salud de la API | http://127.0.0.1:3001/api/health |
| OpenAPI | No disponible en producción |
| PostgreSQL | No publicado en el host |

OpenAPI se publica solo en desarrollo. En producción, `/docs` y `/openapi.json` no se reenvían a la API; la ruta `/docs` en el puerto `3001` devuelve la aplicación React por el fallback SPA, no la documentación.

### Preparar el entorno

Detén primero el entorno de desarrollo, porque ambos usan el puerto `3001`:

```bash
docker compose down
```

Crea el archivo de producción a partir de la plantilla y cambia la contraseña:

```bash
cp -n .env.production.example .env.production
chmod 600 .env.production
```

`.env.production` está ignorado por Git. `DATABASE_URL` debe usar la misma contraseña que `POSTGRES_PASSWORD`; si contiene caracteres especiales, codifícalos en la URL. Los valores de ejemplo no sirven para uso real.

| Variable | Obligatoria | Uso |
|---|---|---|
| `POSTGRES_DB` | No; por defecto `personal_finance` | Nombre de la base de datos |
| `POSTGRES_USER` | No; por defecto `personal_finance` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | Sí | Contraseña de PostgreSQL; no uses el valor de ejemplo |
| `DATABASE_URL` | Sí | URL interna `postgresql+psycopg://...@db:5432/...` |
| `WEB_PORT` | No; por defecto `3001` | Puerto publicado solo en `127.0.0.1` |

### Construir y arrancar

```bash
docker compose --env-file .env.production -f compose.prod.yaml up --build -d
docker compose --env-file .env.production -f compose.prod.yaml ps
```

El servicio `migrate` aplica Alembic y termina antes de que arranque `api`. Si falla, la API no arranca.

Comprobaciones:

```bash
curl -fsS http://127.0.0.1:3001/healthz
curl -fsS http://127.0.0.1:3001/api/health
WEB_PORT=3001 ./scripts/smoke.sh
```

La prueba de humo comprueba la web, Nginx, el proxy de la API, el resumen y el fallback SPA sin modificar datos.

### Estado y logs

```bash
docker compose --env-file .env.production -f compose.prod.yaml ps
docker compose --env-file .env.production -f compose.prod.yaml logs -f
```

### Detener y reiniciar

```bash
docker compose --env-file .env.production -f compose.prod.yaml down
docker compose --env-file .env.production -f compose.prod.yaml up -d
```

`down` conserva el volumen. No uses `down -v` salvo que quieras borrar los datos y tengas autorización explícita.

Para volver al entorno de desarrollo, detén producción y vuelve a levantar el Compose de desarrollo:

```bash
docker compose --env-file .env.production -f compose.prod.yaml down
docker compose up -d
```

### Diferencias con desarrollo

| Desarrollo | Producción local |
|---|---|
| `compose.yaml` | `compose.prod.yaml` |
| Vite con recarga y código montado | Nginx con frontend compilado |
| API con `--reload` y dependencias de prueba | API sin recarga y solo dependencias de ejecución |
| Web `3001`, API `8000` y PostgreSQL `5433` en localhost | Solo web `3001` en `127.0.0.1` |
| Migraciones manuales | Servicio `migrate` antes de la API |

La entrega es local y no debe exponerse a Internet ni a la LAN. TLS y autenticación quedan fuera del alcance.

## Uso actual

La interfaz de una sola página permite:

- Consultar el balance, el total de ingresos, el total de gastos y el desglose por tipo.
- Crear, editar y eliminar ingresos desde la pestaña `Ingresos`.
- Crear, editar y eliminar gastos con tipo desde la pestaña `Gastos`.
- Ver estados de carga, error con reintento, listas vacías y confirmación antes de eliminar.
- Leer importes en COP con formato `es-CO` y fechas en formato local.

Los formularios validan los datos antes de enviarlos. Los errores se muestran en español sin detalles técnicos.

El endpoint de salud responde:

```json
{
  "status": "ok",
  "database": "ok"
}
```

En desarrollo está en `http://localhost:8000/api/health`; en producción se consulta a través de Nginx en `http://127.0.0.1:3001/api/health`. Si PostgreSQL no está disponible, responde `503` con `status: degraded` y `database: unavailable`.

## API de ingresos

Base: `/api/ingresos`. En desarrollo se usa `http://localhost:8000/api/ingresos`; en producción, `http://127.0.0.1:3001/api/ingresos`. La documentación interactiva `/docs` está disponible solo en desarrollo.

| Método | Ruta | Resultado |
|---|---|---|
| `POST` | `/api/ingresos` | `201` con el ingreso creado |
| `GET` | `/api/ingresos` | `200` con la lista, ordenada por `fecha DESC, id DESC` |
| `GET` | `/api/ingresos/{income_id}` | `200` o `404` |
| `PUT` | `/api/ingresos/{income_id}` | `200` con reemplazo completo, `404` o `422` |
| `DELETE` | `/api/ingresos/{income_id}` | `204`, `404` |

Los ejemplos usan la API de desarrollo. En producción, reemplaza `http://localhost:8000` por `http://127.0.0.1:3001`.

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

Base: `/api/gastos`. En desarrollo se usa `http://localhost:8000/api/gastos`; en producción, `http://127.0.0.1:3001/api/gastos`. La documentación interactiva `/docs` está disponible solo en desarrollo.

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

Los ejemplos usan la API de desarrollo. En producción, reemplaza `http://localhost:8000` por `http://127.0.0.1:3001`.

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

`GET /api/resumen` devuelve los totales globales, el balance y el desglose de gastos por tipo. No acepta parámetros ni filtros. En desarrollo se consulta en `http://localhost:8000/api/resumen`; en producción, en `http://127.0.0.1:3001/api/resumen`.

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

Con Docker Compose de desarrollo:

```bash
docker compose exec api uv run alembic upgrade head
docker compose exec api uv run alembic current
docker compose exec api uv run alembic downgrade -1
```

En producción, el servicio `migrate` ejecuta `alembic upgrade head` antes de arrancar la API. Para volver a aplicarlo o consultar la revisión actual:

```bash
docker compose --env-file .env.production -f compose.prod.yaml run --rm migrate
docker compose --env-file .env.production -f compose.prod.yaml exec -T api alembic current
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

## Respaldo de producción

La entrega de producción conserva los datos en el volumen `py-personal-finance-prod_postgres_data`.

Respaldo manual:

```bash
docker compose --env-file .env.production -f compose.prod.yaml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > respaldo.sql
```

La restauración se hace en un entorno controlado y con la API detenida:

```bash
cat respaldo.sql | docker compose --env-file .env.production -f compose.prod.yaml exec -T db \
  sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

`docker compose --env-file .env.production -f compose.prod.yaml down` conserva el volumen. `down -v` elimina los datos y requiere autorización explícita.

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

No uses los valores de ejemplo en producción. La entrega de producción usa `.env.production`; consulta la sección “Entrega de producción local”.

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
│   ├── Dockerfile.api
│   ├── Dockerfile.web
│   └── nginx.conf
├── scripts/
│   └── smoke.sh
├── specs/                  # Especificaciones SDD
├── compose.yaml
├── compose.prod.yaml
├── .env.example
├── .env.production.example
├── .dockerignore
├── constitution.md
└── AGENTS.md
```

`legacy/` contiene una implementación anterior y está fuera de alcance.

## Solución de problemas

### La entrega de producción no arranca

```bash
docker compose --env-file .env.production -f compose.prod.yaml ps -a
docker compose --env-file .env.production -f compose.prod.yaml logs migrate api web
docker compose --env-file .env.production -f compose.prod.yaml config -q
```

Comprueba que el entorno de desarrollo esté detenido y que `POSTGRES_PASSWORD` y `DATABASE_URL` estén definidos. Si `migrate` falla, la API no arranca por diseño.

### OpenAPI no funciona en producción

Es esperado. La documentación OpenAPI está disponible solo en desarrollo. Para consultarla, detén producción y levanta el Compose de desarrollo:

```bash
docker compose --env-file .env.production -f compose.prod.yaml down
docker compose up -d
```

Después abre `http://localhost:8000/docs`. En producción, `/docs` en el puerto `3001` devuelve la aplicación React, no OpenAPI.

### La interfaz muestra "No se pudieron cargar los datos" en desarrollo

```bash
docker compose ps
curl -i http://localhost:8000/api/health
docker compose logs api
```

Si PostgreSQL está detenido, la API responde `503`; es el comportamiento esperado.

En producción, usa `http://127.0.0.1:3001/api/health` y revisa los logs de `api` y `web` con `compose.prod.yaml`.

### Un puerto está ocupado

En desarrollo, cambia `API_PORT`, `WEB_PORT` o `DB_PORT` en `.env` y vuelve a levantar:

```bash
docker compose up -d
```

En producción, cambia `WEB_PORT` en `.env.production` y vuelve a levantar el Compose de producción.

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
- [`specs/006-entrega-docker/`](specs/006-entrega-docker/): especificación, plan y tareas de la entrega Docker.

El flujo es: especificación → clarificación → plan → tareas → implementación → validación.
