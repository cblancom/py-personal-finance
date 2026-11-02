# Tareas 008 — Balance mensual

- Estado: validada (revisión 3).
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-004
  └─────► T-003 ──► T-005
T-004 + T-005 ──► T-006 ──► T-007 ──► T-008
T-001 a T-008 ──► T-009 ──► T-010 ──► T-011 ──► T-012 ──► T-013 ──► T-014 ──► T-015
```

T-001 crea la persistencia. T-002 y T-003 pueden avanzar en paralelo después de T-001. T-004 y T-005 completan la API. T-006 a T-008 implementan el frontend. T-009 consolida las pruebas y T-010 valida y documenta.

Las decisiones D-001 a D-007 de `spec.md` y el plan están aprobados. La revisión 3 se implementa en T-011 a T-015.

## Tareas

- [x] **T-001 — Crear el modelo y la migración de asignaciones mensuales**
  - Requisitos: FR-011, NFR-001, NFR-003, NFR-007.
  - Dependencias: ninguna.
  - Descripción: crear `MonthlyAllocation` en `app/db/models/monthly_allocation.py` con tabla `asignaciones_mensuales`, una fila por año/mes, porcentajes `NUMERIC(5,2)`, checks de rango y suma, unique `(anio, mes)`, timestamps y exportación en `models/__init__.py`. Crear la migración `0007_create_monthly_allocations` con upgrade y downgrade.
  - Hecho cuando: la tabla existe con constraints e índice único; `alembic upgrade head` y `downgrade` funcionan; la versión esperada de la base de test es `0007`; no se modifican tablas existentes.
  - Evidencia (2026-10-31): modelo `MonthlyAllocation` y tabla `asignaciones_mensuales` con unique `(anio, mes)`, checks de rango y suma; migración `0007` aplicada en desarrollo y test; ciclo `0007 → 0006 → 0007` verificado; 232/232 pruebas de backend; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv run ruff check .
    uv run ruff format --check .
    uv run --env-file ../.env alembic upgrade head
    uv run --env-file ../.env alembic current
    ```

- [x] **T-002 — Implementar los cálculos y consultas del balance**
  - Requisitos: FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-015, NFR-001, NFR-002.
  - Dependencias: T-001.
  - Descripción: crear `app/services/monthly_balance.py` con funciones para obtener periodos disponibles, sumar ingresos y gastos por rango de fechas, leer asignaciones, cargar movimientos mensuales agrupados por columna, calcular asignado/restante/sin asignar y construir el balance mensual y anual. Usar `Decimal`, `SUM` y `GROUP BY` para los totales; los movimientos se consultan solo para la vista mensual.
  - Hecho cuando: los cálculos mensuales y anuales son correctos; el restante puede ser negativo; el porcentaje anual es ponderado; sin ingresos los asignados son cero; el monto sin asignar se normaliza a cero si el redondeo lo deja negativo.
  - Evidencia (2026-10-31): `monthly_balance.py` implementa cálculos puros de asignado, restante, sin asignar y porcentaje ponderado, además de consultas mensuales/anuales y periodos con `Decimal`, `SUM` y `GROUP BY`. 5 pruebas unitarias nuevas; 246/246 pruebas de backend; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-003 — Crear los schemas de balance y asignaciones**
  - Requisitos: FR-012, FR-014, FR-015, FR-016, NFR-001, NFR-003.
  - Dependencias: T-001.
  - Descripción: crear `app/api/schemas/monthly_balance.py` con DTOs para rubros, movimientos mensuales, balance mensual/anual, periodos y actualización de porcentajes. Validar cada porcentaje entre 0 y 100, máximo dos decimales y suma menor o igual a 100. Serializar importes y porcentajes como strings.
  - Hecho cuando: los schemas aceptan el contrato aprobado, rechazan porcentajes inválidos y el JSON conserva los nombres en español.
  - Evidencia (2026-10-31): `monthly_balance.py` define rubros, movimientos, balance mensual/anual, periodos y actualización de porcentajes; valida rango, dos decimales, presencia de los tres rubros y suma <=100. 9 pruebas de schema; serialización en español verificada.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api
    uv run ruff check .
    ```

- [x] **T-004 — Implementar los endpoints de consulta**
  - Requisitos: FR-009, FR-010, FR-013, FR-014, FR-015, FR-016, NFR-002.
  - Dependencias: T-002, T-003.
  - Descripción: crear `app/api/routes/monthly_balance.py` con `GET /api/balance-mensual` para mes/año actual, `GET /api/balance-mensual/periodos` y registro en `main.py`. Validar `anio` y `mes`; devolver siempre los tres rubros y, en la consulta mensual, las cuatro listas de movimientos.
  - Hecho cuando: las consultas mensual y anual responden `200`; sin parámetros usan el año actual; los periodos incluyen años con datos y el año actual; OpenAPI contiene las rutas.
  - Evidencia (2026-10-31): `GET /api/balance-mensual` devuelve mes/año o anual con año actual por defecto; `GET /api/balance-mensual/periodos` devuelve años disponibles; OpenAPI contiene las rutas. 7 pruebas de integración y 1 de OpenAPI; 254/254 pruebas de backend.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api tests/integration
    uv run ruff check .
    ```

- [x] **T-005 — Implementar el guardado de porcentajes**
  - Requisitos: FR-004, FR-011, FR-012, FR-014.
  - Dependencias: T-003.
  - Descripción: añadir `PUT /api/balance-mensual/asignaciones/{anio}/{mes}` para crear o actualizar los tres porcentajes del mes, validar la suma y devolver el balance mensual actualizado, incluidos los movimientos del mes. Usar una transacción y rollback ante error.
  - Hecho cuando: guardar dos veces el mismo mes actualiza la fila sin duplicarla; los porcentajes de otros meses no cambian; la suma mayor que 100 devuelve `422`; no se crean movimientos.
  - Evidencia (2026-10-31): `PUT /api/balance-mensual/asignaciones/{anio}/{mes}` hace upsert, valida la suma, devuelve el balance con movimientos y no duplica filas; suma inválida devuelve `422`. Pruebas de integración incluidas en 254/254.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api tests/integration
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-006 — Crear tipos y cliente API del frontend**
  - Requisitos: FR-014, FR-015, FR-016.
  - Dependencias: T-004, T-005.
  - Descripción: añadir `frontend/src/types/monthlyBalance.ts` y `frontend/src/api/monthlyBalance.ts` con tipos de movimientos, consultas de periodos, balance mensual/anual y actualización de porcentajes. Añadir pruebas con `fetch` simulado.
  - Hecho cuando: el cliente usa `/api`, conserva strings decimales y las pruebas cubren rutas, métodos y cuerpos.
  - Evidencia (2026-10-31): `monthlyBalance.ts` define tipos de rubros, movimientos, periodos y payload; el cliente usa `/api` para periodos, balance mensual/anual y actualización de porcentajes. 4 pruebas nuevas; 81/81 frontend; lint, typecheck y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [x] **T-007 — Implementar `MonthlyBalanceView`**
  - Requisitos: FR-002, FR-003, FR-005, FR-006, FR-008, FR-009, FR-010, FR-017.
  - Dependencias: T-006.
  - Descripción: crear la vista con selectores de año/mes, carga de periodos, consulta del balance, cuatro columnas mensuales con fecha/descripción/valor, tabla anual agregada, totales, restantes, monto sin asignar y estados de carga, error, vacío y reintento. La vista anual se activa con `Todos` y muestra porcentaje ponderado.
  - Hecho cuando: los selectores cambian el periodo; la vista mensual muestra las cuatro columnas y sus totales; la vista anual agrega el año; las columnas vacías tienen estado propio; los estados de UI son accesibles.
  - Evidencia (2026-10-31): `MonthlyBalanceView` carga periodos, consulta mes/año, muestra cuatro columnas con fecha/descripción/valor, totales, restantes, sin asignar y tabla anual agregada; 5 pruebas de vista; 87/87 frontend.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [x] **T-008 — Añadir edición de porcentajes e integrar la pestaña**
  - Requisitos: FR-001, FR-004, FR-017.
  - Dependencias: T-007.
  - Descripción: añadir edición de porcentajes en la vista mensual, botón `Guardar porcentajes`, validación local, confirmación de guardado y refresco del balance. Mostrar los restantes en las columnas de gastos necesarios, gastos no necesarios e inversión. Integrar `Balance mensual` como tercera pestaña en `App` y ajustar estilos.
  - Hecho cuando: la pestaña existe y es accesible; guardar porcentajes actualiza los totales y restantes; un error de validación se muestra sin perder datos; los porcentajes de un mes no afectan a otro.
  - Evidencia (2026-10-31): edición y guardado de porcentajes con validación local, confirmación y refresco; pestaña `Balance mensual` integrada en `App`; estilos responsive; 87/87 frontend y build OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [x] **T-009 — Completar pruebas de backend, frontend y OpenAPI**
  - Requisitos: FR-001 a FR-018, NFR-004, NFR-007.
  - Dependencias: T-001 a T-008.
  - Descripción: cubrir cálculos, schemas, endpoints, listas de movimientos con fecha/descripción/valor, columnas vacías, integración con PostgreSQL, migración `0007`, OpenAPI, cliente API, componentes y pestaña en `App`. Verificar que las suites existentes siguen pasando.
  - Hecho cuando: los casos de la matriz están cubiertos; backend y frontend pasan; la migración upgrade/downgrade funciona; OpenAPI incluye las rutas.
  - Evidencia (2026-10-31): 256/256 pruebas backend y 88/88 frontend; OpenAPI, migración `0007`, movimientos, columnas vacías, porcentajes sin asignar y restante negativo cubiertos; ruff, format, lint, typecheck y build pasan.
  - Verificación:
    ```bash
    cd backend
    uv run --env-file ../.env pytest
    uv run ruff check .
    uv run ruff format --check .
    ```
    ```bash
    cd frontend
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```

- [x] **T-010 — Documentar y validar la especificación**
  - Requisitos: AC-001 a AC-014, NFR-004, NFR-006, NFR-007, NFR-008.
  - Dependencias: T-009.
  - Descripción: actualizar README, AGENTS y `specs/README.md`; registrar evidencia; reconstruir producción; ejecutar smoke test y verificar el flujo mensual/anual.
  - Hecho cuando: la documentación coincide con la implementación; los AC tienen evidencia; producción está saludable; la especificación queda validada.
  - Evidencia (2026-10-31): README, AGENTS y `specs/README.md` actualizados; producción migrada a `0007`, servicios healthy, smoke OK y endpoints `GET /api/balance-mensual` y `/periodos` verificados. 256/256 backend y 88/88 frontend.
  - Verificación:
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml config -q
    docker compose --env-file .env.production -f compose.prod.yaml up --build -d
    WEB_PORT=3001 ./scripts/smoke.sh
    ```

- [x] **T-011 — Implementar la cadena de arrastre**
  - Requisitos: FR-019, FR-020, FR-021, NFR-001, NFR-002.
  - Dependencias: T-010.
  - Descripción: calcular el arrastre desde el primer mes con datos, aplicando necesarios a no necesarios, no necesarios a no necesarios e inversión a inversión; arrastrar positivos y negativos; pasar de diciembre a enero del año siguiente; recalcular de forma dinámica.
  - Hecho cuando: los cálculos mensuales y anuales incluyen `arrastre` y `disponible`; el arrastre no se reinicia en enero; los cambios históricos recalculan los meses posteriores.
  - Evidencia (2026-10-31): el servicio calcula la cadena desde el primer mes con datos, arrastra necesarios a no necesarios, mantiene no necesarios e inversión independientes, cruza diciembre a enero y recalcula dinámicamente. 272/272 pruebas backend; ruff y format pasan.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/core tests/integration
    uv run ruff check .
    uv run ruff format --check .
    ```

- [x] **T-012 — Actualizar el contrato de API**
  - Requisitos: FR-022, FR-014, FR-015, FR-016.
  - Dependencias: T-011.
  - Descripción: añadir `arrastre` y `disponible` a los schemas de rubros, mapear los nuevos campos en la ruta y actualizar las pruebas de schema y API.
  - Hecho cuando: la respuesta mensual y anual incluye los nuevos campos; OpenAPI y pruebas pasan.
  - Evidencia (2026-10-31): `BalanceRubroRead` incluye `arrastre` y `disponible`; la ruta mensual/anual los mapea; pruebas de schema e integración actualizadas. 272/272 backend; ruff y format OK.
  - Verificación:
    ```bash
    cd backend
    uv run pytest tests/api tests/integration
    uv run ruff check .
    ```

- [x] **T-013 — Mostrar el arrastre en la vista mensual**
  - Requisitos: FR-003, FR-019, FR-022.
  - Dependencias: T-012.
  - Descripción: actualizar tipos y columnas para mostrar asignado, arrastre, disponible y restante; indicar que el restante de necesarios se transfiere a no necesarios.
  - Hecho cuando: la UI muestra el arrastre y el disponible; los tests de componentes pasan.
  - Evidencia (2026-10-31): la vista mensual muestra `Asignado`, `Arrastre`, `Disponible` y `Restante`; en necesarios el restante se etiqueta como transferido. 99/99 frontend; lint, typecheck y build OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [x] **T-014 — Actualizar la tabla anual con arrastre**
  - Requisitos: FR-009, FR-023.
  - Dependencias: T-012.
  - Descripción: mostrar `Asignado`, `Arrastre`, `Disponible`, `Gastado` y `Restante` en la tabla anual, con la semántica de necesarios/no necesarios/inversión y sin doble conteo.
  - Hecho cuando: la tabla anual muestra los cinco campos y las pruebas de API/componente pasan.
  - Evidencia (2026-10-31): la tabla anual muestra `Asignado`, `Arrastre`, `Disponible`, `Gastado` y `Restante`, con nota para el restante transferido de necesarios; 99/99 frontend; lint, typecheck y build OK.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [x] **T-015 — Revalidar la revisión 3 y publicar 1.1.0**
  - Requisitos: AC-015 a AC-020, NFR-004, NFR-007.
  - Dependencias: T-011 a T-014.
  - Descripción: completar pruebas, actualizar README/AGENTS/specs, sincronizar metadatos a 1.1.0 y validar producción.
  - Hecho cuando: las suites pasan; la documentación refleja el arrastre; la versión 1.1.0 está sincronizada; producción está healthy y el smoke test pasa.
  - Evidencia (2026-10-31): 272/272 backend y 99/99 frontend; versión 1.1.0 sincronizada; producción healthy en `0007`, smoke OK y respuesta de balance con `arrastre` y `disponible` verificada. La especificación queda validada.
  - Verificación:
    ```bash
    cd backend
    uv run --env-file ../.env pytest
    uv run ruff check .
    uv run ruff format --check .
    ```
    ```bash
    cd frontend
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```
    ```bash
    docker compose --env-file .env.production -f compose.prod.yaml config -q
    docker compose --env-file .env.production -f compose.prod.yaml up --build -d
    WEB_PORT=3001 ./scripts/smoke.sh
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-008 |
| FR-002 | T-007, T-008 |
| FR-003 | T-007, T-013 |
| FR-004 | T-005, T-008 |
| FR-005 | T-002, T-007, T-011 |
| FR-006 | T-002, T-007, T-011 |
| FR-007 | T-002, T-009 |
| FR-008 | T-002, T-007 |
| FR-009 | T-002, T-004, T-007, T-014 |
| FR-010 | T-004, T-007 |
| FR-011 | T-001, T-005 |
| FR-012 | T-003, T-005 |
| FR-013 | T-002, T-004 |
| FR-014 | T-004, T-005 |
| FR-015 | T-003, T-004 |
| FR-016 | T-003, T-004 |
| FR-017 | T-007, T-008 |
| FR-018 | T-009, T-010 |
| FR-019 | T-011, T-013 |
| FR-020 | T-011, T-015 |
| FR-021 | T-011, T-015 |
| FR-022 | T-012, T-013 |
| FR-023 | T-014 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001, T-002, T-003 |
| NFR-002 | T-002, T-004 |
| NFR-003 | T-001, T-003, T-004, T-005 |
| NFR-004 | T-009, T-010, T-015 |
| NFR-005 | T-007, T-008 |
| NFR-006 | T-010 |
| NFR-007 | T-009, T-010, T-015 |
| NFR-008 | T-010 |

## Evidencia de validación

Se completa durante T-015.

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumple | Pestaña `Balance mensual` y prueba de `App`. |
| AC-002 | Cumple | Selectores de año/mes y año actual por defecto en pruebas de componente. |
| AC-003 | Cumple | Cuatro columnas con asignado, arrastre, disponible, gastado y restante. |
| AC-004 | Cumple | Vista anual con arrastre y disponible. |
| AC-005 | Cumple | Upsert independiente por mes en pruebas de integración. |
| AC-006 | Cumple | Monto sin asignar y validación de suma. |
| AC-007 | Cumple | Suma mayor que 100 devuelve `422`. |
| AC-008 | Cumple | Restante negativo en cálculo y componente. |
| AC-009 | Cumple | Gastos `INVERSION` en pruebas de integración. |
| AC-010 | Cumple | Porcentaje anual ponderado en cálculo y API. |
| AC-011 | Cumple | Periodos disponibles con año actual y años con datos. |
| AC-012 | Cumple | Rutas y schemas en OpenAPI. |
| AC-013 | Cumple | Carga, error, vacío, validación y guardado en componentes. |
| AC-014 | Cumple | Suites completas y smoke de producción. |
| AC-015 | Cumple | Arrastre positivo de necesarios a no necesarios. |
| AC-016 | Cumple | Arrastre negativo reduce el disponible siguiente. |
| AC-017 | Cumple | No necesarios e inversión se arrastran de forma independiente. |
| AC-018 | Cumple | Diciembre pasa a enero sin reinicio. |
| AC-019 | Cumple | Recálculo dinámico al cambiar una asignación anterior. |
| AC-020 | Cumple | Tabla anual con Asignado, Arrastre, Disponible, Gastado y Restante. |

## Notas

- T-001 a T-015 están completadas; la especificación queda validada.
- No se modifica `legacy/`.
- No se modifican las especificaciones 001 a 007.
- No se añaden dependencias nuevas.
- La migración nueva es `0007`; la versión esperada de la base de test se actualiza en T-001/T-009.
- Los montos asignados no se almacenan; se recalculan al consultar.
- La vista mensual usa cuatro columnas con fecha, descripción y valor; la vista anual es una tabla agregada.
- La vista anual usa el año actual por defecto y el mes `Todos`.
- El arrastre no se almacena: se calcula desde el primer mes con datos.
- La revisión 3 se publicará como versión 1.1.0.
