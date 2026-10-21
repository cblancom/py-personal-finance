# Tareas 005 — Interfaz MVP

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-003 ──► T-004 ──► T-005 ──► T-006 ──► T-007
```

T-003 y T-004 pueden ejecutarse en paralelo después de T-002; el orden mostrado es el recomendado para avanzar de forma secuencial.

## Tareas

- [x] **T-001 — Ampliar tipos y cliente API**
  - Requisitos: FR-015, NFR-001, NFR-003, NFR-004.
  - Dependencias: ninguna.
  - Descripción: crear tipos de ingreso, gasto y resumen; crear `api/incomes.ts`, `api/expenses.ts` y `api/summary.ts`; actualizar `api/client.ts` para manejar `204` y errores. Añadir pruebas del cliente con `fetch` simulado.
  - Hecho cuando: las funciones usan las rutas y métodos correctos; envían JSON en `POST`/`PUT`; `DELETE` con `204` no intenta parsear JSON; los errores producen `ApiError`; lint, typecheck y tests pasan.
  - Evidencia (2026-10-21): tipos de ingreso, gasto y resumen; módulos API con rutas `/api/ingresos`, `/api/gastos` y `/api/resumen`; `request` maneja `204` sin parsear JSON; 13 pruebas nuevas del cliente (20 en total); lint, typecheck, test y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run lint
    npm run typecheck
    npm run test
    ```

- [x] **T-002 — Crear formateadores y panel de resumen**
  - Requisitos: FR-003, FR-010, NFR-004.
  - Dependencias: T-001.
  - Descripción: crear `utils/format.ts` con formato de importes, fechas y etiquetas de tipo; crear `SummaryPanel` con totales, balance y desglose. Añadir pruebas.
  - Hecho cuando: importes en formato `es-CO` con dos decimales y sin símbolo; fechas sin desplazamiento de día; tipos con etiquetas en español; balance negativo y ceros visibles; pruebas pasan.
  - Evidencia (2026-10-21): `formatMoney` usa `es-CO` con dos decimales; `formatDate` evita desplazamiento de día; etiquetas `Necesario`, `No necesario`, `Inversión`; `SummaryPanel` muestra totales, balance, desglose y marca balance negativo. 9 pruebas nuevas (29 en total); lint, typecheck, test y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [ ] **T-003 — Implementar la sección de ingresos**
  - Requisitos: FR-004, FR-006, FR-007, FR-008, FR-011, NFR-004, NFR-006.
  - Dependencias: T-002.
  - Descripción: crear `IncomeForm`, `IncomeList` e `IncomeSection`; permitir crear, editar y eliminar ingresos, con confirmación y validación local. Notificar los cambios a `App`.
  - Hecho cuando: se crea un ingreso; se edita con `PUT`; se elimina con confirmación y `DELETE`; cancelar edición no modifica datos; errores y envío doble se manejan; pruebas pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [ ] **T-004 — Implementar la sección de gastos**
  - Requisitos: FR-005, FR-006, FR-007, FR-008, FR-011, NFR-004, NFR-006.
  - Dependencias: T-002.
  - Descripción: crear `ExpenseForm`, `ExpenseList` y `ExpenseSection`; incluir selector de tipo, crear, editar y eliminar con confirmación y validación local. Notificar los cambios a `App`.
  - Hecho cuando: se crean gastos de los tres tipos; se edita el tipo y los demás campos; se elimina con confirmación; errores y envío doble se manejan; pruebas pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    ```

- [ ] **T-005 — Integrar la aplicación, pestañas y refresco**
  - Requisitos: FR-001, FR-002, FR-009, FR-012, FR-016, NFR-005, NFR-006, NFR-007.
  - Dependencias: T-003, T-004.
  - Descripción: reescribir `App` para cargar resumen, ingresos y gastos, mostrar pestañas, estados de carga/error/vacío y recargar datos tras mutaciones. Eliminar `ApiStatus`, `api/health.ts`, `types/health.ts` y sus pruebas si quedan sin uso. Reescribir `App.test.tsx`.
  - Hecho cuando: la app carga los tres recursos; las pestañas funcionan; el resumen se actualiza tras crear/editar/eliminar; los errores de carga permiten reintentar; no queda código muerto de salud; pruebas pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    ```

- [ ] **T-006 — Estilos, responsive y accesibilidad**
  - Requisitos: FR-013, FR-014.
  - Dependencias: T-005.
  - Descripción: estilizar formularios, tarjetas, pestañas, listados, estados y errores. Asegurar etiquetas, roles, foco visible, contraste y layout móvil. Añadir/ajustar pruebas de roles y atributos accesibles.
  - Hecho cuando: la interfaz se adapta a escritorio/móvil; no hay desbordes horizontales; los campos tienen etiquetas; pestañas y errores son accesibles; pruebas y build pasan.
  - Verificación:
    ```bash
    cd frontend
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```

- [ ] **T-007 — Documentar y validar la interfaz**
  - Requisitos: FR-015, NFR-002, NFR-008, AC-013, AC-014.
  - Dependencias: T-006.
  - Descripción: actualizar README, AGENTS y `specs/README.md` con la interfaz, el flujo de uso y el estado. Ejecutar la validación completa de frontend, backend y Docker, y registrar la evidencia.
  - Hecho cuando: `lint`, `typecheck`, `test` y `build` pasan; el backend sigue pasando; `docker compose up --build` deja los servicios saludables; la interfaz carga y la documentación refleja el estado; la spec queda validada.
  - Verificación:
    ```bash
    docker compose config -q
    docker compose up --build -d
    (cd frontend && npm run lint && npm run typecheck && npm run test && npm run build)
    (cd backend && uv run pytest && uv run ruff check . && uv run ruff format --check .)
    docker compose exec api uv run pytest
    curl -I http://localhost:3001/
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-005, T-006 |
| FR-002 | T-005 |
| FR-003 | T-002 |
| FR-004 | T-003 |
| FR-005 | T-004 |
| FR-006 | T-003, T-004 |
| FR-007 | T-003, T-004 |
| FR-008 | T-003, T-004 |
| FR-009 | T-005 |
| FR-010 | T-002 |
| FR-011 | T-003, T-004 |
| FR-012 | T-005 |
| FR-013 | T-006 |
| FR-014 | T-006 |
| FR-015 | T-001 a T-007 |
| FR-016 | T-005 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-001 a T-006 |
| NFR-002 | T-007 |
| NFR-003 | T-001 |
| NFR-004 | T-001 a T-006 |
| NFR-005 | T-005 |
| NFR-006 | T-003, T-004, T-005 |
| NFR-007 | T-005 |
| NFR-008 | T-007 |

## Evidencia de validación

Se completa durante T-007.

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
| AC-013 | Pendiente | |
| AC-014 | Pendiente | |

## Notas

- No se modifican los contratos del backend.
- No se añaden dependencias nuevas.
- No se implementan pruebas E2E de navegador; la validación de Docker se cubre en la especificación 006.
- No se implementa filtro mensual, autenticación ni gráficos.
- Los importes se mantienen como strings; la UI no realiza cálculos financieros.
- El estado técnico de `/api/health` se elimina de la interfaz; el endpoint permanece en el backend.
