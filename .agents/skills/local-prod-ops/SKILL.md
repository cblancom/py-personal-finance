---
name: local-prod-ops
description: Opera y valida la entrega Docker local de Py Personal Finance, incluyendo cambio entre desarrollo y producción, migraciones, smoke test, respaldos y diagnóstico del puerto 3001. Úsala al levantar, detener, reconstruir o revisar la entrega local.
---

# Skill: Local production operations

## Propósito

Proporciona un runbook seguro para operar la entrega local de producción sin mezclarla con el entorno de desarrollo.

Esta skill es operativa. Para cambios de código usa `spec-driven-development` y la skill de implementación correspondiente.

## Modelo mental

Hay dos entornos distintos:

| Entorno | Archivo | Web | API | PostgreSQL | OpenAPI |
|---|---|---|---|---|---|
| Desarrollo | `compose.yaml` | `3001` | `8000` | `5433` | Sí, en `8000/docs` |
| Producción local | `compose.prod.yaml` | `3001` | Solo red interna | Solo red interna | No |

Ambos publican la web en `3001`. **Nunca deben estar levantados a la vez.**

Producción usa:

- Proyecto Compose `py-personal-finance-prod`.
- Volumen `py-personal-finance-prod_postgres_data`.
- Nginx en el puerto interno `8080`.
- API en el puerto interno `8000`.
- Solo la web publicada en `127.0.0.1:3001`.
- OpenAPI y PostgreSQL no publicados.

## Archivos relevantes

- `compose.yaml`: desarrollo.
- `compose.prod.yaml`: producción local.
- `.env.production.example`: plantilla versionada.
- `.env.production`: configuración local ignorada, con permisos `600`.
- `docker/Dockerfile.api`: etapas `dev` y `prod`.
- `docker/Dockerfile.web`: build de React y runtime de Nginx.
- `docker/nginx.conf`: estáticos, fallback SPA y proxy `/api`.
- `scripts/smoke.sh`: comprobaciones de solo lectura.

## Reglas de seguridad

- No ejecutes `docker compose ... down -v` sin autorización explícita.
- No ejecutes `docker volume prune`, `docker system prune` ni operaciones equivalentes.
- No publiques los puertos de API o PostgreSQL en producción.
- No expongas la entrega a Internet ni a la LAN.
- No habilites TLS ni autenticación desde esta skill; requieren una especificación.
- No imprimas `.env.production` ni copies su contraseña en la conversación.
- No uses `docker compose config` para compartir salida: puede contener secretos resueltos.
- No edites archivos dentro de contenedores en ejecución.
- No uses la base de producción para pruebas destructivas.
- No declares éxito sin comprobar salud y smoke test.

## Comprobar el estado actual

Desarrollo:

```bash
docker compose ps
```

Producción:

```bash
docker compose --env-file .env.production -f compose.prod.yaml ps -a
```

Antes de arrancar cualquiera de los dos, verifica que el puerto `3001` esté libre:

```bash
ss -ltnp 2>/dev/null | grep ':3001' || lsof -i :3001 2>/dev/null || true
```

Si aparece un contenedor de otro proyecto, no lo detengas sin autorización.

## Arrancar producción

### 1. Detener desarrollo

```bash
docker compose down
```

No uses `-v`. El volumen de desarrollo debe conservarse.

### 2. Verificar el entorno

Comprueba que exista `.env.production` y que tenga permisos restrictivos:

```bash
test -f .env.production || cp -n .env.production.example .env.production
chmod 600 .env.production
```

Revisa que `POSTGRES_PASSWORD` y `DATABASE_URL` estén definidos, sin imprimir sus valores. Si `DATABASE_URL` contiene una contraseña con caracteres especiales, debe estar codificada correctamente.

Valida la configuración:

```bash
docker compose --env-file .env.production -f compose.prod.yaml config -q
```

### 3. Construir y arrancar

```bash
docker compose --env-file .env.production -f compose.prod.yaml up --build -d
```

El orden es:

1. `db` healthy.
2. `migrate` ejecuta `alembic upgrade head` y termina con código `0`.
3. `api` arranca y queda healthy.
4. `web` arranca y queda healthy.

Si `migrate` falla, `api` no arranca. No fuerces el arranque de la API.

### 4. Verificar

```bash
docker compose --env-file .env.production -f compose.prod.yaml ps -a
docker compose --env-file .env.production -f compose.prod.yaml logs --no-color migrate
WEB_PORT=3001 ./scripts/smoke.sh
```

Comprueba:

- `migrate` aparece como `Exited (0)`.
- `api`, `db` y `web` están healthy.
- Solo `web` muestra `127.0.0.1:3001->8080/tcp`.
- `smoke.sh` termina con `smoke: OK`.
- `/api/health` responde `200` a través de `3001`.

Comprobaciones opcionales:

```bash
docker compose --env-file .env.production -f compose.prod.yaml exec -T api id -u
docker compose --env-file .env.production -f compose.prod.yaml exec -T web id -u
docker compose --env-file .env.production -f compose.prod.yaml exec -T api alembic current
```

Los UID esperados son `10001` para la API y `101` para la web.

## Detener producción

```bash
docker compose --env-file .env.production -f compose.prod.yaml down
```

Esto conserva el volumen. Para volver a arrancar:

```bash
docker compose --env-file .env.production -f compose.prod.yaml up -d
```

## Volver a desarrollo

```bash
docker compose --env-file .env.production -f compose.prod.yaml down
docker compose up -d
```

Después abre `http://localhost:3001`. La API de desarrollo queda en `http://localhost:8000` y OpenAPI en `http://localhost:8000/docs`.

## Reconstruir tras cambios

```bash
docker compose --env-file .env.production -f compose.prod.yaml up --build -d
WEB_PORT=3001 ./scripts/smoke.sh
```

No ejecutes `down -v` para “limpiar”. Si el cambio requiere una migración, `migrate` la aplica al arrancar.

## Migraciones

`migrate` se ejecuta como servicio one-shot. Para repetirlo:

```bash
docker compose --env-file .env.production -f compose.prod.yaml run --rm migrate
```

Para consultar la revisión actual:

```bash
docker compose --env-file .env.production -f compose.prod.yaml exec -T api alembic current
```

No ejecutes `alembic downgrade` ni migraciones destructivas sin autorización.

## Respaldo

Respaldo manual:

```bash
docker compose --env-file .env.production -f compose.prod.yaml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > respaldo.sql
```

La restauración se hace en un entorno controlado y con la API detenida. No la automatices ni la ejecutes contra una base con datos sin revisar antes el procedimiento y las consecuencias.

`down -v` elimina el volumen de producción. Requiere autorización explícita.

## Diagnóstico

### El puerto 3001 está ocupado

Comprueba qué entorno está levantado:

```bash
docker compose ps
docker compose --env-file .env.production -f compose.prod.yaml ps -a
```

Detén el entorno que no corresponda.

### `migrate` falló

```bash
docker compose --env-file .env.production -f compose.prod.yaml ps -a
docker compose --env-file .env.production -f compose.prod.yaml logs --no-color migrate
```

Corrige la migración o el entorno y vuelve a arrancar. No arranques solo `api` para saltarte la migración.

### La web responde 502

Nginx está arriba, pero la API no:

```bash
docker compose --env-file .env.production -f compose.prod.yaml ps
docker compose --env-file .env.production -f compose.prod.yaml logs --no-color api
```

Comprueba `/api/health` a través de `3001` y la salud de `api`.

### OpenAPI no funciona

En producción, `/docs` y `/openapi.json` no se publican. `/docs` en `3001` devuelve la SPA, no OpenAPI.

Para consultar OpenAPI, detén producción y levanta desarrollo:

```bash
docker compose --env-file .env.production -f compose.prod.yaml down
docker compose up -d
```

Después abre `http://localhost:8000/docs`.

### Faltan variables obligatorias

El Compose falla si faltan `POSTGRES_PASSWORD` o `DATABASE_URL`. Revisa `.env.production` sin mostrar su contenido y vuelve a validar con `config -q`.

### Vite sirve código viejo en desarrollo

Si el servidor de desarrollo mantiene un módulo obsoleto tras ediciones rápidas, reinicia `web`:

```bash
docker compose restart web
```

Esto solo aplica a desarrollo; producción sirve archivos compilados.

## Checklist de operación

- [ ] Solo un entorno usa el puerto `3001`.
- [ ] `.env.production` existe, está ignorado y tiene permisos `600`.
- [ ] `config -q` pasa.
- [ ] `migrate` termina con código `0`.
- [ ] `api`, `db` y `web` están healthy.
- [ ] Solo la web publica un puerto.
- [ ] `smoke.sh` pasa.
- [ ] Los logs no contienen contraseñas ni `DATABASE_URL`.
- [ ] No se ejecutó `down -v`.
- [ ] Si se volvió a desarrollo, producción está detenida.

## Errores frecuentes

- Levantar desarrollo y producción a la vez.
- Ejecutar `docker compose down -v` para resolver un conflicto.
- Publicar `8000` o `5433` en producción.
- Intentar abrir `/docs` o `/openapi.json` en `3001`.
- Arrancar `api` sin que `migrate` haya terminado.
- Usar `docker compose logs` sin `-f compose.prod.yaml` y confundir el entorno.
- Compartir la salida de `docker compose config`.
- Restaurar un respaldo sobre una base con datos sin revisar el procedimiento.
