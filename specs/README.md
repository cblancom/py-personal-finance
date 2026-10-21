# Especificaciones — Py Personal Finance

Índice del plan global por fases y estado de las especificaciones SDD.

## Flujo de trabajo

Cada especificación sigue este ciclo antes de implementarse:

1. `spec.md`: qué se necesita y por qué.
2. Clarificación: ambigüedades, casos límite y supuestos.
3. `plan.md`: cómo se construirá.
4. `tasks.md`: trabajo ejecutable y verificable.
5. Implementación incremental.
6. Validación con evidencia y actualización de la trazabilidad.

Los principios del proyecto están en [`../constitution.md`](../constitution.md) y las instrucciones operativas en [`../AGENTS.md`](../AGENTS.md).

## Estado de las especificaciones

| Orden | Especificación | Fase | Alcance | Depende de | Estado |
|---|---|---|---|---|---|
| 001 | [`001-fundaciones`](001-fundaciones/spec.md) ([plan](001-fundaciones/plan.md), [tareas](001-fundaciones/tasks.md)) | 0 | Estructura, salud, SQLAlchemy, Alembic, compose de desarrollo y arneses de prueba | Constitución y AGENTS | En implementación (T-001 a T-005 completadas) |
| 002 | `002-api-ingresos` | 1 | Modelo, migración y CRUD completo de ingresos | 001 | Pendiente |
| 003 | `003-api-gastos` | 1 | Modelo, migración y CRUD completo de gastos con tipo | 001 | Pendiente |
| 004 | `004-api-resumen` | 2 | Totales de ingresos y gastos, balance y desglose por tipo | 002, 003 | Pendiente |
| 005 | `005-interfaz-mvp` | 3 | Formularios, listados, edición, eliminación, totales y estados de UI | 002, 003, 004 | Pendiente |
| 006 | `006-entrega-docker` | 4 | Dockerfiles de producción, Nginx, prueba de humo y validación del MVP | 005 | Pendiente |

Estados posibles: `Pendiente`, `En clarificación`, `Aprobada`, `En implementación`, `Implementada`, `Validada`.

## Alcance del MVP

Incluido:

- Registrar, listar, editar y eliminar ingresos.
- Registrar, listar, editar y eliminar gastos.
- Clasificar gastos como `NECESARIO`, `NO_NECESARIO` o `INVERSION`.
- Calcular total de ingresos, total de gastos, balance y desglose por tipo.
- Interfaz local de una sola página.
- Persistencia en PostgreSQL con migraciones Alembic.
- Ejecución completa con Docker Compose.

Fuera del MVP:

- Autenticación y multiusuario.
- Vista o filtro mensual.
- Categorías configurables.
- Presupuestos, gráficos, importación/exportación y movimientos recurrentes.
- CI/CD, métricas y despliegue en la nube.

## Decisiones confirmadas

- Aplicación local de un solo usuario, sin autenticación.
- Importes con `Decimal` en Python y `NUMERIC` en PostgreSQL; nunca `float`.
- CRUD completo, incluida la edición, desde el inicio.
- Vista mensual después del MVP.
- Contrato externo en español: rutas, campos JSON, tablas y columnas.
- Código interno en inglés: módulos, clases, funciones, variables, componentes y pruebas.
- Los DTO de frontera conservan los nombres del contrato en español.
- SQLAlchemy síncrono con `psycopg` 3.
- Sin CORS: el frontend consume `/api` mediante proxy de mismo origen.

## Evolución post-MVP

Orden propuesto, sujeto a nuevas especificaciones:

1. Vista y filtro mensual.
2. Categorías configurables.
3. Gráficos de evolución y distribución.
4. Autenticación y aislamiento por usuario.
5. Presupuestos y metas.
6. Importación y exportación CSV.
7. Búsqueda, filtros y paginación.
8. Movimientos recurrentes.
9. CI, observabilidad y respaldos.

La autenticación es obligatoria antes de exponer la aplicación a Internet.

## Convención para nuevas especificaciones

- Usar el siguiente número disponible: `specs/NNN-nombre-corto/`.
- Mantener un `spec.md` por capacidad cohesiva, con requisitos identificados como `FR-NNN` y no funcionales como `NFR-NNN`.
- No crear `plan.md` hasta que `spec.md` esté revisado y sin preguntas bloqueantes.
- No implementar hasta que `tasks.md` esté revisado y aprobado.
- Actualizar este índice al crear, aprobar o validar una especificación.
