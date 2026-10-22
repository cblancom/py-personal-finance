# Plan técnico 006 — Entrega Docker

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Fase: 4.
- Iteración: MVP.

## 1. Resumen de la solución

Se añade una entrega local de producción sobre Docker Compose, separada del entorno de desarrollo:

- El frontend se compila con Node y se sirve como archivos estáticos desde Nginx.
- Nginx es el único punto de entrada del navegador y actúa como proxy de `/api`.
- La API se ejecuta sin `--reload`, sin código montado y sin dependencias de desarrollo.
- Las migraciones se aplican en un servicio `migrate` antes de arrancar la API.
- PostgreSQL usa un volumen nombrado y no publica su puerto.
- Solo la web se publica en `127.0.0.1:3001`.
- La entrega se valida con una prueba de humo de solo lectura.

El Compose de desarrollo se conserva. La nueva entrega usa un archivo y un proyecto de Compose distintos.

## 2. Arquitectura y flujo de datos

```text
Navegador
   │  http://127.0.0.1:3001
   ▼
┌─────────────────────────────┐
│ web: Nginx (puerto 8080)    │
│                             │
│ /, /assets/*  ──► dist/     │
│ /api/*        ──► api:8000  │
│ /healthz      ──► 200       │
└──────────────┬──────────────┘
               │ red interna de Compose
               ▼
┌─────────────────────────────┐
│ api: Uvicorn (puerto 8000)  │
│ sin puerto publicado        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ db: PostgreSQL (5432)       │
│ sin puerto publicado        │
│ volumen postgres_data       │
└─────────────────────────────┘

migrate: ejecuta Alembic y termina antes de arrancar api
```

El navegador solo conoce `http://127.0.0.1:3001`. Nginx conserva la ruta `/api/...` al reenviarla, de modo que la API sigue recibiendo las mismas rutas que en desarrollo.

## 3. Componentes y responsabilidades

| Archivo | Responsabilidad |
|---|---|
| `docker/Dockerfile.api` | Imagen de la API con etapas `dev` y `prod`. |
| `docker/Dockerfile.web` | Build del frontend y runtime de Nginx. |
| `docker/nginx.conf` | Estáticos, fallback SPA, proxy `/api`, caché, cabeceras y `/healthz`. |
| `compose.prod.yaml` | Servicios `db`, `migrate`, `api` y `web`; redes, puertos, salud y volumen. |
| `.env.production.example` | Plantilla de variables de producción. |
| `scripts/smoke.sh` | Comprobaciones de solo lectura de la entrega. |
| `compose.yaml` | Sin cambios funcionales; apunta a la etapa `dev` de la imagen de la API. |
| `README.md` | Uso, operación, respaldo y diferencias con desarrollo. |
| `AGENTS.md` | Comandos canónicos de la entrega. |
| `specs/README.md` | Estado de la especificación 006. |

No se modifican archivos de `backend/app`, `frontend/src` ni el contrato de la API.

## 4. Imagen de producción de la API

`docker/Dockerfile.api` se reorganiza en etapas:

### Etapa `base`

- `python:3.13-slim`.
- `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`.
- `uv` copiado desde `ghcr.io/astral-sh/uv:0.11.21`.
- `UV_PROJECT_ENVIRONMENT=/opt/venv` y `UV_CACHE_DIR=/tmp/uv-cache`.
- Copia de `backend/pyproject.toml` y `backend/uv.lock`.
- `uv sync --frozen --no-dev`.
- `PATH` con `/opt/venv/bin`.
- Copia de `backend/app`, `backend/alembic` y `backend/alembic.ini`.

### Etapa `prod`

- Crea un usuario de sistema sin privilegios.
- Ejecuta como ese usuario.
- Expone `8000` solo dentro de la red de Docker.
- `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`.
- No incluye `tests/` ni dependencias de desarrollo.

### Etapa `dev`

- Instala también el grupo `dev` con `uv sync --frozen`.
- Copia `backend/` completo, incluidas las pruebas.
- Mantiene el comando basado en `uv run` para el Compose de desarrollo.
- `compose.yaml` añade `build.target: dev`.

La imagen de producción no se usa para ejecutar pruebas. La suite se sigue ejecutando en la imagen de desarrollo.

## 5. Imagen y configuración del frontend

`docker/Dockerfile.web` usa dos etapas:

### Etapa de build

- `node:20-alpine`.
- `WORKDIR /app`.
- Copia de `frontend/package.json` y `frontend/package-lock.json`.
- `npm ci`.
- Copia del resto de `frontend/`.
- `npm run build`.

### Etapa de runtime

- `nginxinc/nginx-unprivileged:1.27-alpine`.
- Copia de `docker/nginx.conf` a la configuración del servidor.
- Copia de `/app/dist` a `/usr/share/nginx/html`.
- `EXPOSE 8080`.
- Nginx se ejecuta con el usuario no root de la imagen.

No se pasa ninguna URL de API al build: el frontend usa rutas relativas `/api`, igual que ahora.

## 6. Configuración de Nginx

`docker/nginx.conf` define un servidor en `8080` con:

- `root /usr/share/nginx/html` e `index index.html`.
- `location = /healthz` con respuesta `200` y cuerpo `ok`.
- `location /api/` con `proxy_pass http://api:8000` sin URI adicional, para conservar `/api/...`.
- Cabeceras de proxy: `Host`, `X-Real-IP`, `X-Forwarded-For` y `X-Forwarded-Proto`.
- `location /assets/` con caché larga e inmutable.
- `location = /index.html` sin caché.
- `location /` con `try_files $uri $uri/ /index.html`.
- `gzip` para tipos de texto.
- Cabeceras `X-Content-Type-Options`, `Referrer-Policy` y `X-Frame-Options`.
- `server_tokens off`.

No se configura CORS. No se reenvían `/docs`, `/openapi.json` ni `/health`; solo `/api/`, que ya contiene las rutas de dominio y `/api/health`.

## 7. Compose de producción

`compose.prod.yaml` define:

```text
name: py-personal-finance-prod
```

### `db`

- `postgres:16-alpine`.
- Variables `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`.
- Volumen `postgres_data`.
- Healthcheck con `pg_isready`.
- Sin puertos publicados.
- `restart: unless-stopped`.

### `migrate`

- Build de `docker/Dockerfile.api`, etapa `prod`.
- Comando `alembic upgrade head`.
- `DATABASE_URL` desde el entorno.
- Depende de `db` saludable.
- Sin reinicio automático; debe terminar y dejar paso a la API.

### `api`

- Build de `docker/Dockerfile.api`, etapa `prod`.
- `DATABASE_URL` desde el entorno.
- Depende de `db` saludable y de `migrate` completado correctamente.
- Healthcheck contra `/api/health`.
- Sin puertos publicados.
- `restart: unless-stopped`.

### `web`

- Build de `docker/Dockerfile.web`.
- Publica `127.0.0.1:${WEB_PORT:-3001}:8080`.
- Depende de `api` saludable.
- Healthcheck contra `/healthz`.
- `restart: unless-stopped`.

El proyecto y el volumen de producción son independientes de los de desarrollo. Esto evita reutilizar datos de prueba por accidente.

Como el Compose de desarrollo también publica la web en `3001`, hay que detenerlo antes de arrancar producción. Los volúmenes de desarrollo se conservan.

## 8. Configuración y secretos

`.env.production.example` contendrá:

```dotenv
POSTGRES_DB=personal_finance
POSTGRES_USER=personal_finance
POSTGRES_PASSWORD=cambia-esta-contrasena
DATABASE_URL=postgresql+psycopg://personal_finance:cambia-esta-contrasena@db:5432/personal_finance
WEB_PORT=3001
```

Reglas:

- `.env.production` se crea a partir de la plantilla y no se versiona.
- `.gitignore` mantiene `.env.*` y añade una excepción para `.env.production.example`.
- `POSTGRES_PASSWORD` y `DATABASE_URL` son obligatorios mediante `${VAR:?mensaje}` en Compose.
- La contraseña de ejemplo debe reemplazarse.
- Si la contraseña contiene caracteres especiales, deben codificarse en `DATABASE_URL`.
- No se pasan secretos como `ARG` de Docker ni se copian al contexto de build.

## 9. Migraciones y arranque

El servicio `migrate` usa la misma imagen que la API y ejecuta:

```bash
alembic upgrade head
```

La API no arranca hasta que `migrate` termina con código `0`. Si Alembic falla:

- `migrate` queda en error.
- `api` no se inicia.
- Los logs muestran el error sin credenciales.

Ejecutar el servicio de nuevo es seguro porque `alembic upgrade head` es idempotente cuando no hay revisiones pendientes. No se implementa creación automática de tablas ni `Base.metadata.create_all()`.

## 10. Persistencia y respaldo

PostgreSQL usa el volumen nombrado `postgres_data` dentro del proyecto de producción.

Operaciones documentadas:

```bash
docker compose --env-file .env.production -f compose.prod.yaml down
docker compose --env-file .env.production -f compose.prod.yaml up -d
```

`down` conserva el volumen. `down -v` elimina los datos y se documenta como operación destructiva que requiere autorización.

Respaldo manual:

```bash
docker compose --env-file .env.production -f compose.prod.yaml \
  exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > respaldo.sql
```

La restauración se documenta para un entorno controlado y no se automatiza.

## 11. Prueba de humo

`scripts/smoke.sh` será un script Bash con `set -euo pipefail` que:

- Usa `BASE_URL=http://127.0.0.1:${WEB_PORT:-3001}`.
- Comprueba `/` con `curl --retry 30 --retry-delay 2 --retry-all-errors -fsS`.
- Comprueba `/healthz`.
- Comprueba `/api/health` y busca `"status":"ok"`.
- Comprueba `/api/resumen` y busca `"balance"`.
- Comprueba el fallback SPA en una ruta inexistente.
- Falla si alguna respuesta no es la esperada.

No modifica datos. Se puede ejecutar con la entrega levantada y no requiere dependencias fuera de `curl` y utilidades de shell.

## 12. Seguridad y límites

- Solo `web` se publica en el host, en `127.0.0.1`.
- `api` y `db` no tienen puertos publicados.
- `api` y `web` se ejecutan como usuarios no root.
- No hay bind mounts de código en producción.
- No se incluyen secretos en imágenes.
- Los logs no incluyen `DATABASE_URL` ni contraseñas.
- Nginx no expone documentación OpenAPI.
- No se implementan TLS, autenticación, rootless Docker, seccomp personalizado ni firmas de imagen.

## 13. Estrategia de pruebas y validación

### Configuración

```bash
docker compose --env-file .env.production -f compose.prod.yaml config -q
```

### Construcción y arranque

```bash
docker compose --env-file .env.production -f compose.prod.yaml up --build -d
docker compose --env-file .env.production -f compose.prod.yaml ps
```

### Prueba de humo

```bash
WEB_PORT=3001 ./scripts/smoke.sh
```

### Migraciones

```bash
docker compose --env-file .env.production -f compose.prod.yaml run --rm migrate
```

La segunda ejecución debe terminar correctamente sin cambios pendientes.

### Persistencia

1. Crear un movimiento temporal mediante la API.
2. Ejecutar `down` y `up` sin `-v`.
3. Verificar que el movimiento sigue existiendo.
4. Eliminarlo y comprobar que la base queda limpia.

### Seguridad y puertos

```bash
docker compose --env-file .env.production -f compose.prod.yaml exec -T api id -u
docker compose --env-file .env.production -f compose.prod.yaml exec -T web id -u
docker compose --env-file .env.production -f compose.prod.yaml ps
docker compose --env-file .env.production -f compose.prod.yaml logs | grep -Ei 'password|postgresql\+psycopg' || true
```

### Regresión

```bash
(cd frontend && npm run lint && npm run typecheck && npm run test && npm run build)
(cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest)
docker compose exec api uv run pytest
```

## 14. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| El proxy reescribe mal `/api` | `proxy_pass http://api:8000` sin URI adicional y prueba de humo. |
| La imagen de producción usa dependencias de desarrollo | Etapa `prod` con `uv sync --frozen --no-dev` y verificación de que `pytest` no está instalado. |
| La API arranca antes de migrar | `depends_on` con `service_completed_successfully` y healthcheck de `db`. |
| Se filtran secretos en logs o imágenes | Variables de entorno, `.env.production` ignorado y revisión de logs. |
| Se reutiliza el volumen de desarrollo | Nombre de proyecto y volumen separados. |
| `down -v` borra datos por accidente | Documentación destacada y comando destructivo fuera del flujo normal. |
| El contenedor no root no puede leer Nginx o los estáticos | Copias con permisos de lectura y prueba de arranque. |
| El puerto `3001` está ocupado | Detener el Compose de desarrollo o cambiar `WEB_PORT`; mensaje de error claro. |
| El build del frontend no es reproducible | `npm ci` con `package-lock.json`. |
| Una migración falla y deja la API caída | `migrate` falla de forma visible; se corrige y se vuelve a ejecutar. |

## 15. Trazabilidad requisitos → plan

| Requisito | Secciones del plan | Tareas |
|---|---|---|
| FR-001 | 4 | T-001 |
| FR-002 | 5 | T-002 |
| FR-003 | 6 | T-002 |
| FR-004 | 7 | T-003 |
| FR-005 | 8 | T-003 |
| FR-006 | 9 | T-004 |
| FR-007 | 10 | T-004, T-006 |
| FR-008 | 7, 12 | T-003, T-004 |
| FR-009 | 11 | T-005 |
| FR-010 | 13 | T-006 |
| FR-011 | 12 | T-001, T-002, T-003 |
| NFR-001 | 13 | T-007 |
| NFR-002 | 8, 12 | T-003, T-007 |
| NFR-003 | 7, 13 | T-007 |
| NFR-004 | 6 | T-002 |
| NFR-005 | 7, 12 | T-003, T-004 |
| NFR-006 | 3 | Todas |
| NFR-007 | 4, 13 | T-001, T-007 |
| NFR-008 | 1, 12 | Todas |

## 16. Aprobación y siguiente paso

Este plan fue aprobado. La implementación avanza por las tareas de `tasks.md` en orden, empezando por las imágenes y terminando con la validación completa.

No se modifica `legacy/`, no se añaden dependencias de aplicación y no se exponen la API ni PostgreSQL fuera de la red de Docker.
