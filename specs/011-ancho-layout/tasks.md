# Tareas 011 — Ajuste de ancho y layout responsive

- Estado: validada (T-001 a T-004 completadas).
- Especificación: [`spec.md`](spec.md).
- Plan: [`plan.md`](plan.md).

## Orden de ejecución

```text
T-001 ──► T-002 ──► T-003 ──► T-004
```

T-001 ajusta el contenedor global. T-002 ajusta las columnas y la tabla del balance. T-003 actualiza los breakpoints. T-004 valida el resultado responsive y actualiza la evidencia.

La especificación 011 está aprobada. El plan fue aprobado y T-001 a T-004 están completadas; la especificación queda validada.

## Tareas

- [x] **T-001 — Ampliar el contenedor global y ajustar la línea decorativa**
  - Requisitos: FR-001, FR-002, AC-001, AC-002.
  - Dependencias: ninguna.
  - Descripción: cambiar `main` a `max-width: 1440px`, reducir el padding lateral con `clamp()` y reajustar `main::before`. Mantener el contenido centrado y el ajuste móvil existente.
  - Hecho cuando: el contenido principal mide como máximo `1440px`; los márgenes laterales son menores en escritorio; la línea decorativa no se solapa con el contenido.
  - Evidencia (2026-11-05): `main` usa `max-width: 1440px` y padding lateral con `clamp()`; `main::before` quedó alineado. Revisión visual a 1440px y 1920px correcta.
  - Verificación:
    ```bash
    cd frontend
    npm run typecheck
    npm run build
    ```
    Revisión visual a `1440px` y `1920px`.

- [x] **T-002 — Reducir el espacio interno y el ancho mínimo de la tabla del balance**
  - Requisitos: FR-003, FR-004, AC-003, AC-006, AC-007.
  - Dependencias: T-001.
  - Descripción: cambiar `.balance-columns` a `gap: 0.75rem`, `.balance-column` a `padding: 0 0.75rem` y `.balance-table` a `min-width: 13rem`. Mantener `overflow-x: auto` como respaldo.
  - Hecho cuando: las cuatro columnas conservan sus bordes y alineación; la tabla mensual cabe en la columna en escritorio; las descripciones pueden envolver y los valores quedan completos.
  - Evidencia (2026-11-05): columnas con `gap: 0.75rem`, padding de `0.75rem` y tabla con `min-width: 13rem`; las descripciones envuelven y los valores se ven completos a 1280px y 1440px.
  - Verificación:
    ```bash
    cd frontend
    npm run test
    npm run build
    ```
    Revisión visual a `1280px` y `1440px` con descripciones largas.

- [x] **T-003 — Actualizar los breakpoints responsive**
  - Requisitos: FR-005, FR-006, AC-003, AC-004, AC-005, AC-006.
  - Dependencias: T-002.
  - Descripción: sustituir el breakpoint de dos columnas de `900px` por `1100px`; mantener una columna por debajo de `720px`; conservar el scroll horizontal de respaldo en pantallas estrechas.
  - Hecho cuando: a `1280px` se ven cuatro columnas, a `1024px` dos y a `375px` una; no hay scroll horizontal en el balance de escritorio.
  - Evidencia (2026-11-05): breakpoint de dos columnas movido a `1100px`; revisión visual a 375px, 1024px, 1280px, 1440px y 1920px correcta.
  - Verificación:
    Revisión visual a `375px`, `768px`, `1024px`, `1280px`, `1440px` y `1920px`.

- [x] **T-004 — Validar, documentar y registrar evidencia**
  - Requisitos: FR-007, FR-008, AC-008, AC-009, NFR-001 a NFR-005.
  - Dependencias: T-001 a T-003.
  - Descripción: ejecutar lint, typecheck, pruebas y build; revisar que balance anual, gráfica y formularios no tengan regresiones; actualizar la evidencia, el estado de la spec y `AGENTS.md` si corresponde.
  - Hecho cuando: las suites pasan; la revisión visual no muestra desbordes ni solapamientos; el diff se limita a CSS y documentación; la spec queda validada.
  - Evidencia (2026-11-05): 100/100 pruebas frontend; lint, typecheck y build OK; revisión visual sin desbordes en 375px, 1024px, 1280px, 1440px y 1920px. El diff de implementación se limita a `frontend/src/index.css`.
  - Verificación:
    ```bash
    cd frontend
    npm run lint
    npm run typecheck
    npm run test
    npm run build
    ```

## Matriz de cobertura

### Requisitos funcionales

| Requisito | Tareas |
|---|---|
| FR-001 | T-001 |
| FR-002 | T-001 |
| FR-003 | T-002 |
| FR-004 | T-002 |
| FR-005 | T-003 |
| FR-006 | T-003 |
| FR-007 | T-004 |
| FR-008 | T-004 |

### Requisitos no funcionales

| Requisito | Tareas |
|---|---|
| NFR-001 | T-003, T-004 |
| NFR-002 | T-002, T-004 |
| NFR-003 | T-004 |
| NFR-004 | T-001 a T-004 |
| NFR-005 | T-004 |

## Evidencia de validación

| Criterio | Resultado | Evidencia |
|---|---|---|
| AC-001 | Cumple | `main` con `max-width: 1440px` y centrado. |
| AC-002 | Cumple | Padding lateral reducido; línea decorativa alineada. |
| AC-003 | Cumple | Cuatro columnas desde 1101px; revisión a 1280px y 1440px. |
| AC-004 | Cumple | Dos columnas a 1024px. |
| AC-005 | Cumple | Una columna a 375px. |
| AC-006 | Cumple | Sin scroll horizontal en balance de escritorio. |
| AC-007 | Cumple | Descripciones y valores visibles con textos largos. |
| AC-008 | Cumple | 100/100 pruebas frontend y revisión de vistas principales. |
| AC-009 | Cumple | Implementación limitada a CSS y documentación. |

## Notas

- La implementación se limita a `frontend/src/index.css`.
- No se modifican componentes, API, datos ni migraciones.
- No se añaden dependencias.
- No se modifican las specs 005 ni 008.
- La iteración de la especificación es `1.2.1`; no se modificaron metadatos de versión en esta corrección.
