# Plan técnico 001 — Fundaciones del proyecto

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Fase: 0.
- Iteración: MVP.

## 1. Resumen de la solución

La Fase 0 construye un monorepositorio reproducible con tres servicios orquestados por Docker Compose: PostgreSQL, una API FastAPI y una interfaz React servida por Vite en desarrollo.

El backend incluye configuración por entorno, sesión SQLAlchemy, un endpoint operativo `/api/health` y Alembic con una revisión base vacía. El frontend incluye una pantalla inicial que consulta ese endpoint a través del proxy `/api`. Las pruebas unitarias de ambos lados se ejecutan sin depender de PostgreSQL.

No se crean tablas ni funcionalidad financiera. El único objeto de base de datos es la tabla de versiones de Alembic.

## 2. Arquitectura y flujo de datos

```text
Navegador
   │
   │  http://localhost:3001
   ▼
Vite dev server (contenedor web)
   │
   │  proxy /api → http://api:8000
   ▼
FastAPI (contenedor api)
   │
   │  SQLAlchemy + psycopg
   ▼
PostgreSQL 16 (contenedor db)
```

Flujo de salud:

1. El navegador carga la SPA desde Vite.
2. `App` solicita `/api/health` mediante `fetch`.
3. Vite redirige la petición a la API.
4. La API ejecuta `SELECT 1` en una sesión SQLAlchemy.
5. La API responde `200` si la conexión funciona o `503` si falla.
6. La interfaz muestra `API disponible` o `API no disponible`.

En la especificación 006 se sustituirá Vite por Nginx para el despliegue final, manteniendo el mismo contrato `/api`.

## 3. Componentes y responsabilidades

### Backend

| Ruta | Responsabilidad |
|---|---|
| `backend/app/main.py` | Crear la aplicación FastAPI y registrar el router de salud bajo `/api`. |
| `backend/app/core/config.py` | Leer `DATABASE_URL`, validar su presencia y exponer una configuración inmutable. |
| `backend/app/db/base.py` | Declarar `Base` para los futuros modelos SQLAlchemy. |
| `backend/app/db/session.py` | Crear el motor, la fábrica de sesiones y la dependencia `get_db`. |
| `backend/app/api/schemas/health.py` | Modelo Pydantic de respuesta de salud. |
| `backend/app/api/routes/health.py` | Endpoint `/health`, comprobación de base de datos y respuesta `503`. |
| `backend/tests/conftest.py` | Configurar el entorno de pruebas y el cliente de FastAPI. |
| `backend/tests/core/test_config.py` | Probar configuración válida y ausencia de `DATABASE_URL`. |
| `backend/tests/api/test_health.py` | Probar respuestas `200` y `503` mediante sustitución de `get_db`. |
| `backend/alembic/env.py` | Conectar Alembic con `DATABASE_URL` y `Base.metadata`. |
| `backend/alembic/versions/0001_baseline.py` | Revisión base sin operaciones de esquema. |
| `backend/alembic.ini` | Configuración de Alembic. |
| `backend/pyproject.toml` | Dependencias, ruff y configuración de pytest. |

### Frontend

| Ruta | Responsabilidad |
|---|---|
| `frontend/vite.config.ts` | Plugins, proxy `/api` y configuración de Vitest. |
| `frontend/src/api/client.ts` | Cliente `fetch` mínimo con manejo uniforme de errores. |
| `frontend/src/api/health.ts` | Función `getHealth` sobre el cliente. |
| `frontend/src/types/health.ts` | Tipos del contrato de salud. |
| `frontend/src/components/ApiStatus.tsx` | Presentación accesible del estado de la API. |
| `frontend/src/App.tsx` | Composición de la pantalla y ciclo de consulta. |
| `frontend/src/test/setup.ts` | Configuración de Testing Library y jest-dom. |
| `frontend/src/App.test.tsx` | Pruebas de renderizado y estados disponible/no disponible. |

### Infraestructura y documentación

| Ruta | Responsabilidad |
|---|---|
| `docker/Dockerfile.api` | Imagen de desarrollo de la API con `uv` y entorno virtual en `/opt/venv`. |
| `compose.yaml` | Servicios `db`, `api` y `web`, healthchecks, volúmenes y puertos. |
| `.env.example` | Variables de Compose y URL para desarrollo local. |
| `.dockerignore` | Excluir `legacy/`, dependencias, cachés y secretos del contexto de build. |
| `.gitignore` | Ignorar entornos virtuales, dependencias, artefactos y `.env`. |
| `README.md` | Arranque, URLs, pruebas, migraciones y solución de problemas. |

## 4. Decisiones técnicas

### 4.1 Stack y versiones

- Python 3.13 sobre `python:3.13-slim`.
- FastAPI con Pydantic v2.
- SQLAlchemy 2 en modo síncrono.
- `psycopg[binary]` 3 como driver PostgreSQL.
- Alembic para migraciones.
- PostgreSQL 16 sobre Alpine.
- React + TypeScript + Vite sobre Node 20.
- Vitest + Testing Library para pruebas de interfaz.
- ruff para lint y formato del backend.
- ESLint y TypeScript estricto para el frontend.

Las versiones exactas se resuelven con `uv.lock` y `package-lock.json`, que se versionan.

### 4.2 Configuración

`app/core/config.py` expone:

- `Settings`: contenedor inmutable con `database_url`.
- `load_settings(env)`: función pura y testeable que lee `DATABASE_URL`.
- `get_settings()`: variante con caché para uso en la aplicación.

Si `DATABASE_URL` falta o está vacía, se lanza `RuntimeError` con un mensaje que nombra la variable, sin incluir su valor. El fallo ocurre al importar la configuración o al iniciar la aplicación.

No se añade `pydantic-settings` porque solo existe una variable en esta fase y la biblioteca estándar cubre la necesidad.

### 4.3 Persistencia

`app/db/session.py` crea el motor con:

- `pool_pre_ping=True` para descartar conexiones inválidas.
- `connect_args={"connect_timeout": 3}` para acotar la espera cuando PostgreSQL no responde.
- `SessionLocal` con `autocommit=False` y `autoflush=False`.

`get_db` entrega una sesión por petición y la cierra en `finally`.

`Base` se declara en `app/db/base.py` aunque todavía no tenga modelos. No se ejecuta `Base.metadata.create_all()` en ningún punto.

### 4.4 Endpoint de salud

`GET /api/health` usa `get_db` y ejecuta `text("SELECT 1")`.

- Éxito: `200` con `HealthResponse(status="ok", database="ok")`.
- Error de SQLAlchemy: `503` con `{"status": "degraded", "database": "unavailable"}`.
- El error se registra como advertencia sin cadena de conexión ni credenciales.
- La ruta declara el modelo de respuesta y la respuesta `503` en OpenAPI.

El endpoint es operativo. Sus claves `status` y `database` permanecen en inglés y no forman parte del contrato de dominio en español.

### 4.5 Proxy y CORS

El frontend usa rutas relativas bajo `/api`. Vite redirige `/api` a `VITE_API_PROXY_TARGET`, con valor por defecto `http://localhost:8000` y valor `http://api:8000` dentro de Compose.

No se habilita CORS. Navegador, proxy y API comparten origen desde la perspectiva del navegador.

### 4.6 Docker de desarrollo

`Dockerfile.api`:

- Usa `uv` copiado desde la imagen oficial.
- Instala dependencias con `uv sync --frozen`.
- Define `UV_PROJECT_ENVIRONMENT=/opt/venv` para que el entorno virtual no quede dentro de `/app`, que se monta como volumen.
- Ejecuta Uvicorn con `uv run --frozen`.

`compose.yaml`:

- `db`: PostgreSQL 16, volumen persistente y healthcheck con `pg_isready`.
- `api`: build desde la raíz, montaje de `backend/` para recarga, healthcheck HTTP con la biblioteca estándar de Python.
- `web`: `node:20-alpine`, montaje de `frontend/`, volumen para `node_modules` y Vite con `--host 0.0.0.0`.
- Todos los puertos publicados se enlazan a `127.0.0.1`.
- `api` depende de `db` saludable; `web` depende de `api` saludable.
- El healthcheck de `web` incluye un periodo de gracia para la instalación inicial de dependencias.

El servicio `web` de esta fase es de desarrollo. Nginx, una imagen estática y el endurecimiento de contenedores pertenecen a la especificación 006.

### 4.7 Migraciones

`alembic.ini` no contiene una URL fija. `env.py` obtiene la URL desde `get_settings()` y escapa `%` antes de pasarla a la configuración de Alembic para evitar errores de interpolación.

`target_metadata = Base.metadata` queda preparado para futuras migraciones autogeneradas. La revisión `0001_baseline` no crea tablas: su `upgrade` y `downgrade` son no-ops. Aplicarla crea únicamente `alembic_version`.

### 4.8 Pruebas

- Backend: pytest con `TestClient` y sustitución de `get_db`. Las pruebas de salud no necesitan PostgreSQL.
- Configuración: prueba de `load_settings({})` y de un entorno válido.
- Frontend: Vitest con jsdom, Testing Library y `fetch` sustituido. No se usa MSW.
- La integración real con PostgreSQL se verifica con Compose y los comandos de Alembic, no con pruebas unitarias.

### 4.9 Alternativas descartadas

| Alternativa | Motivo para descartarla |
|---|---|
| SQLAlchemy async | Añade complejidad de sesiones y drivers sin necesidad en el MVP. |
| `pydantic-settings` | Una sola variable no justifica otra dependencia. |
| Axios | `fetch` cubre el cliente mínimo sin dependencias. |
| Router o estado global en React | La pantalla única no los necesita. |
| Nginx y contenedores no root en esta fase | Se abordan en la especificación de entrega para no duplicar trabajo. |
| SQLite en pruebas | No reproduce los tipos y restricciones de PostgreSQL que se usarán después. |

## 5. Contrato de API

### `GET /api/health`

Sin autenticación. No recibe parámetros.

Respuesta `200`:

```json
{
  "status": "ok",
  "database": "ok"
}
```

Respuesta `503`:

```json
{
  "status": "degraded",
  "database": "unavailable"
}
```

Reglas:

- No se devuelven detalles de la excepción, credenciales ni la URL de conexión.
- El tiempo de espera de conexión está acotado a 3 segundos.
- La documentación OpenAPI queda disponible en `/docs`.

## 6. Modelo de datos y migraciones

No se crean tablas de dominio en esta iteración.

| Objeto | Cambio |
|---|---|
| `alembic_version` | Creada por Alembic al aplicar la revisión base. |
| `ingresos` | No existe todavía; se crea en 002. |
| `gastos` | No existe todavía; se crea en 003. |

La revisión `0001_baseline` debe poder aplicarse y revertirse sin efectos sobre datos. Las migraciones posteriores serán la única vía para incorporar el esquema financiero.

## 7. Manejo de errores y consistencia

- **`DATABASE_URL` ausente:** error de configuración al iniciar; el contenedor no arranca y el mensaje no expone secretos.
- **PostgreSQL caído:** la API permanece en ejecución y `/api/health` responde `503`.
- **Fallo de migración:** el comando Alembic termina con código distinto de cero; la revisión base no modifica datos.
- **Frontend sin API:** la interfaz muestra `API no disponible`; no se produce una pantalla en blanco ni una promesa rechazada sin manejar.
- **Petición de salud cancelada:** el componente evita actualizar estado después de desmontarse.
- **Sesión de base de datos:** se cierra siempre mediante `get_db`; no hay escrituras ni transacciones de dominio en esta fase.
- **Reintentos:** no se implementan en la aplicación; los healthchecks y `depends_on` cubren el arranque de Compose.

## 8. Seguridad y límites de confianza

- La aplicación es local y no tiene autenticación; no debe exponerse a Internet.
- Todos los puertos publicados se enlazan a `127.0.0.1`.
- `.env` está ignorado y `.env.example` solo contiene valores de desarrollo.
- No se habilita CORS.
- Los logs no incluyen secretos, cadenas de conexión completas ni datos financieros.
- La imagen de desarrollo ejecuta como root para simplificar los montajes; el endurecimiento y el usuario no root se abordan en 006.
- El contexto de build excluye `legacy/` y archivos locales mediante `.dockerignore`.

## 9. Observabilidad

- Uvicorn escribe logs de acceso y errores en stdout.
- El fallo de salud registra una advertencia sin detalles sensibles.
- `/api/health` es la señal operativa usada por Docker Compose.
- No se añaden métricas, trazas, alertas ni servicios externos.

## 10. Estrategia de pruebas

### Backend

| Caso | Tipo | Evidencia |
|---|---|---|
| Configuración válida | Unitaria | `test_config.py` |
| `DATABASE_URL` ausente | Unitaria | `test_config.py` |
| Salud con base disponible | Unitaria con override | `test_health.py` |
| Salud con base no disponible | Unitaria con override | `test_health.py` |
| Forma de la respuesta | Unitaria | `test_health.py` |

Comandos:

```bash
cd backend
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

### Frontend

| Caso | Tipo | Evidencia |
|---|---|---|
| Renderizado del título y mensaje inicial | Componente | `App.test.tsx` |
| API disponible | Componente con `fetch` simulado | `App.test.tsx` |
| API no disponible | Componente con `fetch` simulado | `App.test.tsx` |
| Estado de carga | Componente | `App.test.tsx` |

Comandos:

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

### Integración manual

```bash
docker compose up --build
curl -i http://localhost:8000/api/health
docker compose stop db
curl -i http://localhost:8000/api/health
docker compose start db
docker compose exec api uv run alembic upgrade head
docker compose exec api uv run alembic downgrade base
docker compose exec api uv run alembic upgrade head
```

No se incorporan pruebas end-to-end con navegador en esta fase.

## 11. Despliegue y reversibilidad

- `docker compose up --build` es el flujo principal de desarrollo.
- `docker compose down` conserva el volumen de PostgreSQL.
- `docker compose down -v` no forma parte del flujo normal y requiere autorización.
- `alembic downgrade base` revierte la revisión base sin tocar datos de dominio.
- Los puertos se cambian mediante `API_PORT`, `WEB_PORT` y `DB_PORT`.
- `uv.lock` y `package-lock.json` garantizan instalaciones reproducibles.

## 12. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| El montaje de `backend/` oculta el entorno virtual de la imagen. | `UV_PROJECT_ENVIRONMENT=/opt/venv`. |
| `npm install` en cada arranque ralentiza el servicio web. | Volumen nombrado para `node_modules`; instalación inicial documentada. |
| El proxy de Vite apunta a un host incorrecto dentro de Docker. | `VITE_API_PROXY_TARGET=http://api:8000` en Compose. |
| Un puerto local está ocupado. | Variables `API_PORT`, `WEB_PORT` y `DB_PORT`. |
| `DATABASE_URL` contiene `%` y rompe la interpolación de Alembic. | Escapar `%` antes de `set_main_option`. |
| El healthcheck marca la API como no saludable cuando PostgreSQL cae. | Comportamiento esperado; se documenta como estado degradado. |
| Las pruebas importan la aplicación antes de definir el entorno. | `conftest.py` define `DATABASE_URL` antes de importar módulos de la aplicación. |
| El contexto de build incluye `legacy/` o dependencias locales. | `.dockerignore` explícito. |
| Vite requiere una versión de Node superior a la disponible. | Fijar una versión compatible con Node 20.19 y verificar `npm run build`. |
| Las claves de salud en inglés contradicen el contrato en español. | Se documentan como excepción operativa fuera del dominio. |

## 13. Trazabilidad requisitos → plan

| Requisito | Sección del plan | Tareas |
|---|---|---|
| FR-001 | 3, 4.6, 11 | T-001, T-006, T-009, T-010 |
| FR-002 | 4.4, 5, 7 | T-004, T-012 |
| FR-003 | 4.2, 7 | T-002 |
| FR-004 | 4.3, 6 | T-003, T-004 |
| FR-005 | 4.7, 6 | T-005, T-012 |
| FR-006 | 4.5, 3 | T-007, T-008 |
| FR-007 | 4.6, 11 | T-009, T-010 |
| FR-008 | 4.8, 10 | T-004 |
| FR-009 | 4.8, 10 | T-006, T-008 |
| FR-010 | 4.1, 10 | T-001, T-006, T-011 |
| FR-011 | 3, 11 | T-011, T-012 |

La cobertura de requisitos no funcionales se detalla en `tasks.md`.

## 14. Aprobación y siguiente paso

Este plan fue aprobado junto con `tasks.md`.

La implementación comienza por `T-001` y avanza en el orden de dependencias definido en `tasks.md`.
