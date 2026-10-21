# AGENTS.md

Instrucciones operativas para trabajar en este repositorio.

## 1. Resumen del proyecto

Py Personal Finance registra ingresos y gastos personales, clasifica los gastos como necesarios, no necesarios o inversiones y calcula totales. El MVP es local, de un solo usuario y sin autenticación.

Stack:

- Backend: Python 3.13, FastAPI, SQLAlchemy 2 (síncrono), Pydantic v2, Alembic.
- Base de datos: PostgreSQL 16.
- Frontend: React, TypeScript, Vite.
- Infraestructura: Docker y Docker Compose.
- Pruebas: pytest (backend), Vitest + Testing Library (frontend).
- Calidad backend: ruff. Calidad frontend: ESLint + TypeScript.

`legacy/` contiene una implementación anterior. Está fuera de alcance: no se modifica, no se importa y no se usa como base de código.

## 2. Estado actual

El repositorio comienza desde cero. La implementación se inicia con `specs/001-fundaciones/`. Los comandos de este documento son el contrato operativo que esa especificación debe materializar; si un comando no existe todavía, la fase correspondiente no está terminada.

## 3. Estructura objetivo

```text
project-root/
├── AGENTS.md
├── constitution.md
├── README.md
├── compose.yaml
├── .env.example
├── specs/
│   └── 001-fundaciones/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── schemas/
│   │   ├── core/
│   │   ├── db/
│   │   │   └── models/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── types/
│   ├── package.json
│   └── package-lock.json
└── docker/
    ├── Dockerfile.api
    ├── Dockerfile.web
    └── nginx.conf
```

No se crean carpetas vacías ni capas adicionales sin necesidad.

## 4. Entorno verificado

- Python 3.13.5 disponible mediante `python3`.
- `uv` 0.11.21 disponible.
- Node.js 20.19.2 y npm 9.2.0 disponibles.
- Docker 29.8.1 y Docker Compose v5.5.1 disponibles.

## 5. Comandos canónicos

### Backend (desde `backend/`)

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic revision --autogenerate -m "describe change"
```

### Frontend (desde `frontend/`)

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm run test
npm run build
```

### Docker Compose (desde la raíz)

```bash
docker compose up --build
docker compose down
docker compose logs -f
docker compose exec api uv run alembic upgrade head
docker compose exec db psql -U postgres -d personal_finance
```

### Verificación mínima antes de terminar una tarea

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest
cd frontend && npm run lint && npm run typecheck && npm run test && npm run build
```

No se declara una tarea terminada si alguno de estos comandos falla y el fallo está relacionado con el cambio.

## 6. Convenciones

- Contrato externo en español: rutas (`/api/ingresos`, `/api/gastos`, `/api/resumen`), campos JSON (`fecha`, `descripcion`, `valor`, `tipo`), tablas y columnas.
- Código interno en inglés: clases, funciones, variables, componentes y nombres de pruebas.
- Los DTO de frontera conservan los nombres del contrato en español. Los modelos SQLAlchemy usan atributos en inglés con el nombre de columna explícito.
- Los importes usan `Decimal`/`NUMERIC`; nunca `float`.
- Las fechas usan ISO 8601.
- Las migraciones son la única vía para modificar el esquema. No usar `Base.metadata.create_all()`.
- El frontend consume `/api` mediante proxy de mismo origen; no se habilita CORS salvo necesidad justificada.
- No se añaden dependencias sin justificarlas en el plan de la funcionalidad.
- No se añaden comentarios al código salvo que aporten contexto que el código no exprese.

## 7. Flujo de trabajo SDD

Para cada funcionalidad:

1. Leer `constitution.md`, este archivo y la especificación correspondiente.
2. Revisar `spec.md` y resolver ambigüedades antes de planificar.
3. Crear `plan.md` y obtener aprobación.
4. Crear `tasks.md` con tareas pequeñas, dependencias y resultado verificable.
5. Implementar una tarea o un grupo pequeño de tareas relacionadas.
6. Ejecutar las pruebas y verificaciones aplicables.
7. Revisar el diff antes de continuar.
8. Validar los requisitos con evidencia y mantener la trazabilidad.

Cada especificación vive en `specs/NNN-nombre-funcionalidad/`.

## 8. Límites y acciones que requieren confirmación

- No modificar, mover ni eliminar `legacy/`.
- No hacer commits, push, PRs ni despliegues sin solicitud explícita.
- No ejecutar migraciones destructivas, borrar volúmenes ni reiniciar bases de datos con datos sin autorización.
- No exponer la aplicación a Internet ni añadir autenticación fuera de una especificación aprobada.
- No introducir servicios, infraestructura o dependencias nuevas sin justificación y aprobación.
- No registrar secretos ni datos financieros identificables.
- No cambiar el alcance para evitar un requisito difícil.

## 9. Definición de terminado

Una tarea está terminada cuando:

- Cumple sus criterios verificables y los requisitos asociados.
- Las pruebas y comprobaciones aplicables se ejecutaron y pasaron.
- La documentación afectada está actualizada.
- El diff no contiene secretos, cambios ajenos al alcance ni complejidad innecesaria.
- `tasks.md` refleja el estado real.
