# Especificación 006 — Entrega Docker

- Estado: validada.
- Fase: 4.
- Iteración: MVP.
- Dependencias: `specs/005-interfaz-mvp/`.
- Plan: `plan.md` (aprobado).
- Tareas: `tasks.md` (aprobadas).

## 1. Contexto y problema

El entorno actual de Docker Compose está pensado para desarrollo:

- El frontend se sirve con Vite, recarga en caliente y el código se monta desde el host.
- La API se ejecuta con `--reload`, monta `backend/` y su imagen incluye dependencias de prueba.
- PostgreSQL publica su puerto en localhost para facilitar el trabajo local.
- Las migraciones se ejecutan manualmente.

Ese entorno no es una entrega reproducible: depende de archivos del host, instala herramientas que no se necesitan en ejecución y no tiene un punto de entrada único para el navegador.

La especificación 006 construye una entrega local parecida a producción, sin exponer la aplicación fuera del host. El navegador accede a un único origen; Nginx sirve el frontend compilado y reenvía `/api` a la API; la API solo es accesible dentro de la red de Docker; PostgreSQL conserva los datos en un volumen; y las migraciones se aplican de forma controlada antes de arrancar la API.

Esta entrega sigue siendo de un solo usuario, local y sin autenticación. No incluye TLS, dominio, acceso desde Internet ni despliegue en la nube.

## 2. Usuarios y actores

- **Propietario/operador:** persona que construye, arranca, detiene y respalda la aplicación en su equipo.
- **Desarrollador:** persona que mantiene las imágenes, la configuración de Nginx y el Compose de producción.
- **Agente de implementación:** agente que trabaja siguiendo `constitution.md`, `AGENTS.md` y esta especificación.
- **Usuario final:** accede desde el mismo host mediante el puerto web; no hay usuarios remotos ni roles.

No se implementan autenticación, permisos ni multiusuario.

## 3. Historias de usuario y flujos

### US-001 — Construir y arrancar la entrega

Como operador, quiero construir y arrancar la aplicación desde un entorno limpio con un comando documentado para obtener una entrega reproducible.

**Flujo esperado:**

1. El entorno de desarrollo está detenido para liberar el puerto `3001`.
2. Existe una plantilla de variables de producción.
3. El operador crea su archivo de entorno local con una contraseña real.
4. Docker Compose construye las imágenes de API y web.
5. PostgreSQL queda saludable.
6. El servicio de migraciones aplica el esquema y termina correctamente.
7. La API arranca y queda saludable.
8. Nginx sirve la interfaz en `http://127.0.0.1:3001`.

### US-002 — Acceder por un único origen

Como usuario, quiero abrir la interfaz en el navegador y que las peticiones a `/api` funcionen sin configurar CORS ni URLs absolutas.

**Flujo esperado:**

1. El navegador carga `/` desde Nginx.
2. Nginx entrega `index.html` y los assets compilados.
3. Las peticiones a `/api/*` se reenvían al servicio `api` conservando la ruta.
4. La interfaz funciona igual que en desarrollo.
5. Una recarga en una ruta del frontend devuelve `index.html`, no un `404`.

### US-003 — Aplicar migraciones y conservar datos

Como operador, quiero que el esquema se actualice antes de arrancar la API y que los datos sobrevivan a un reinicio normal.

**Flujo esperado:**

1. PostgreSQL está disponible y saludable.
2. El servicio `migrate` ejecuta `alembic upgrade head`.
3. Si la migración falla, la API no arranca.
4. Si la migración termina bien, la API arranca.
5. `docker compose --env-file .env.production -f compose.prod.yaml down` conserva el volumen de datos.
6. Un nuevo `up` reutiliza los datos existentes.

### US-004 — Diagnosticar el estado de la entrega

Como operador, quiero comprobar la salud de los servicios y revisar logs sin encontrar secretos para distinguir un fallo de infraestructura de un fallo de la aplicación.

**Flujo esperado:**

1. PostgreSQL tiene healthcheck.
2. La API expone `/api/health` y responde `200` cuando la base está disponible.
3. Nginx expone `/healthz`.
4. `docker compose --env-file .env.production -f compose.prod.yaml ps` muestra el estado de los servicios.
5. Los logs se escriben en stdout y no incluyen contraseñas ni cadenas de conexión.

### US-005 — Verificar la entrega con una prueba de humo

Como operador, quiero ejecutar una comprobación de solo lectura para confirmar que la web, Nginx, la API y PostgreSQL están conectados.

**Flujo esperado:**

1. La web responde `200`.
2. `/healthz` responde `200`.
3. `/api/health` responde `200` con la base disponible.
4. `/api/resumen` responde `200`.
5. Una ruta SPA desconocida devuelve `index.html`.
6. La prueba no crea, edita ni elimina movimientos.

## 4. Requisitos funcionales

### FR-001 — Imagen de producción de la API

La API debe tener una imagen de ejecución que:

- Use Python 3.13 y una versión fijada de `uv`.
- Instale solo dependencias de ejecución, sin `pytest`, `ruff` ni herramientas de desarrollo.
- No copie pruebas ni archivos innecesarios.
- Ejecute Uvicorn sin `--reload`.
- No monte código desde el host.
- Ejecute la aplicación con un usuario no root.
- Exponga el puerto interno `8000` solo dentro de la red de Docker.

La imagen de desarrollo debe conservarse para poder ejecutar la suite dentro de Docker. La separación puede hacerse con etapas (`dev` y `prod`) del mismo Dockerfile o con un Dockerfile de producción independiente.

**Verificación:** la imagen de producción arranca sin dependencias de desarrollo y el contenedor no se ejecuta como root.

### FR-002 — Imagen de producción del frontend

El frontend debe construirse en una etapa con Node 20 y `npm ci`, y la imagen final debe contener únicamente:

- Nginx.
- La configuración del servidor.
- Los archivos estáticos generados en `frontend/dist`.

La imagen final no debe incluir Node, npm, código fuente ni dependencias de desarrollo. Nginx debe ejecutarse como usuario no root y escuchar en el puerto interno `8080`.

**Verificación:** la imagen final no contiene `node_modules` ni el código fuente; el contenedor sirve la aplicación compilada.

### FR-003 — Configuración de Nginx

Nginx debe:

- Servir `/` y los assets estáticos.
- Devolver `index.html` para rutas SPA desconocidas.
- Reenviar `/api/` a `api:8000` conservando la ruta original.
- Exponer `/healthz` para el healthcheck del contenedor.
- Comprimir respuestas de texto cuando corresponda.
- Cachear los assets con hash durante un periodo largo.
- No cachear `index.html`.
- Añadir cabeceras básicas de seguridad.
- No habilitar CORS; el navegador y la API comparten origen a través de Nginx.
- No exponer `/docs`, `/openapi.json` ni otros endpoints del backend fuera de `/api/`.

**Verificación:** las rutas de la interfaz y del API funcionan a través del puerto web; una ruta SPA desconocida devuelve la aplicación.

### FR-004 — Compose de producción

Debe existir un archivo `compose.prod.yaml` separado del Compose de desarrollo, con:

- Un nombre de proyecto propio para no compartir contenedores ni volúmenes con desarrollo.
- Servicios `db`, `migrate`, `api` y `web`.
- Sin bind mounts de código.
- Sin servidores de desarrollo.
- `restart: unless-stopped` en los servicios de larga duración.
- Dependencias basadas en salud y en finalización correcta de migraciones.
- Un volumen nombrado para PostgreSQL.
- Solo el servicio `web` publicado en el host.
- Publicación de la web en `127.0.0.1:${WEB_PORT:-3001}:8080`.
- Sin puertos publicados para `api` ni `db`.

El Compose de desarrollo debe seguir funcionando sin cambios funcionales. Como ambos entornos publican la web en `3001`, el entorno de desarrollo debe estar detenido antes de arrancar producción.

**Verificación:** `docker compose --env-file .env.production -f compose.prod.yaml ps` muestra los servicios esperados y ningún puerto de API o base de datos publicado en el host.

### FR-005 — Configuración y secretos

La entrega debe incluir una plantilla `.env.production.example` versionada y un archivo `.env.production` ignorado por Git.

Debe exigir, como mínimo:

- `POSTGRES_PASSWORD` con un valor real, sin contraseña por defecto en producción.
- `DATABASE_URL` apuntando a `db:5432`.
- `WEB_PORT` con valor por defecto `3001`.

La documentación debe explicar que una contraseña con caracteres especiales debe escribirse correctamente codificada en `DATABASE_URL` y que los valores de ejemplo no son válidos para uso real.

**Verificación:** el Compose falla de forma comprensible si faltan variables obligatorias; `.env.production` no aparece en `git status`.

### FR-006 — Migraciones controladas

Debe existir un servicio `migrate` que:

- Use la imagen de producción de la API.
- Ejecute `alembic upgrade head`.
- Dependa de que PostgreSQL esté saludable.
- Termine con código `0` si la migración es correcta.
- No arranque Uvicorn.

El servicio `api` debe depender de la finalización correcta de `migrate`. Si la migración falla, la API no debe arrancar. No se debe usar `Base.metadata.create_all()`.

**Verificación:** una migración correcta permite arrancar la API; una migración fallida impide su arranque.

### FR-007 — Persistencia y respaldo

PostgreSQL debe usar un volumen nombrado. Los datos deben conservarse tras:

```bash
docker compose --env-file .env.production -f compose.prod.yaml down
docker compose --env-file .env.production -f compose.prod.yaml up -d
```

La documentación debe explicar:

- Que `down -v` elimina los datos y requiere autorización explícita.
- Cómo crear un respaldo con `pg_dump`.
- Cómo restaurar un respaldo en un entorno controlado.

No se implementa respaldo automático ni restauración programada.

**Verificación:** los datos de una prueba sobreviven a un ciclo `down`/`up` sin `-v`.

### FR-008 — Salud, logs y diagnóstico

La entrega debe incluir:

- Healthcheck de PostgreSQL con `pg_isready`.
- Healthcheck de la API contra `/api/health`.
- Healthcheck de Nginx contra `/healthz`.
- Logs de servicios en stdout/stderr.
- Ausencia de contraseñas, URLs de conexión y datos financieros en logs.

**Verificación:** `docker compose --env-file .env.production -f compose.prod.yaml ps` refleja el estado; los logs no contienen secretos.

### FR-009 — Prueba de humo

Debe existir un script de prueba de humo que, usando `WEB_PORT`:

- Compruebe que la web responde.
- Compruebe `/healthz`.
- Compruebe `/api/health`.
- Compruebe `/api/resumen`.
- Compruebe el fallback SPA.
- Falle con código distinto de cero si alguna comprobación no se cumple.
- No modifique datos.

La prueba debe poder ejecutarse después de `docker compose --env-file .env.production -f compose.prod.yaml up -d`.

**Verificación:** el script termina con código `0` con la entrega sana y con código distinto de cero si un servicio no responde.

### FR-010 — Documentación operativa

README y AGENTS deben documentar:

- Cómo crear `.env.production`.
- Cómo construir y arrancar la entrega.
- Cómo ver el estado y los logs.
- Cómo ejecutar la prueba de humo.
- Cómo detener la entrega conservando datos.
- Cómo respaldar y restaurar.
- El puerto `3001` y la ausencia de exposición externa.
- La diferencia entre el Compose de desarrollo y el de producción.

`specs/README.md` debe actualizarse con el estado de esta especificación.

**Verificación:** los comandos documentados funcionan y no contradicen los archivos reales.

### FR-011 — Endurecimiento básico

La entrega debe:

- Ejecutar API y web con usuarios no root.
- No montar código fuente en producción.
- No incluir secretos en imágenes.
- No publicar API ni PostgreSQL en el host.
- Publicar la web solo en `127.0.0.1`.
- Incluir cabeceras básicas de seguridad en Nginx.

No se implementan perfiles seccomp personalizados, rootless Docker, firmas de imagen ni aislamiento multiusuario.

**Verificación:** los contenedores no se ejecutan como root; `docker compose --env-file .env.production -f compose.prod.yaml ps` no muestra puertos de API o base de datos.

## 5. Requisitos no funcionales

### NFR-001 — Reproducibilidad

La entrega debe construirse desde un entorno limpio de contenedores, sin borrar volúmenes con datos, con las versiones fijadas en `uv.lock` y `package-lock.json` y sin pasos manuales no documentados.

### NFR-002 — Seguridad y privacidad

La aplicación no se expone fuera del host. Los secretos se gestionan por entorno, no se versionan y no aparecen en imágenes ni logs.

### NFR-003 — Compatibilidad

Debe funcionar con Docker Compose v2 y con el flujo de desarrollo existente. No se cambia el contrato de la API ni el esquema de la base de datos.

### NFR-004 — Rendimiento de entrega

Nginx debe cachear assets con hash y comprimir respuestas de texto. La entrega no debe ejecutar Node ni Vite en tiempo de ejecución.

### NFR-005 — Observabilidad

Los servicios deben reportar salud y escribir logs en stdout. No se añaden métricas, trazas ni alertas externas.

### NFR-006 — Mantenibilidad

La configuración debe ser pequeña, explícita y reutilizar las imágenes y archivos existentes. No se añaden dependencias de aplicación.

### NFR-007 — No regresión

Las suites de backend y frontend deben seguir pasando, y el Compose de desarrollo debe seguir siendo utilizable.

### NFR-008 — Simplicidad

Se aplica YAGNI: no se añaden Kubernetes, registry, CI/CD, TLS, autenticación, backups automáticos ni servicios adicionales.

## 6. Reglas de negocio

- **BR-001:** la aplicación es local, de un solo usuario y sin autenticación.
- **BR-002:** no se expone a Internet ni a la LAN; el único puerto publicado es la web en `127.0.0.1`.
- **BR-003:** el puerto web externo se conserva en `3001`; el puerto interno de Nginx es `8080`. Desarrollo y producción no pueden estar levantados a la vez con el mismo puerto.
- **BR-004:** API y PostgreSQL solo son accesibles dentro de la red de Docker.
- **BR-005:** la moneda y el contrato de la API no cambian.
- **BR-006:** el esquema solo evoluciona mediante Alembic.
- **BR-007:** el proyecto de producción usa un nombre y un volumen distintos de desarrollo.
- **BR-008:** los datos de desarrollo no se migran automáticamente a producción.
- **BR-009:** `down -v` es destructivo y requiere autorización explícita.

## 7. Casos límite y errores

- Falta `.env.production` o una variable obligatoria: el Compose falla con un mensaje claro.
- Contraseña de ejemplo o demasiado débil: la documentación exige reemplazarla; no se implementa un validador de fortaleza.
- Caracteres especiales en la contraseña: `DATABASE_URL` debe codificarlos; se documenta.
- Puerto `3001` ocupado por el entorno de desarrollo: se debe detener el Compose de desarrollo antes de arrancar producción.
- Puerto `3001` ocupado por otro proceso: el arranque falla y se informa cómo cambiar `WEB_PORT`.
- PostgreSQL no disponible: `db` no queda healthy y `migrate`/`api` no arrancan.
- Migración fallida: `migrate` termina con error y `api` no arranca.
- Volumen existente con esquema antiguo: `migrate` aplica las revisiones pendientes.
- Build del frontend fallido: no se publica una imagen incompleta.
- Proxy de API caído: Nginx devuelve un error controlado y la interfaz muestra su estado de error.
- Ruta SPA desconocida: Nginx devuelve `index.html` con `200`.
- `index.html` cacheado tras un despliegue: se sirve sin caché.
- Logs con credenciales: se considera fallo de la entrega.
- `down -v` accidental: se advierte explícitamente en la documentación.
- Imagen de desarrollo usada por error en producción: el Compose de producción debe apuntar a la etapa o imagen correcta.

## 8. Fuera de alcance

- Exposición a Internet, LAN o acceso remoto.
- TLS, dominio, proxy inverso externo o certificados.
- Autenticación y multiusuario.
- CI/CD, registry de imágenes, etiquetado de versiones y despliegue automático.
- Kubernetes, Docker Swarm, multi-host, alta disponibilidad y cero downtime.
- Backups automáticos, monitoreo, métricas y alertas.
- Migración de datos desde el entorno de desarrollo.
- Cambios en la API, el frontend, el esquema o las reglas de negocio.
- Exposición pública de `/docs` o `/openapi.json`.
- Pruebas E2E de navegador.

## 9. Criterios de aceptación verificables

| ID | Criterio | Evidencia |
|---|---|---|
| AC-001 | `compose.prod.yaml` valida con las variables obligatorias. | `docker compose --env-file .env.production -f compose.prod.yaml config -q`. |
| AC-002 | La entrega se construye y arranca desde cero. | `up --build -d` y `ps` con servicios healthy, usando `.env.production`. |
| AC-003 | La web responde en `http://127.0.0.1:3001`. | `curl -I` y prueba de humo. |
| AC-004 | `/healthz` responde `200`. | Prueba de humo. |
| AC-005 | `/api/health` responde `200` con base disponible. | Prueba de humo. |
| AC-006 | `/api/resumen` responde `200`. | Prueba de humo. |
| AC-007 | Una ruta SPA desconocida devuelve `index.html`. | Prueba de humo. |
| AC-008 | Solo la web está publicada en el host. | Inspección de `docker compose --env-file .env.production -f compose.prod.yaml ps`. |
| AC-009 | Las migraciones se aplican antes de la API y son reintentables. | Logs de `migrate` y arranque de `api`. |
| AC-010 | Los datos persisten tras `down`/`up` sin `-v`. | Prueba con un movimiento temporal y limpieza. |
| AC-011 | API y web no se ejecutan como root; no hay secretos en imágenes ni logs. | `id` en contenedores y revisión de logs. |
| AC-012 | La prueba de humo pasa y falla si un servicio no responde. | `scripts/smoke.sh`. |
| AC-013 | Las suites de backend y frontend siguen pasando. | Comandos canónicos. |
| AC-014 | La documentación refleja los comandos y el estado real. | Revisión de README, AGENTS y `specs/README.md`. |

## 10. Preguntas abiertas y supuestos

### Supuestos aceptados

- La entrega es local y solo se publica en `127.0.0.1`.
- El puerto externo se mantiene en `3001` porque el `8080` del host está ocupado.
- Nginx escucha en `8080` dentro del contenedor y se ejecuta como usuario no root.
- Las migraciones se ejecutan en un servicio `migrate` separado.
- PostgreSQL se ejecuta en un contenedor con volumen nombrado; no se usa una base externa.
- El respaldo queda documentado, no automatizado.
- La prueba de humo es de solo lectura.
- No se migran datos de desarrollo a producción.
- No se cambia el contrato de la API ni el esquema.

### Preguntas pendientes

Ninguna bloqueante. Cualquier cambio de exposición, autenticación, TLS o estrategia de migraciones requiere revisar esta especificación antes de implementar.

## 11. Resultado de validación

Validada el 2026-10-21. La entrega local se construyó y arrancó desde contenedores limpios sin borrar volúmenes; `api`, `db` y `web` quedaron healthy; las migraciones se aplicaron antes de la API; la prueba de humo pasó; la persistencia se comprobó con un movimiento temporal; API y web ejecutan como usuarios no root; los logs no contienen secretos; y las suites de frontend y backend pasan. La entrega queda disponible en `http://127.0.0.1:3001`.
