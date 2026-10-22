---
name: frontend-feature
description: Implementa vistas, secciones, formularios o flujos del frontend React de Py Personal Finance con tipos, cliente API, estado, validación, pruebas Vitest y accesibilidad. Úsala para conectar endpoints o añadir UI.
---

# Skill: Frontend feature

## Propósito

Guía la implementación de una funcionalidad del frontend respetando el patrón ya usado por ingresos, gastos, resumen y la integración de `App`.

Esta skill cubre implementación, estado, API, pruebas y accesibilidad. Para dirección visual o rediseño estético, usa además `frontend-design` si está disponible.

El flujo de especificación, plan y tareas sigue gobernado por `spec-driven-development`.

## Cuándo usarla

Actívala cuando la tarea implique:

- Añadir una pantalla, pestaña, sección o formulario.
- Conectar un endpoint con React.
- Crear tipos o módulos del cliente API.
- Añadir estados de carga, error, vacío o edición.
- Añadir pruebas de componentes o de integración del frontend.

## Reglas no negociables

- La interfaz se escribe en español; el código interno en inglés.
- No añadir router, librería de estado global, librería de formularios ni dependencias nuevas sin justificación aprobada.
- Usar rutas relativas `/api`; no hardcodear `http://localhost:8000` en componentes.
- No habilitar CORS.
- Los importes de la API son strings. La UI no realiza cálculos financieros.
- Mostrar dinero con `formatMoney` (COP, `es-CO`).
- Las fechas de lista se muestran con `formatDate`; la fecha por defecto de un formulario nuevo es `todayIsoDate`.
- Los campos deben tener etiquetas asociadas.
- Los errores deben ser visibles y accesibles, sin detalles técnicos.
- Mantener el sistema visual existente; no reescribir `index.css` sin necesidad.
- No tocar `legacy/`.

## Lectura previa obligatoria

Antes de escribir código:

1. Lee `constitution.md`, `AGENTS.md` y la especificación, plan y tarea correspondientes.
2. Inspecciona el patrón más cercano:
   - `frontend/src/components/IncomeSection.tsx`
   - `frontend/src/components/ExpenseSection.tsx`
   - `frontend/src/components/IncomeForm.tsx`
   - `frontend/src/components/ExpenseForm.tsx`
   - `frontend/src/components/IncomeList.tsx`
   - `frontend/src/components/ExpenseList.tsx`
   - `frontend/src/App.tsx`
3. Revisa `frontend/src/api/client.ts`, los módulos API y sus pruebas.
4. Revisa `frontend/src/utils/format.ts`, `validation.ts` y sus pruebas.
5. Revisa `frontend/src/index.css` y los tests de componentes.
6. Confirma el contrato de la API antes de inventar campos o estados.

## Flujo de implementación

### 1. Definir tipos

Ubicación: `frontend/src/types/`.

- Los campos conservan los nombres del contrato en español.
- Define la entidad (`id` incluido) y el payload sin `id`.
- Usa `Omit` si el patrón lo permite.
- No inventes campos que la API no devuelve.

### 2. Crear el módulo API

Ubicación: `frontend/src/api/<resource>.ts`.

Usa `request` de `client.ts`:

- `list...` acepta `AbortSignal` cuando se usa en carga inicial.
- `create...` usa `POST` y envía JSON.
- `update...` usa `PUT` con el objeto completo.
- `delete...` usa `DELETE`; `client.ts` ya maneja `204`.
- Las rutas son relativas a `/api`.
- Añade pruebas con `fetch` simulado, siguiendo los módulos existentes.

No añadas manejo de errores duplicado en cada módulo; `request` ya lanza `ApiError`.

### 3. Reutilizar utilidades

Antes de crear una utilidad nueva:

- Revisa `formatMoney`, `formatDate`, `todayIsoDate`, `expenseTypeLabel`.
- Revisa `validateMovementInput`.
- Si la lógica es compartida y pura, créala en `utils/` y pruébala aparte.
- No dupliques validación entre formularios.

### 4. Componer la sección

Sigue la separación actual:

#### Sección

Responsabilidades:

- Mantener `editing...`, `submitting`, `error` y una versión de formulario.
- Crear, editar y eliminar mediante el módulo API.
- Pedir confirmación con `window.confirm` antes de eliminar.
- Llamar a `onChanged()` después de una mutación exitosa.
- Pasar `key` al formulario para reiniciarlo tras guardar o cancelar.
- Mostrar errores de sección en un `role="alert"`.

No mover el estado global de `App` a la sección.

#### Formulario

Responsabilidades:

- Campos controlados.
- Validación local antes de enviar.
- Recorte de descripción antes de enviar.
- Modo creación y edición con el mismo componente.
- Botón deshabilitado y texto “Guardando...” durante el envío.
- Botón de cancelar edición cuando aplique.
- Etiquetas con `htmlFor` e `id` únicos.
- Error en `role="alert"`.

#### Listado

Responsabilidades:

- Renderizar tabla y estado vacío.
- Mostrar fecha, descripción, tipo si aplica y valor formateado.
- Acciones con `aria-label` que incluyan el recurso y la descripción.
- No gestionar estado de edición ni llamadas API.

### 5. Integrar en `App`

`App` es dueña de:

- Carga inicial en paralelo.
- `summary`, listas, pestaña activa, `loading`, `error` y `loadVersion`.
- Recarga mediante `reloadData`.
- Pestañas con `role="tablist"`, `role="tab"`, `aria-selected` y panel con `role="tabpanel"`.
- Estados de carga, error con reintento y refresco.
- No duplicar las llamadas API dentro de los componentes presentacionales.

Si la funcionalidad no necesita una pestaña nueva, intégrala sin romper las existentes.

### 6. Estilos y accesibilidad

- Reutiliza clases existentes: `movement-section`, `movement-form`, `field`, `button`, `movement-list`, `movement-table`, `form-error`, etc.
- Añade clases nuevas solo si representan una estructura nueva.
- Mantén el sistema de tokens de `:root`.
- No introduzcas tarjetas redondeadas, sombras o gradientes genéricos.
- Asegura foco visible, contraste y `prefers-reduced-motion`.
- Las tablas deben tener un contenedor con `overflow-x: auto` para móvil.
- No dependas solo del color para errores o balance negativo.
- Verifica etiquetas, roles y navegación por teclado.

Para decisiones visuales nuevas, usa `frontend-design`; no improvises una identidad visual desde esta skill.

### 7. Pruebas

Sigue el patrón de Vitest + Testing Library.

#### Cliente API

- Simula `fetch`.
- Comprueba ruta, método, cabeceras, cuerpo y manejo de `204`.
- Comprueba errores con `ApiError`.

#### Formulario

- Envío válido y descripción recortada.
- Errores de fecha, descripción, valor, decimales y dígitos.
- Modo edición con valores iniciales.
- Cancelar edición.
- Botón deshabilitado durante el envío.

#### Listado

- Renderizado de datos.
- Estado vacío.
- Acciones de editar y eliminar.

#### Sección

- Crear y llamar a `onChanged`.
- Editar y llamar a `onChanged`.
- Eliminar solo tras confirmación.
- Cancelar eliminación sin llamar a la API.
- Mostrar error de API sin perder datos.

#### App

- Carga inicial de resumen y listas.
- Pestañas y `aria-selected`.
- Recarga tras mutación.
- Error inicial con reintento.
- Estado de carga.

#### Importes COP en pruebas

`formatMoney` usa `Intl.NumberFormat` con moneda COP y espacio no separable. Testing Library normaliza ese espacio:

- En `format.test.ts`, verifica el string crudo con `\u00A0`.
- En pruebas de componentes, usa un espacio normal: `$ 1.500,50`.
- No uses `getByText` con NBSP explícito en RTL salvo que sepas que no se normaliza.

### 8. Verificación

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

Si el cambio afecta la entrega de producción, valida también el smoke test con el stack correspondiente.

## Checklist de salida

- [ ] Tipos alineados con el contrato.
- [ ] Módulo API con pruebas.
- [ ] Formulario accesible y validado.
- [ ] Listado con estado vacío y acciones accesibles.
- [ ] Sección que crea, edita, elimina y refresca.
- [ ] Integración en `App` sin duplicar estado.
- [ ] Estilos reutilizados y responsive.
- [ ] Sin URLs absolutas de API.
- [ ] Sin dependencias nuevas.
- [ ] Pruebas de cliente, componentes y App.
- [ ] Lint, typecheck, test y build pasan.

## Errores frecuentes

- Hardcodear `http://localhost:8000`.
- Usar `number` o `parseFloat` para dinero.
- Mostrar importes sin `formatMoney`.
- Olvidar `onChanged` tras crear, editar o eliminar.
- No reiniciar el formulario tras guardar.
- Duplicar el estado de edición en `App` y en la sección.
- Eliminar sin confirmación.
- Usar etiquetas sin `htmlFor`/`id`.
- Usar `getByText` con NBSP en pruebas de componentes.
- Añadir un router o una librería de estado para una sola pantalla.
- Romper el layout móvil con una tabla sin overflow controlado.

## Límites

- No cambies el contrato de la API desde el frontend.
- Si falta un campo o un comportamiento, vuelve a la especificación.
- Si la tarea requiere una dirección visual nueva, carga `frontend-design` si está disponible.
- Si la tarea requiere una nueva migración o endpoint, usa también `backend-resource`.
