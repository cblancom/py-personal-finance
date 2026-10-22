# Tareas 006 — Entrega Docker

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──┐
        ├──► T-003 ──► T-004 ──► T-005 ──► T-006 ──► T-007
T-002 ──┘
```

T-001 y T-002 pueden ejecutarse en paralelo después de aprobar el plan. T-003 integra las imágenes y la configuración; T-004 completa migraciones, salud y persistencia. T-007 cierra la validación y actualiza la evidencia.

## Tareas

- [x] **T-001 — Crear la imagen de producción de la API**
  - Requisitos: FR-001, NFR-007.
  - Dependencias: ninguna.
  - Descripción: reorganizar `docker/Dockerfile.api` en etapas `base`, `prod` y `dev`. La etapa `prod` instala solo dependencias de ejecución, copia `app`, `alembic` y `alembic.ini`, ejecuta como usuario no root y arranca Uvicorn sin `--reload`. La etapa `dev` conserva las dependencias de prueba. Añadir `build.target: dev` en `compose.yaml`.
  - Hecho cuando: la imagen de producción construye; no incluye `pytest` ni `ruff`; el contenedor no ejecuta como root; la imagen de desarrollo sigue ejecutando la suite completa.
  - Evidencia (2026-10-21): `Dockerfile.api` dividido en etapas `base`, `dev` y `prod`; `compose.yaml` usa `target: dev`. La imagen `prod` ejecuta como UID 10001, no incluye `pytest`, `ruff` ni `tests/`, y `/api/health` responde `200` con PostgreSQL. La imagen `dev` conserva las dependencias de prueba; 135/135 pruebas pasan.
  - Verificación:
    ```bash
    docker build -f docker/Dockerfile.api --target prod -t py-personal-finance-api-prod .
    docker run --rm --entrypoint sh py-personal-finance-api-prod -c 'command -v pytest || true; id -u'
    docker compose build api
    docker compose exec api uv run pytest
    ```

- [x] **T-002 — Crear la imagen web y la configuración de Nginx**
  - Requisitos: FR-002, FR-003, FR-011, NFR-004.
  - Dependencias: ninguna.
  - Descripción: crear `docker/Dockerfile.web` con build de Node 20 y runtime `nginxinc/nginx-unprivileged:1.27-alpine`. Crear `docker/nginx.conf` con estáticos, fallback SPA, proxy `/api`, `/healthz`, gzip, caché de assets, `index.html` sin caché y cabeceras de seguridad.
  - Hecho cuando: la imagen final no contiene Node ni `node_modules`; Nginx valida la configuración; sirve la SPA y reenvía `/api`; el contenedor no ejecuta como root.
  - Evidencia (2026-10-21): `Dockerfile.web` compila el frontend con Node 20 y copia `dist` a `nginxinc/nginx-unprivileged:1.27-alpine`; la imagen final no contiene Node ni `node_modules`. Nginx valida la configuración, ejecuta como UID 101, sirve `/` y `/healthz` con `200`, reenvía `/api/health` y `/api/resumen` con `200`, resuelve el fallback SPA y aplica caché de assets y cabeceras de seguridad.
  - Verificación:
    ```bash
    docker build -f docker/Dockerfile.web -t py-personal-finance-web-prod .
    docker run --rm --add-host api:127.0.0.1 --entrypoint nginx py-personal-finance-web-prod -t
    docker run --rm --entrypoint sh py-personal-finance-web-prod -c 'id -u; command -v node || true'
    ```

- [x] **T-003 — Crear el Compose de producción**
  - Requisitos: FR-004, FR-005, FR-008, FR-011, NFR-002.
  - Dependencias: T-001, T-002.
  - Descripción: crear `compose.prod.yaml` con nombre de proyecto propio y servicios `db`, `migrate`, `api` y `web`. Sin bind mounts; solo `web` publicada en `127.0.0.1:${WEB_PORT:-3001}:8080`; API y base sin puertos; volumen nombrado; `restart: unless-stopped`; healthchecks. Crear `.env.production.example` y la excepción en `.gitignore`. Documentar que el Compose de desarrollo debe estar detenido porque ambos usan `3001`.
  - Hecho cuando: `config -q` pasa con un entorno válido; falla si faltan `POSTGRES_PASSWORD` o `DATABASE_URL`; ningún puerto de API o base se publica; no hay secretos en el Compose; el conflicto de puerto con desarrollo está documentado.
  - Evidencia (2026-10-21): `compose.prod.yaml` usa el proyecto `py-personal-finance-prod` y define `db`, `migrate`, `api` y `web`; solo `web` publica `127.0.0.1:3001:8080`; API y base no publican puertos; `migrate` ejecuta `alembic upgrade head`; PostgreSQL usa el volumen `postgres_data`; hay healthchecks y `restart` en los servicios de larga duración. `.env.production.example` está versionado y `.env.production` queda ignorado. `config -q` pasa con la plantilla y falla si faltan `POSTGRES_PASSWORD` o `DATABASE_URL`.
  - Verificación:
    ```bash
    cp .env.production.example .env.production
    docker compose --env-file .env.production -f compose.prod.yaml config -q
    docker compose --env-file .env.production -f compose.prod.yaml config | grep -n 'published'
    git check-ignore .env.production
    ```

- [x] **T-004 — Implementar migraciones, salud y persistencia**
  - Requisitos: FR-006, FR-007, FR-008.
  - Dependencias: T-003.
  - Descripción: configurar `migrate` con `alembic upgrade head`, dependencia de `db` saludable y `api` dependiente de `migrate` mediante `service_completed_successfully`. Añadir healthchecks de API y web y verificar el volumen de PostgreSQL. Documentar el respaldo manual.
  - Hecho cuando: la migración termina antes de la API; repetirla es seguro; una migración fallida impide arrancar la API; los datos persisten tras `down`/`up` sin `-v`; los healthchecks reflejan el estado real.
  - Evidencia (2026-10-21): `migrate` aplicó `0001` a `0003` antes de arrancar `api` y terminó con código `0`; repetir `alembic upgrade head` no aplicó cambios. `api` y `web` quedaron healthy; `/api/health`, `/api/resumen` y `/healthz` responden `200`. Una migración forzada a fallar dejó `api` sin arrancar. Un ingreso temporal sobrevivió a `down`/`up` sin `-v` y se eliminó después. El respaldo con `pg_dump` genera un volcado válido. Volumen separado `py-personal-finance-prod_postgres_data`.
  - Verificación:
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml up --build -d
    docker compose --env-file .env.production -f compose.prod.yaml run --rm migrate
    docker compose --env-file .env.production -f compose.prod.yaml ps
    docker compose --env-file .env.production -f compose.prod.yaml down
    docker compose --env-file .env.production -f compose.prod.yaml up -d
    ```

- [x] **T-005 — Crear la prueba de humo**
  - Requisitos: FR-009.
  - Dependencias: T-004.
  - Descripción: crear `scripts/smoke.sh` ejecutable con comprobaciones de solo lectura para `/`, `/healthz`, `/api/health`, `/api/resumen` y fallback SPA. Usar `WEB_PORT`, `curl -fsS` y reintentos acotados para esperar el arranque; fallar con código distinto de cero y mostrar la comprobación fallida.
  - Hecho cuando: el script pasa con la entrega sana; falla si un servicio no responde; no crea, edita ni elimina datos.
  - Evidencia (2026-10-21): `scripts/smoke.sh` es ejecutable, valida `/`, `/healthz`, `/api/health`, `/api/resumen` y el fallback SPA, y no modifica datos. Con la entrega sana pasa; con `web` detenida termina con código `1` y muestra `la web no responde`. Permite acortar los reintentos con `SMOKE_RETRIES` y `SMOKE_DELAY`.
  - Verificación:
    ```bash
    WEB_PORT=3001 ./scripts/smoke.sh
    docker compose --env-file .env.production -f compose.prod.yaml stop web
    WEB_PORT=3001 ./scripts/smoke.sh
    docker compose --env-file .env.production -f compose.prod.yaml start web
    ```

- [x] **T-006 — Documentar la entrega**
  - Requisitos: FR-007, FR-010.
  - Dependencias: T-005.
  - Descripción: actualizar README, AGENTS y `specs/README.md` con el flujo de producción, variables, puerto `3001`, comandos de estado y logs, migraciones, persistencia, respaldo/restauración y diferencias con desarrollo. Mantener la advertencia sobre `down -v` y la ausencia de exposición externa.
  - Hecho cuando: los comandos documentados coinciden con los archivos reales; se explica cómo crear `.env.production`; se distingue desarrollo de producción; el índice SDD refleja el estado.
  - Evidencia (2026-10-21): README incorpora la sección “Entrega de producción local” con preparación de `.env.production`, variables, build, salud, logs, detención, diferencias con desarrollo, migraciones y respaldo/restauración. AGENTS añade los comandos de producción y la verificación específica; `specs/README.md` refleja T-001 a T-006. Los comandos documentados usan `compose.prod.yaml`, `--env-file .env.production`, `WEB_PORT=3001` y `scripts/smoke.sh`.
  - Verificación:
    ```bash
    grep -n 'compose.prod.yaml' README.md AGENTS.md
    grep -n '3001' README.md AGENTS.md
    git diff --check
    ```

- [x] **T-007 — Validar la entrega completa**
  - Requisitos: AC-001 a AC-014, NFR-001, NFR-003, NFR-007.
  - Dependencias: T-006.
  - Descripción: ejecutar la validación completa desde un entorno limpio de contenedores, sin borrar volúmenes con datos: configuración, build, arranque, salud, smoke test, migraciones, persistencia, puertos, usuarios no root, revisión de logs y suites de backend/frontend. Registrar la evidencia y marcar la especificación como validada.
  - Hecho cuando: todos los AC se cumplen; no hay regresiones; los servicios quedan healthy; la documentación refleja el estado; los archivos temporales de la prueba se eliminan.
  - Evidencia (2026-10-21): validación completa con `.env.production`: `config -q` OK; `down`/`up --build` sin `-v`; `api`, `db` y `web` healthy; `migrate` en `0003` y segunda ejecución con código `0`; smoke OK y fallo controlado con `web` detenida; un ingreso temporal sobrevivió al reinicio y se eliminó; UID `10001` en API y `101` en web; imágenes sin archivos `.env`; logs sin contraseña ni `DATABASE_URL`; frontend 50/50 con lint, typecheck y build; backend 63 unitarias locales y 135/135 en Docker. La entrega de producción queda arriba en `127.0.0.1:3001`.
  - Verificación:
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml config -q
    docker compose --env-file .env.production -f compose.prod.yaml up --build -d
    WEB_PORT=3001 ./scripts/smoke.sh
    docker compose --env-file .env.production -f compose.prod.yaml ps
    docker compose --env-file .env.production -f compose.prod.yaml exec -T api id -u
    docker compose --env-file .env.production -f compose.prod.yaml exec -T web id -u
    (cd frontend && npm run lint && npm run typecheck && npm run test && npm run build)
    (cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest)
    docker compose exec api uv run pytest
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-001 |
| FR-002 | T-002 |
| FR-003 | T-002 |
| FR-004 | T-003 |
| FR-005 | T-003 |
| FR-006 | T-004 |
| FR-007 | T-004, T-006 |
| FR-008 | T-003, T-004 |
| FR-009 | T-005 |
| FR-010 | T-006 |
| FR-011 | T-001, T-002, T-003 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-007 |
| NFR-002 | T-003, T-007 |
| NFR-003 | T-007 |
| NFR-004 | T-002 |
| NFR-005 | T-003, T-004 |
| NFR-006 | T-001 a T-007 |
| NFR-007 | T-001, T-007 |
| NFR-008 | T-001 a T-007 |

## Evidencia de validación

Se completa durante T-007.

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumple | `docker compose --env-file .env.production -f compose.prod.yaml config -q` pasa. |
| AC-002 | Cumple | `down`/`up --build` sin `-v` deja `api`, `db` y `web` healthy. |
| AC-003 | Cumple | `http://127.0.0.1:3001/` responde `200`. |
| AC-004 | Cumple | `/healthz` responde `200` con `ok`. |
| AC-005 | Cumple | `/api/health` responde `200` con `database: ok`. |
| AC-006 | Cumple | `/api/resumen` responde `200`. |
| AC-007 | Cumple | Ruta SPA inexistente devuelve la aplicación. |
| AC-008 | Cumple | Solo `web` publica `127.0.0.1:3001`; API y DB no publican puertos. |
| AC-009 | Cumple | `migrate` aplica `0003`, se puede repetir y un fallo deja la API sin arrancar. |
| AC-010 | Cumple | Un ingreso temporal sobrevivió a `down`/`up` sin `-v` y se eliminó después. |
| AC-011 | Cumple | API UID `10001`, web UID `101`; imágenes sin `.env`; logs sin contraseña ni `DATABASE_URL`. |
| AC-012 | Cumple | `scripts/smoke.sh` pasa con la entrega sana y falla con web detenida. |
| AC-013 | Cumple | Frontend 50/50, lint, typecheck y build; backend 63 unitarias y 135/135 en Docker. |
| AC-014 | Cumple | README, AGENTS y `specs/README.md` reflejan comandos, puerto y estado. |

## Notas

- No se modifican la API, el frontend ni el esquema de la base de datos.
- No se añaden dependencias de aplicación; Nginx es una pieza de infraestructura.
- El puerto externo se mantiene en `3001`; el `8080` del host está ocupado.
- Desarrollo y producción comparten el puerto `3001`, por lo que no deben estar levantados a la vez.
- La entrega es local: solo se publica la web en `127.0.0.1`.
- No se exponen la API ni PostgreSQL fuera de la red de Docker.
- No se migran datos de desarrollo a producción.
- No se implementan TLS, autenticación, CI/CD, registry, Kubernetes ni backups automáticos.
- `down -v` es destructivo y requiere autorización explícita.
- El Compose de desarrollo debe seguir funcionando.
