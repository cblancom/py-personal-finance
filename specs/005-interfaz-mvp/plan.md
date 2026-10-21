# Plan técnico 005 — Interfaz MVP

- Estado: aprobado.
- Especificación: [`spec.md`](spec.md).
- Fase: 3.
- Iteración: MVP.

## 1. Resumen de la solución

La interfaz se construye sobre el frontend existente de React + TypeScript + Vite, sin añadir dependencias.

La pantalla tendrá:

- Encabezado.
- Panel de resumen global.
- Pestañas Ingresos y Gastos.
- Formulario y listado de la pestaña activa.

El frontend consumirá las APIs existentes:

- `GET/POST/PUT/DELETE /api/ingresos`
- `GET/POST/PUT/DELETE /api/gastos`
- `GET /api/resumen`

Los importes se reciben como strings y se formatean solo para presentación. Los cálculos financieros siguen en el backend.

## 2. Arquitectura y flujo de datos

```text
App
 ├── carga inicial: resumen + ingresos + gastos
 ├── SummaryPanel
 ├── tabs Ingresos / Gastos
 ├── IncomeSection
 │    ├── IncomeForm
 │    └── IncomeList
 └── ExpenseSection
      ├── ExpenseForm
      └── ExpenseList

App → api/*.ts → fetch → FastAPI → PostgreSQL
```

Flujo de carga:

1. `App` solicita resumen, ingresos y gastos en paralelo.
2. Mientras espera, muestra el estado de carga.
3. Si todo responde, renderiza el resumen, las pestañas y la lista activa.
4. Si falla alguna petición, muestra un banner de error y permite reintentar.

Flujo de mutación:

1. El formulario valida localmente.
2. Llama al cliente API correspondiente.
3. Si la API responde correctamente, el componente notifica a `App`.
4. `App` recarga resumen, ingresos y gastos.
5. La lista y el resumen reflejan los datos persistidos.

## 3. Componentes y responsabilidades

| Ruta | Responsabilidad |
|---|---|
| `frontend/src/types/income.ts` | Tipos de ingreso y payload. |
| `frontend/src/types/expense.ts` | Tipos de gasto, payload y `ExpenseType`. |
| `frontend/src/types/summary.ts` | Tipo del resumen. |
| `frontend/src/api/incomes.ts` | Listado, creación, edición y eliminación de ingresos. |
| `frontend/src/api/expenses.ts` | Listado, creación, edición y eliminación de gastos. |
| `frontend/src/api/summary.ts` | Consulta del resumen. |
| `frontend/src/api/client.ts` | `fetch` común, `ApiError` y manejo de `204`. |
| `frontend/src/utils/format.ts` | Formato de importes, fechas y etiquetas de tipo. |
| `frontend/src/components/SummaryPanel.tsx` | Tarjetas de totales, balance y desglose. |
| `frontend/src/components/IncomeForm.tsx` | Formulario de creación/edición de ingresos. |
| `frontend/src/components/ExpenseForm.tsx` | Formulario de creación/edición de gastos. |
| `frontend/src/components/IncomeList.tsx` | Listado y acciones de ingresos. |
| `frontend/src/components/ExpenseList.tsx` | Listado y acciones de gastos. |
| `frontend/src/components/IncomeSection.tsx` | Formulario, listado y edición/eliminación de ingresos. |
| `frontend/src/components/ExpenseSection.tsx` | Formulario, listado y edición/eliminación de gastos. |
| `frontend/src/components/ErrorBanner.tsx` | Mensaje de error y acción de reintento. |
| `frontend/src/App.tsx` | Carga de datos, pestañas, estado global de la pantalla y refresco. |

Se eliminan de la interfaz los artefactos del estado técnico de salud que queden sin uso:

- `frontend/src/components/ApiStatus.tsx`
- `frontend/src/api/health.ts`
- `frontend/src/api/health.test.ts`
- `frontend/src/types/health.ts`

El endpoint `/api/health` permanece en el backend para operaciones.

## 4. Tipos y cliente API

### Tipos

```ts
export type ExpenseType = "NECESARIO" | "NO_NECESARIO" | "INVERSION";

export interface Income {
  id: number;
  fecha: string;
  descripcion: string;
  valor: string;
}

export interface Expense extends Income {
  tipo: ExpenseType;
}

export interface Summary {
  total_ingresos: string;
  total_gastos: string;
  balance: string;
  gastos_por_tipo: Record<ExpenseType, string>;
}
```

Los payloads de creación/edición omiten `id`.

### Cliente

`api/client.ts` mantendrá:

- `request<T>` con `Accept: application/json`.
- `ApiError` con el status HTTP.
- Retorno de `undefined` cuando la respuesta es `204`.
- Envío de JSON con `Content-Type: application/json` en `POST` y `PUT`.

Funciones:

```ts
listIncomes(): Promise<Income[]>
createIncome(payload: IncomePayload): Promise<Income>
updateIncome(id: number, payload: IncomePayload): Promise<Income>
deleteIncome(id: number): Promise<void>

listExpenses(): Promise<Expense[]>
createExpense(payload: ExpensePayload): Promise<Expense>
updateExpense(id: number, payload: ExpensePayload): Promise<Expense>
deleteExpense(id: number): Promise<void>

getSummary(): Promise<Summary>
```

Las rutas son relativas y usan `/api`.

## 5. Composición de la interfaz

### Encabezado

- Título `Py Personal Finance`.
- Texto breve de contexto.

### Panel de resumen

Tres tarjetas principales:

- Total ingresos.
- Total gastos.
- Balance.

Debajo, el desglose:

- Necesario.
- No necesario.
- Inversión.

El balance negativo se muestra con signo y un estilo que no depende solo del color.

### Pestañas

Dos pestañas: `Ingresos` y `Gastos`.

- `role="tablist"` en el contenedor.
- `role="tab"` y `aria-selected` en cada botón.
- El panel activo usa `role="tabpanel"`.
- Solo se monta el formulario/listado activo.

### Formularios

Ingreso:

- Fecha (`type="date"`, por defecto hoy local).
- Descripción (`input` o `textarea`, máximo 200).
- Valor (`type="number"`, `step="0.01"`, `min="0.01"`).
- Botón Guardar.

Gasto: los mismos campos más un `select` de tipo.

Modo edición:

- El formulario se rellena con el movimiento seleccionado.
- El botón principal cambia a `Guardar cambios`.
- Aparece `Cancelar edición`.
- Al guardar o cancelar se vuelve al modo creación.

### Listados

Cada fila muestra:

- Fecha formateada.
- Descripción.
- Tipo (solo gastos).
- Valor formateado.
- Botones Editar y Eliminar.

Los botones tienen texto y `aria-label` cuando el contexto no es suficiente.

### Eliminación

Se usa `window.confirm` para confirmar. Si el usuario cancela, no se llama a la API.

## 6. Estado y flujo de React

`App` mantiene:

- `summary`.
- `incomes`.
- `expenses`.
- `activeTab`.
- `loading`.
- `error`.

`IncomeSection` y `ExpenseSection` mantienen:

- Movimiento en edición.
- Valores del formulario.
- Error de formulario.
- Estado de envío.

`App` expone una función `reloadData` que recarga resumen, ingresos y gastos. Las secciones la llaman después de una mutación exitosa.

No se usa Context, Redux, Zustand ni router.

## 7. Formato y validación

### Formato

`utils/format.ts`:

- `formatMoney(value: string)`: `Intl.NumberFormat("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 })`. Sin símbolo de moneda.
- `formatDate(value: string)`: fecha local sin desplazar el día; se evita interpretar `YYYY-MM-DD` como UTC.
- `expenseTypeLabel(type)`: `Necesario`, `No necesario`, `Inversión`.

### Validación de cliente

- Fecha obligatoria.
- Descripción recortada, entre 1 y 200 caracteres.
- Valor numérico mayor que 0 y con máximo 2 decimales.
- Tipo obligatorio en gastos.

La validación del servidor sigue siendo la fuente de verdad. Un `422` se muestra como un mensaje general para revisar los datos.

## 8. Errores y estados

- Error de carga inicial: banner con `role="alert"` y botón Reintentar.
- Error de mutación: mensaje dentro de la sección activa; el formulario conserva los datos.
- Error `404`: mensaje de que el movimiento ya no existe y recarga de datos.
- Lista vacía: mensaje específico para ingresos o gastos.
- Carga: texto visible y botones de envío deshabilitados.
- Envío doble: el botón se deshabilita mientras la promesa está pendiente.

No se muestran mensajes técnicos ni cuerpos de error del backend.

## 9. Accesibilidad y responsive

- Cada campo tiene `<label>` asociado.
- Errores en regiones `aria-live` o `role="alert"`.
- Foco visible.
- Pestañas con roles y `aria-selected`.
- Contraste suficiente.
- El balance y los estados no dependen solo del color.
- CSS con grid/flex; tarjetas apiladas en móvil.
- Tablas o listas con `overflow` controlado para no romper el layout.
- Botones con área táctil suficiente.

## 10. Estrategia de pruebas

### Cliente API

- Rutas y métodos de ingresos/gastos.
- Envío de `Content-Type` y cuerpo JSON.
- `DELETE` con `204` no intenta parsear JSON.
- Errores HTTP producen `ApiError`.
- Resumen.

### Componentes

- `SummaryPanel`: valores, desglose, balance negativo.
- `IncomeForm`/`ExpenseForm`: creación, edición, validación, cancelación.
- `IncomeList`/`ExpenseList`: renderizado, edición, eliminación y confirmación.
- `App`: carga, pestañas, estados de error/vacío, refresco tras mutación.

Se simulan los módulos de API con Vitest. No se requiere backend en ejecución.

### Comandos

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| `DELETE 204` intenta hacer `response.json()`. | Manejar `204` en `request` y devolver `undefined`. |
| Desplazamiento de fecha por zona horaria. | Formatear la fecha ISO sin convertirla desde UTC. |
| Enviar importes como número y perder precisión. | Mantener strings en el estado y en el payload. |
| Resumen desactualizado tras una mutación. | Recargar resumen y listas después de cada operación. |
| La recarga falla después de una mutación exitosa. | Mostrar error y no afirmar que los totales están actualizados. |
| Mensajes `422` poco claros. | Mensaje general en español que invita a revisar los datos. |
| Eliminar el estado de salud rompe pruebas existentes. | Reemplazar las pruebas de salud por pruebas de la interfaz y eliminar código sin uso. |
| Listas largas sin paginación. | Aceptado para el MVP; el volumen esperado es pequeño. |
| Mocks de API divergen del contrato. | Tipos compartidos y pruebas del cliente API. |
| Layout roto en móvil. | CSS responsive y revisión visual. |

## 12. Trazabilidad requisitos → plan

| Requisito | Sección del plan | Tareas |
|---|---|---|
| FR-001 | 5 | T-005, T-006 |
| FR-002 | 2, 6 | T-005 |
| FR-003 | 5, 7 | T-002 |
| FR-004 | 5, 7 | T-003 |
| FR-005 | 5, 7 | T-004 |
| FR-006 | 5 | T-003, T-004 |
| FR-007 | 5, 6 | T-003, T-004 |
| FR-008 | 5, 6 | T-003, T-004 |
| FR-009 | 2, 6 | T-005 |
| FR-010 | 7 | T-002 |
| FR-011 | 7, 8 | T-003, T-004 |
| FR-012 | 8 | T-005 |
| FR-013 | 9 | T-006 |
| FR-014 | 9 | T-006 |
| FR-015 | 10 | T-001 a T-007 |
| FR-016 | 3, 8 | T-005 |
| NFR-001 | 1, 3 | T-001 a T-006 |
| NFR-002 | 10 | T-007 |
| NFR-003 | 4 | T-001 |
| NFR-004 | 3, 5 | T-001 a T-006 |
| NFR-005 | 6 | T-005 |
| NFR-006 | 6, 8 | T-003, T-004, T-005 |
| NFR-007 | 8 | T-005 |
| NFR-008 | 10 | T-007 |

## 13. Aprobación y siguiente paso

Este plan fue aprobado junto con `tasks.md`.

La implementación comienza por `T-001` y avanza en el orden de dependencias de `tasks.md`.
