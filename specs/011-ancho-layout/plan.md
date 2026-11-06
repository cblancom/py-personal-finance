# Plan técnico 011 — Ajuste de ancho y layout responsive

- Estado: validado (T-001 a T-004 completadas).
- Especificación: [`spec.md`](spec.md).
- Fase: 9.
- Iteración: 1.2.1.

## 1. Resumen de la solución

La corrección se implementa únicamente en `frontend/src/index.css`.

Incluye:

- Aumentar el ancho máximo de `main` de `1080px` a `1440px`.
- Reducir el padding lateral del contenedor global.
- Reducir el espacio interno y el ancho mínimo de las tablas del balance mensual.
- Mover el breakpoint de cuatro a dos columnas de `900px` a `1100px`.
- Mantener el scroll horizontal como respaldo únicamente en pantallas estrechas.

No se modifican componentes React, APIs, datos, migraciones ni dependencias.

## 2. Diagnóstico técnico

Estado actual:

```text
main max-width: 1080px
padding horizontal: 3.5rem izquierda + 2rem derecha
contenido útil: ~992px

.balance-columns: 4 columnas, gap 1rem
ancho por columna: ~236px
padding por columna: 1rem izquierda + 1rem derecha
ancho interno: ~204px

.balance-table min-width: 15rem = 240px
desbordamiento por columna: ~36px
```

Consecuencias:

- Cada tabla mensual genera scroll horizontal dentro de `.balance-column__table-wrap`.
- En monitores grandes, el contenedor deja márgenes laterales muy amplios.
- El breakpoint de `900px` no evita el scroll entre `901px` y el ancho necesario para cuatro columnas.

## 3. Cambios CSS propuestos

### 3.1 Contenedor principal

```css
main {
  max-width: 1440px;
  margin: 0 auto;
  padding: 3rem clamp(1.25rem, 2vw, 2rem) 5rem clamp(2rem, 3vw, 3rem);
}
```

- Mantener `box-sizing: border-box` global.
- Mantener el contenido centrado.
- Ajustar la línea decorativa:

```css
main::before {
  left: clamp(0.75rem, 1.5vw, 1.25rem);
}
```

En el breakpoint móvil se conserva el ajuste existente de `padding` y `left`.

### 3.2 Columnas del balance

```css
.balance-columns {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
  align-items: start;
}

.balance-column {
  min-width: 0;
  padding: 0 0.75rem;
  border-left: 1px solid var(--rule);
}

.balance-column:first-child {
  padding-left: 0;
  border-left: 0;
}
```

### 3.3 Tabla mensual

```css
.balance-table {
  width: 100%;
  min-width: 13rem;
  border-collapse: collapse;
  font-size: 0.82rem;
  font-variant-numeric: tabular-nums;
}
```

Se mantiene:

- `white-space: nowrap` en `.balance-table .amount`.
- La descripción sin `nowrap`, para que pueda envolver.
- `overflow-x: auto` en `.balance-column__table-wrap` como respaldo móvil.

### 3.4 Breakpoints

```css
@media (max-width: 1100px) {
  .balance-columns {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1.5rem 1rem;
  }

  .balance-column:nth-child(3) {
    padding-left: 0;
    border-left: 0;
  }
}
```

El bloque de una columna se mantiene en `max-width: 720px`.

Comportamiento esperado:

| Ancho | Columnas |
|---|---|
| `> 1100px` | 4 |
| `720px–1100px` | 2 |
| `< 720px` | 1 |

## 4. Archivos afectados

| Archivo | Cambio |
|---|---|
| `frontend/src/index.css` | Ancho global, padding, columnas, tabla y breakpoints. |
| `specs/011-ancho-layout/tasks.md` | Evidencia de implementación y validación. |
| `specs/011-ancho-layout/spec.md` | Estado y resultado de validación. |
| `specs/README.md` | Estado de la especificación. |
| `AGENTS.md` | Estado del proyecto cuando la spec esté validada. |

No se modifica `frontend/src/App.tsx` ni ningún componente.

## 5. Verificación visual

Revisar en DevTools con estos anchos:

| Ancho | Comprobación |
|---|---|
| `375px` | Una columna; scroll horizontal solo si es necesario. |
| `768px` | Dos columnas; sin solapamientos. |
| `1024px` | Dos columnas; sin scroll horizontal en el balance. |
| `1280px` | Cuatro columnas; sin scroll horizontal. |
| `1440px` | Cuatro columnas; contenido centrado. |
| `1920px` | Cuatro columnas; márgenes laterales reducidos. |

Comprobar además:

- Descripciones largas envueltas sin desbordar.
- Valores monetarios completos y alineados.
- Línea decorativa alineada.
- Balance anual sin regresiones.
- Gráfica y formularios sin estiramientos incómodos.
- Foco visible y navegación por teclado.

## 6. Verificación automatizada

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

No se añaden pruebas visuales automatizadas. La corrección se valida con las suites existentes y revisión manual responsive.

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Formularios o gráfica demasiado estirados | Mantener sus `max-width` existentes y revisar visualmente. |
| Descripciones que envuelven demasiado | Mantener `min-width: 13rem` y revisar con textos largos. |
| Línea decorativa desalineada | Ajustar `main::before` junto con el padding. |
| Scroll horizontal persistente en portátiles | Cambiar el breakpoint a `1100px`. |
| Regresión en móvil | Conservar el layout de una columna y el scroll de respaldo. |

## 8. Aprobación y siguiente paso

La especificación 011 está aprobada. El plan fue aprobado y T-001 a T-004 quedaron completadas y validadas.

No se modifica `legacy/`. No se añaden dependencias. No se toca el backend.
