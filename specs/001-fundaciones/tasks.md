# Tareas 001 — Fundaciones del proyecto

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-003 ──► T-004 ──► T-009
                      └───► T-005
T-006 ──► T-007 ──► T-008

T-005, T-008, T-009 ──► T-010 ──► T-011 ──► T-012
```

El backend y el frontend pueden avanzar en paralelo después de T-001. T-010 integra ambos y requiere que T-005, T-008 y T-009 estén terminadas.

## Tareas

- [x] **T-001 — Crear el esqueleto del backend y fijar dependencias**
  - Requisitos: FR-001, FR-010, NFR-004, NFR-008.
  - Dependencias: ninguna.
  - Descripción: crear `backend/app/{api/routes,api/schemas,core,db}`, `backend/tests/` y `backend/pyproject.toml`; declarar dependencias de ejecución y desarrollo; configurar ruff y pytest; generar `uv.lock`.
  - Hecho cuando: `uv sync` instala todo; `uv run ruff check .` y `uv run ruff format --check .` pasan; `uv.lock` existe.
  - Evidencia (2026-10-21): `uv sync` instaló 35 paquetes; `ruff check` y `ruff format --check` pasan (7 archivos formateados); imports de FastAPI, SQLAlchemy, Alembic y psycopg correctos; `uv.lock` generado.
  - Verificación:
    ```bash
    cd backend
    uv sync
    uv run ruff check .
    uv run ruff format --check .
    uv run python -c "import fastapi, sqlalchemy, alembic, psycopg"
    ```

- [x] **T-002 — Implementar la configuración por entorno**
  - Requisitos: FR-003, NFR-002, NFR-007.
  - Dependencias: T-001.
  - Descripción: crear `app/core/config.py` con `Settings`, `load_settings(env)` y `get_settings()`; exigir `DATABASE_URL` y fallar con un mensaje que no exponga su valor. Añadir pruebas unitarias para configuración válida y ausente.
  - Hecho cuando: las pruebas de configuración pasan y el mensaje de error nombra `DATABASE_URL` sin mostrar secretos.
  - Evidencia (2026-10-21): 5 pruebas pasan; se cubren URL válida, variable ausente, valor en blanco, no filtración de otros valores y caché de `get_settings`. Ruff y formato pasan (10 archivos).
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core/test_config.py
    uv run ruff check .
    ```

- [x] **T-003 — Crear las fundaciones de SQLAlchemy**
  - Requisitos: FR-004, NFR-003.
  - Dependencias: T-001, T-002.
  - Descripción: crear `app/db/base.py` con `Base` y `app/db/session.py` con motor, `pool_pre_ping`, `connect_timeout=3`, `SessionLocal` y `get_db`. No usar `create_all`.
  - Hecho cuando: los módulos importan con una `DATABASE_URL` válida, no existe ninguna llamada a `create_all` y ruff pasa.
  - Evidencia (2026-10-21): import de `engine`, `SessionLocal` y `get_db` correcto (driver `postgresql`); no hay llamadas a `create_all`; ruff check y format pasan (12 archivos); las 5 pruebas existentes siguen pasando.
  - Verificación:
    ```bash
    cd backend
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance \
      uv run python -c "from app.db.session import engine, SessionLocal, get_db; print(engine.url.get_backend_name())"
    grep -R "create_all" app tests || true
    uv run ruff check .
    ```

- [x] **T-004 — Implementar `/api/health` con pruebas unitarias**
  - Requisitos: FR-002, FR-004, FR-008, NFR-006, NFR-007.
  - Dependencias: T-003.
  - Descripción: crear `app/api/schemas/health.py`, `app/api/routes/health.py` y registrar el router en `app/main.py`. Escribir primero las pruebas de éxito y fallo con sustitución de `get_db`. Responder `503` sin filtrar detalles de la excepción.
  - Hecho cuando: `uv run pytest` pasa sin PostgreSQL; `/api/health` aparece en OpenAPI; las respuestas tienen la forma acordada.
  - Evidencia (2026-10-21): 9 pruebas pasan sin PostgreSQL (5 de configuración y 4 de salud); se cubren `200`, `503`, no filtración de credenciales en respuesta/logs y presencia en OpenAPI. `ruff check` y format pasan (18 archivos). Se sustituyó `httpx` por `httpx2` para eliminar el warning de deprecación de `TestClient`.
  - Verificación:
    ```bash
    cd backend
    uv run pytest
    uv run ruff check .
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance \
      uv run python -c "from app.main import app; print('/api/health' in app.openapi()['paths'])"
    ```

- [x] **T-005 — Inicializar Alembic y crear la revisión base**
  - Requisitos: FR-005, NFR-003.
  - Dependencias: T-003.
  - Descripción: crear `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako` y `alembic/versions/0001_baseline.py`. Obtener la URL desde `get_settings()`, escapar `%` y usar `Base.metadata` como metadata objetivo. La revisión base no crea tablas.
  - Hecho cuando: Alembic reconoce la revisión `0001`; no hay URL fija en `alembic.ini`; upgrade y downgrade se validan en T-012.
  - Evidencia (2026-10-21): `alembic history` muestra `<base> -> 0001 (head), baseline`; `alembic heads` muestra `0001 (head)`; `sqlalchemy.url` está vacío en `alembic.ini`; la revisión base no crea tablas. Ruff y formato pasan (20 archivos); las 9 pruebas siguen pasando. Upgrade/downgrade quedan para T-012.
  - Verificación:
    ```bash
    cd backend
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance \
      uv run alembic history
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/personal_finance \
      uv run alembic heads
    ```

- [x] **T-006 — Crear el frontend y configurar calidad y pruebas**
  - Requisitos: FR-001, FR-009, FR-010, NFR-004, NFR-008.
  - Dependencias: ninguna.
  - Descripción: crear `frontend/` con Vite + React + TypeScript estricto; instalar ESLint, Vitest, jsdom, Testing Library y jest-dom; definir scripts `dev`, `lint`, `typecheck`, `test`, `build`; añadir configuración de pruebas y una prueba de humo.
  - Hecho cuando: todos los comandos de calidad pasan y `package-lock.json` existe.
  - Evidencia (2026-10-21): `npm ci` instala 252 paquetes sin vulnerabilidades; `lint`, `typecheck`, `test` (1 prueba) y `build` pasan. Se usa React 19.3.1, Vite 8.3.5, Vitest 4.1.12, TypeScript 6.0.3 y ESLint 10.13.0. Se fijaron `jsdom` 27.4.0 y `@testing-library/jest-dom` 6.9.1 por compatibilidad con Node 20. `package-lock.json` generado.
  - Verificación:
    ```bash
    cd frontend
    npm ci
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```

- [x] **T-007 — Crear el cliente HTTP, los tipos y el proxy**
  - Requisitos: FR-006, NFR-003, NFR-007.
  - Dependencias: T-006.
  - Descripción: configurar el proxy `/api` en `vite.config.ts` con `VITE_API_PROXY_TARGET`; crear `src/types/health.ts`, `src/api/client.ts` y `src/api/health.ts`. Los componentes no deben contener URLs absolutas.
  - Hecho cuando: typecheck y build pasan; el proxy apunta a `http://localhost:8000` por defecto y a `http://api:8000` en Compose.
  - Evidencia (2026-10-21): proxy `/api` configurable mediante `VITE_API_PROXY_TARGET`, con valor por defecto `http://localhost:8000`; cliente `fetch` relativo con `ApiError`, tipos de salud y `getHealth`. 3 pruebas pasan (1 de App y 2 del cliente); lint, typecheck y build pasan; no hay URLs absolutas en `src`. La asignación `http://api:8000` se valida al crear Compose en T-010.
  - Verificación:
    ```bash
    cd frontend
    npm run typecheck
    npm run build
    grep -R "localhost:8000" src || true
    ```

- [ ] **T-008 — Implementar la pantalla inicial y sus pruebas**
  - Requisitos: FR-006, FR-009, NFR-005.
  - Dependencias: T-007.
  - Descripción: crear `App.tsx` y `ApiStatus.tsx`; consultar `/api/health` al montar; manejar carga, disponible y no disponible; cancelar la actualización al desmontar. Probar título, carga, éxito y fallo con `fetch` simulado.
  - Hecho cuando: las pruebas de componente pasan y la interfaz no se rompe cuando la API falla.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [ ] **T-009 — Crear el Dockerfile de la API y el contexto de build**
  - Requisitos: FR-007, NFR-001, NFR-002.
  - Dependencias: T-004.
  - Descripción: crear `docker/Dockerfile.api` con `uv`, `uv sync --frozen`, `UV_PROJECT_ENVIRONMENT=/opt/venv` y Uvicorn. Crear `.dockerignore` excluyendo `legacy/`, `.env`, cachés, entornos virtuales y dependencias del frontend.
  - Hecho cuando: la imagen construye y el módulo `app.main` importa dentro del contenedor con una URL ficticia.
  - Verificación:
    ```bash
    docker build -f docker/Dockerfile.api -t py-personal-finance-api:dev .
    docker run --rm \
      -e DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/personal_finance \
      py-personal-finance-api:dev python -c "from app.main import app; print(app.title)"
    ```

- [ ] **T-010 — Crear Docker Compose de desarrollo**
  - Requisitos: FR-001, FR-007, NFR-001, NFR-002, NFR-009.
  - Dependencias: T-005, T-008, T-009.
  - Descripción: crear `compose.yaml` con `db`, `api` y `web`; healthchecks; volúmenes persistentes; montajes de desarrollo; `depends_on`; puertos enlazados a `127.0.0.1`; proxy de Vite hacia `api:8000`. Crear `.env.example` y actualizar `.gitignore`.
  - Hecho cuando: `docker compose up --build` deja los tres servicios activos, la API responde `200` en salud y la web carga.
  - Verificación:
    ```bash
    docker compose config -q
    docker compose up --build -d
    docker compose ps
    curl -i http://localhost:8000/api/health
    curl -I http://localhost:3001/
    ```

- [ ] **T-011 — Documentar el arranque y alinear AGENTS**
  - Requisitos: FR-010, FR-011, NFR-001.
  - Dependencias: T-010.
  - Descripción: crear `README.md` con requisitos, arranque, URLs, desarrollo local, pruebas, migraciones y solución de problemas. Actualizar `AGENTS.md` con la segunda confirmación de seguridad indicada en la constitución y verificar que sus comandos coinciden con los scripts reales.
  - Hecho cuando: una persona puede seguir el README desde un clon limpio y todos los comandos documentados existen.
  - Verificación:
    ```bash
    docker compose config -q
    cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .
    cd ../frontend && npm run lint && npm run typecheck && npm run test && npm run build
    ```

- [ ] **T-012 — Validar la Fase 0 y registrar evidencia**
  - Requisitos: todos los criterios de aceptación de `spec.md`.
  - Dependencias: T-011.
  - Descripción: ejecutar la verificación completa, probar el estado degradado deteniendo PostgreSQL, ejecutar upgrade/downgrade/upgrade de Alembic, confirmar que solo existe `alembic_version`, revisar puertos y secretos, y registrar los resultados en este archivo.
  - Hecho cuando: todos los criterios de aceptación tienen evidencia y cualquier fallo queda documentado.
  - Verificación:
    ```bash
    docker compose up --build -d
    curl -i http://localhost:8000/api/health
    docker compose stop db
    curl -i http://localhost:8000/api/health
    docker compose start db
    docker compose exec api uv run alembic upgrade head
    docker compose exec api uv run alembic downgrade base
    docker compose exec api uv run alembic upgrade head
    docker compose exec db psql -U postgres -d personal_finance -c "\dt"
    docker compose ps
    docker compose logs api
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-001, T-006, T-009, T-010 |
| FR-002 | T-004, T-012 |
| FR-003 | T-002 |
| FR-004 | T-003, T-004 |
| FR-005 | T-005, T-012 |
| FR-006 | T-007, T-008 |
| FR-007 | T-009, T-010 |
| FR-008 | T-004 |
| FR-009 | T-006, T-008 |
| FR-010 | T-001, T-006, T-011 |
| FR-011 | T-011, T-012 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-009, T-010, T-011, T-012 |
| NFR-002 | T-002, T-009, T-010, T-012 |
| NFR-003 | T-003, T-007 |
| NFR-004 | T-001, T-006 |
| NFR-005 | T-008 |
| NFR-006 | T-004, T-012 |
| NFR-007 | T-002, T-004, T-008 |
| NFR-008 | T-001, T-006 |
| NFR-009 | T-010, T-011 |

## Evidencia de validación

Se completa durante T-012.

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Pendiente | |
| AC-002 | Pendiente | |
| AC-003 | Pendiente | |
| AC-004 | Pendiente | |
| AC-005 | Pendiente | |
| AC-006 | Pendiente | |
| AC-007 | Pendiente | |
| AC-008 | Pendiente | |
| AC-009 | Pendiente | |
| AC-010 | Pendiente | |
| AC-011 | Pendiente | |
| AC-012 | Pendiente | |

## Notas

- No se ejecuta `docker compose down -v` sin autorización explícita.
- No se implementa ninguna tarea de las especificaciones 002 a 006 en esta fase.
- Si una tarea revela una decisión no prevista, se actualiza primero `plan.md` o `spec.md` según corresponda.
