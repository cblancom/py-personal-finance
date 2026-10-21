# Especificación 001 — Fundaciones del proyecto

- Estado: validada.
- Fase: 0.
- Iteración: MVP.
- Dependencias: `constitution.md`, `AGENTS.md`.
- Plan: `plan.md` (aprobado).
- Tareas: `tasks.md` (aprobadas).

## 1. Contexto y problema

El proyecto parte de un repositorio sin implementación. Antes de construir el registro de ingresos y gastos se necesita un entorno reproducible que permita desarrollar, probar y ejecutar la aplicación completa, además de un contrato operativo claro para las siguientes especificaciones.

Sin esta base, cada funcionalidad posterior tendría que resolver por su cuenta la configuración, la conexión a PostgreSQL, las migraciones, el proxy hacia la API y las herramientas de prueba, lo que aumentaría el riesgo de inconsistencias y trabajo duplicado.

Esta iteración construye únicamente los cimientos técnicos. No incluye tablas ni funcionalidad financiera.

## 2. Usuarios y actores

- **Desarrollador propietario:** persona que clona el repositorio, ejecuta la aplicación y mantiene las migraciones.
- **Agente de implementación:** agente que trabaja siguiendo `constitution.md`, `AGENTS.md` y las especificaciones aprobadas.
- **Usuario final:** no participa todavía en un flujo funcional; solo observa la pantalla inicial y el estado de la API.

No existen roles, permisos ni autenticación en esta iteración.

## 3. Historias de usuario y flujos

### US-001 — Arranque reproducible

Como desarrollador, quiero ejecutar `docker compose up --build` en un entorno limpio para obtener PostgreSQL, la API y la interfaz disponibles sin pasos manuales ocultos.

**Flujo esperado:**

1. Existe un `.env.example` con las variables necesarias.
2. Docker Compose construye y levanta los tres servicios.
3. PostgreSQL queda saludable antes de iniciar la API.
4. La API responde en `/api/health`.
5. La interfaz carga en el navegador y muestra el estado de la API.

### US-002 — Verificación local

Como desarrollador, quiero ejecutar las pruebas y comprobaciones de calidad con comandos documentados para saber si el repositorio está en buen estado.

**Flujo esperado:**

1. `uv run pytest` ejecuta las pruebas del backend.
2. `npm run test` ejecuta las pruebas del frontend.
3. `ruff`, ESLint y TypeScript verifican el código.
4. Los comandos documentados coinciden con los archivos de configuración reales.

### US-003 — Evolución del esquema

Como desarrollador, quiero crear y aplicar migraciones Alembic de forma controlada para que el esquema evolucione sin recrear la base de datos.

**Flujo esperado:**

1. Alembic lee la URL de conexión desde el entorno.
2. `alembic upgrade head` aplica la revisión base.
3. `alembic downgrade base` revierte la revisión.
4. No existe código que cree tablas fuera de Alembic.

### US-004 — Estado visible de la API

Como usuario, quiero ver en la pantalla inicial si el backend está disponible para distinguir un problema de infraestructura de un problema de la interfaz.

**Flujo esperado:**

1. La interfaz consulta `/api/health`.
2. Si la API responde correctamente, muestra un estado disponible.
3. Si la API no responde o reporta un problema, muestra un estado no disponible sin romper la página.

## 4. Requisitos funcionales

### FR-001 — Estructura del repositorio

El repositorio debe contener las carpetas `backend/`, `frontend/`, `docker/` y `specs/`, además de `constitution.md`, `AGENTS.md`, `README.md`, `compose.yaml` y `.env.example`.

- `backend/` agrupa la aplicación FastAPI, Alembic, las pruebas y los archivos de dependencias.
- `frontend/` agrupa la aplicación React, sus pruebas y los archivos de dependencias.
- `docker/` contiene los artefactos de infraestructura. En esta iteración se crea `Dockerfile.api`; `Dockerfile.web` y `nginx.conf` se incorporan en la especificación 006.
- `specs/` contiene las especificaciones SDD.
- `legacy/` no se modifica ni se referencia.

**Verificación:** el árbol de directorios coincide con el acordado y no hay carpetas vacías sin propósito.

### FR-002 — Aplicación backend y endpoint de salud

El backend debe iniciar con FastAPI y exponer `GET /api/health`.

Cuando PostgreSQL esté disponible, debe responder `200` con cuerpo JSON:

```json
{
  "status": "ok",
  "database": "ok"
}
```

Cuando PostgreSQL no esté disponible, debe responder `503` con cuerpo JSON:

```json
{
  "status": "degraded",
  "database": "unavailable"
}
```

La respuesta no debe incluir credenciales, trazas internas ni detalles de conexión. La comprobación debe tener un timeout acotado para no bloquear indefinidamente.

Este endpoint es operativo: sus claves permanecen en inglés y no forman parte del contrato de dominio en español.

**Verificación:** ambos escenarios se comprueban con la API en ejecución y con la base detenida.

### FR-003 — Configuración por variables de entorno

El backend debe leer `DATABASE_URL` desde el entorno. Si falta o está vacía, debe fallar al iniciar con un mensaje claro que no exponga secretos.

Los valores por defecto para desarrollo local deben estar documentados en `.env.example`. Los secretos reales no se versionan.

**Verificación:** iniciar la API sin `DATABASE_URL` produce un error comprensible; con la variable definida, inicia correctamente.

### FR-004 — Fundaciones de persistencia

El backend debe proporcionar:

- Un motor SQLAlchemy creado a partir de `DATABASE_URL`.
- Una fábrica de sesiones reutilizable.
- Una dependencia de FastAPI que entregue una sesión por petición y la cierre al finalizar.
- Una función de comprobación de conectividad usada por el endpoint de salud.

No debe existir ninguna llamada a `Base.metadata.create_all()` ni creación implícita de tablas.

**Verificación:** la API usa la sesión inyectada y la comprobación de salud refleja el estado real de PostgreSQL.

### FR-005 — Alembic inicializado

Alembic debe estar configurado para leer `DATABASE_URL` desde el entorno y operar sobre la base de datos de la aplicación.

Debe existir una revisión base que no cree tablas de dominio y que pueda aplicarse y revertirse:

- `alembic upgrade head` debe completar sin errores sobre una base vacía.
- `alembic downgrade base` debe revertir la revisión.
- Ejecutar `alembic upgrade head` dos veces debe ser seguro.

La tabla de versiones de Alembic es la única estructura creada en esta iteración.

**Verificación:** se ejecutan upgrade, downgrade y upgrade de nuevo sobre una base limpia.

### FR-006 — Shell del frontend

La aplicación React debe renderizar una pantalla inicial en español que incluya:

- El nombre del proyecto.
- Un mensaje que indique que la interfaz está en construcción.
- El estado de la API obtenido desde `/api/health`.

La consulta debe realizarse mediante el cliente HTTP del frontend y a través de `/api`, sin URL absoluta hardcodeada en los componentes. La interfaz debe manejar los estados de carga, disponible y no disponible.

**Verificación:** con la API encendida se muestra disponible; con la API apagada se muestra no disponible y la página sigue renderizando.

### FR-007 — Docker Compose de desarrollo

`compose.yaml` debe definir tres servicios:

- `db`: PostgreSQL con volumen persistente y healthcheck.
- `api`: backend con recarga automática y dependencia de `db` saludable.
- `web`: frontend con servidor de desarrollo Vite y dependencia de `api`.

El entorno debe permitir editar código local sin reconstruir las imágenes. Los puertos deben ser configurables mediante variables de entorno. La base de datos solo debe publicarse en `127.0.0.1`.

`docker compose up --build` debe funcionar desde un entorno limpio con los valores de `.env.example`.

**Verificación:** los tres servicios quedan en ejecución, `db` y `api` reportan salud, y la web responde.

### FR-008 — Arnes de pruebas del backend

El backend debe incluir pytest y una estructura de pruebas que permita ejecutar `uv run pytest` sin depender de que la base de datos esté levantada para las pruebas unitarias.

Debe existir al menos una prueba del comportamiento de `/api/health` para los estados disponible y no disponible, usando sustitución de dependencias o dobles de prueba.

**Verificación:** `uv run pytest` pasa en un entorno sin PostgreSQL.

### FR-009 — Arnes de pruebas del frontend

El frontend debe incluir Vitest y Testing Library con al menos una prueba de renderizado de la pantalla inicial y una prueba del estado mostrado cuando la API no está disponible.

**Verificación:** `npm run test` pasa.

### FR-010 — Herramientas de calidad

El backend debe usar ruff para lint y formato, con configuración versionada.

El frontend debe usar ESLint y TypeScript en modo estricto, con los scripts `lint`, `typecheck`, `test` y `build`.

**Verificación:** todos los comandos de `AGENTS.md` existen y pasan.

### FR-011 — Documentación operativa

`README.md` debe explicar el arranque con Docker Compose, el desarrollo local, las variables de entorno, las migraciones y las pruebas.

`AGENTS.md` debe contener comandos que coincidan con la configuración real del repositorio.

**Verificación:** una persona puede seguir el README desde un clon limpio sin consultar otros documentos.

## 5. Requisitos no funcionales

### NFR-001 — Reproducibilidad

La aplicación completa debe levantarse desde un clon limpio con Docker y Docker Compose, sin requerir Python ni Node instalados en el host para el flujo principal.

### NFR-002 — Seguridad y secretos

No debe existir ningún secreto versionado. `.env` debe estar ignorado por Git y `.env.example` debe contener únicamente valores de desarrollo no sensibles.

### NFR-003 — Coherencia de nombres

Las rutas y los campos expuestos deben usar español. Los identificadores internos del backend y frontend deben usar inglés. Los nombres de tablas y columnas serán en español cuando existan en iteraciones posteriores.

### NFR-004 — Mantenibilidad

La base debe evitar duplicación de configuración y capas innecesarias. Cada módulo debe tener una responsabilidad clara y un tamaño proporcional al MVP.

### NFR-005 — Accesibilidad básica

La pantalla inicial debe usar HTML semántico, textos legibles, contraste suficiente y un estado de error comprensible sin depender únicamente del color.

### NFR-006 — Observabilidad segura

Los servicios deben registrar eventos en stdout. Los logs no deben contener contraseñas, cadenas de conexión completas ni datos sensibles.

### NFR-007 — Pruebas deterministas

Las pruebas unitarias no deben depender de servicios externos, del orden de ejecución ni de datos persistentes.

### NFR-008 — Dependencias bloqueadas

`backend/uv.lock` y `frontend/package-lock.json` deben versionarse para fijar las dependencias resueltas.

### NFR-009 — Compatibilidad

La base debe funcionar en Linux y macOS con Docker. El flujo no debe depender de rutas absolutas del host.

## 6. Reglas de negocio

- **BR-001:** el MVP es de un solo usuario, local y sin autenticación.
- **BR-002:** el contrato externo se expresa en español y el código interno en inglés.
- **BR-003:** los importes futuros usarán `Decimal`/`NUMERIC`; queda prohibido `float`. Esta regla aplica aunque todavía no existan tablas de movimientos.
- **BR-004:** el esquema se modifica exclusivamente mediante migraciones Alembic.
- **BR-005:** `legacy/` está fuera de alcance y no se reutiliza.
- **BR-006:** esta iteración no incluye funcionalidad financiera, autenticación, vista mensual, Nginx de producción ni CI/CD.
- **BR-007:** la API no habilita CORS; el frontend accede por `/api` mediante proxy de mismo origen.

## 7. Casos límite y errores

- **Base de datos caída:** la API debe seguir en ejecución y reportar `503` en `/api/health` sin exponer detalles internos.
- **Variable `DATABASE_URL` ausente:** el backend debe fallar al iniciar con un mensaje claro.
- **Puerto ocupado:** debe poder resolverse cambiando una variable de entorno sin modificar código.
- **Frontend sin backend:** la pantalla inicial debe mostrar el estado no disponible y no lanzar una pantalla en blanco.
- **Migración ejecutada dos veces:** `alembic upgrade head` debe ser seguro e idempotente.
- **Base vacía:** `alembic upgrade head` y `alembic downgrade base` deben funcionar sobre una base recién creada.
- **Volumen existente:** `docker compose down` no debe eliminar datos; solo `down -v` lo haría y no forma parte del flujo normal.
- **Dependencias no instaladas:** el mensaje de error debe indicar el comando de instalación correspondiente.

## 8. Fuera de alcance

- Tablas `ingresos` y `gastos`.
- Modelos SQLAlchemy de dominio.
- Endpoints de ingresos, gastos, resumen, edición o eliminación.
- Formularios, listados y tarjetas de totales.
- Vista o filtro mensual.
- Autenticación, multiusuario y permisos.
- Datos de ejemplo o carga inicial.
- Nginx, TLS y configuración de producción.
- CI/CD, backups, métricas, trazas y alertas.
- Soporte de múltiples monedas.
- Pruebas end-to-end con navegador.

## 9. Criterios de aceptación verificables

| ID | Criterio | Evidencia |
|---|---|---|
| AC-001 | La estructura del repositorio coincide con FR-001. | Inspección del árbol de archivos. |
| AC-002 | `docker compose up --build` levanta `db`, `api` y `web` desde un entorno limpio. | Salida de `docker compose ps` con los tres servicios activos. |
| AC-003 | `GET /api/health` responde `200` con `database: ok` cuando PostgreSQL está disponible. | `curl` y prueba automatizada. |
| AC-004 | `/api/health` responde `503` cuando PostgreSQL está detenido, sin tumbar la API. | Prueba manual y prueba automatizada con doble. |
| AC-005 | `alembic upgrade head`, `alembic downgrade base` y un nuevo upgrade funcionan sobre una base limpia. | Salida de los tres comandos. |
| AC-006 | El frontend muestra el nombre del proyecto y el estado de la API. | Prueba de componente y verificación en navegador. |
| AC-007 | `uv run pytest` pasa sin base de datos. | Salida del comando. |
| AC-008 | `npm run lint`, `npm run typecheck`, `npm run test` y `npm run build` pasan. | Salida de los comandos. |
| AC-009 | `uv run ruff check .` y `uv run ruff format --check .` pasan. | Salida de los comandos. |
| AC-010 | No hay secretos versionados y `.env` está ignorado. | Revisión de `.gitignore` y `git status`. |
| AC-011 | El README permite arrancar y verificar el proyecto desde un clon limpio. | Ejecución guiada de los pasos. |
| AC-012 | La base de datos no está expuesta fuera de localhost. | Inspección de `compose.yaml` y de los puertos publicados. |

## 10. Preguntas abiertas y supuestos

### Supuestos aceptados para esta iteración

- Se usa PostgreSQL 16 sobre Alpine.
- El backend usa Python 3.13 sobre una imagen slim.
- El frontend usa Node.js 20 sobre Alpine.
- La gestión de dependencias es `uv` para backend y `npm` para frontend.
- SQLAlchemy se usa en modo síncrono; no se introduce async para el MVP.
- Los puertos por defecto son `8000` para la API, `3001` para la web y `5433` para PostgreSQL en localhost.
- El frontend de desarrollo usa el proxy de Vite hacia `/api`; no se habilita CORS.
- La API arranca aunque PostgreSQL no esté disponible y lo reporta mediante `/api/health`.
- Nginx y el endurecimiento de contenedores se abordan en la especificación de entrega, no en esta.
- No se incorpora CI/CD en el MVP.

### Preguntas pendientes

Ninguna bloqueante para elaborar el plan técnico de esta especificación.

## 11. Resultado de validación

- Fecha: 2026-10-21.
- Veredicto: **cumplida**.
- Evidencia: tabla de validación en [`tasks.md`](tasks.md).
