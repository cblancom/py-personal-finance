# Especificación 010 — Tipo opcional de ingresos

- Estado: validada.
- Fase: 8.
- Iteración: 1.2.
- Dependencias: `specs/002-api-ingresos/`, `specs/003-api-gastos/`, `specs/007-importacion-movimientos/`, `specs/008-balance-mensual/`.
- Plan: `plan.md` (aprobado; T-001 a T-008 completadas).
- Tareas: `tasks.md` (T-001 a T-008 completadas).

## 1. Contexto y problema

Los ingresos tienen hoy un campo opcional `categoria` de texto libre. Ese campo no participa en el balance: todos los ingresos se suman y luego se reparten entre los rubros según los porcentajes mensuales.

El usuario necesita clasificar opcionalmente un ingreso con el mismo tipo que los gastos (`NECESARIO`, `NO_NECESARIO` o `INVERSION`). Cuando un ingreso tiene tipo, no debe repartirse por porcentajes: debe sumarse directamente al disponible del rubro correspondiente en el mes del ingreso. Cuando no tiene tipo, el comportamiento actual debe permanecer intacto.

La categoría libre no aporta al cálculo financiero y complica la distinción entre “categoría” y “tipo”. Esta especificación la reemplaza por `tipo`, aunque ello implique una migración destructiva de los valores históricos de `categoria`.

## 2. Relación con especificaciones existentes

- **002-api-ingresos:** el contrato de ingresos cambia de `categoria` a `tipo`. Las demás reglas de fecha, descripción, valor, orden y errores se mantienen.
- **003-api-gastos:** se reutilizan los mismos valores de tipo y su validación. No se modifica el contrato de gastos.
- **007-importacion-movimientos:** la decisión D-002 sobre categoría libre de ingresos queda sustituida. En la importación de ingresos, `Categoría`/`Tipo` se interpreta como tipo opcional; un valor desconocido deja la fila pendiente. El texto original se conserva en `filas_importacion.categoria` para auditoría.
- **008-balance-mensual:** se extienden los cálculos y el contrato de rubros para incorporar ingresos tipados. Las reglas de arrastre de la revisión 3 se mantienen.
- **009-graficas-gastos:** no se modifica. Las gráficas siguen mostrando solo gastos.

Esta especificación es la fuente de verdad para el nuevo comportamiento. No se reescriben las especificaciones históricas; las cláusulas sustituidas quedan documentadas aquí.

## 3. Usuarios y actores

- **Usuario propietario:** registra, edita e importa ingresos y consulta el balance.
- **Frontend:** ofrece el selector de tipo, muestra el tipo en el listado y presenta los ingresos tipados en el balance.
- **Backend:** valida el tipo, lo persiste y ajusta los cálculos mensuales y anuales.
- **PostgreSQL:** almacena el tipo y ejecuta las agregaciones.

No hay autenticación, roles ni multiusuario.

## 4. Historias de usuario y flujos

### US-001 — Asignar un tipo opcional a un ingreso

Como usuario, quiero indicar si un ingreso pertenece a necesarios, no necesarios o inversión, sin que el campo sea obligatorio.

**Flujo:**

1. El usuario crea o edita un ingreso.
2. Selecciona un tipo o deja la opción `Sin tipo`.
3. El sistema valida y persiste el tipo.
4. El ingreso se muestra con su tipo en el listado.

### US-002 — Mantener el comportamiento de los ingresos sin tipo

Como usuario, quiero que los ingresos sin tipo sigan repartiéndose por los porcentajes mensuales como hasta ahora.

**Flujo:**

1. El usuario registra un ingreso sin tipo.
2. El sistema lo incluye en la base porcentual del mes.
3. Los montos asignados y el monto sin asignar se calculan igual que antes.

### US-003 — Sumar un ingreso tipado al disponible

Como usuario, quiero que un ingreso con tipo se sume directamente al disponible del rubro elegido, sin repartirse por porcentajes.

**Flujo:**

1. El usuario registra un ingreso con tipo `NO_NECESARIO`.
2. El sistema excluye ese ingreso de la base porcentual.
3. El importe se suma al disponible de `NO_NECESARIO` del mes.
4. El restante y el arrastre se recalculan con ese importe.

### US-004 — Ver el efecto en el balance anual

Como usuario, quiero que la tabla anual refleje los ingresos tipados sin contar dos veces el mismo dinero.

**Flujo:**

1. El usuario consulta un año.
2. La tabla muestra el asignado base, el arrastre, los ingresos tipados, el disponible, el gastado y el restante.
3. El porcentaje ponderado se calcula sobre los ingresos sin tipo.

### US-005 — Importar ingresos tipados

Como usuario, quiero que la columna `Categoría`/`Tipo` de la importación de ingresos asigne el tipo cuando contenga un valor válido.

**Flujo:**

1. El usuario importa un archivo de ingresos.
2. Si la columna contiene `Necesario`, `No necesario` o `Inversión`, el ingreso se crea con ese tipo.
3. Si la columna está vacía, el ingreso se crea sin tipo.
4. Si la columna contiene un valor desconocido, la fila queda pendiente con un error de tipo para corregirla.

## 5. Requisitos funcionales

### FR-001 — Modelo y migración de ingresos

La tabla `ingresos` debe reemplazar la columna `categoria` por `tipo`:

- `tipo`: `VARCHAR(20)`, nullable.
- Valores permitidos: `NECESARIO`, `NO_NECESARIO`, `INVERSION` o `NULL`.
- Restricción `CHECK` que rechaza cualquier otro valor.
- No se crea un índice nuevo para `tipo`.

Debe existir una migración Alembic `0008_add_income_type`:

- `upgrade`: añade `tipo`, intenta mapear valores históricos exactos de `categoria` a los tres tipos y elimina `categoria`.
- Los valores históricos que no coincidan con un tipo se pierden.
- `downgrade`: elimina `tipo` y vuelve a crear `categoria` como `VARCHAR(100)` nullable. Los valores perdidos no se recuperan.
- La migración debe ser reversible en estructura.

**Verificación:** `alembic upgrade head`, `alembic downgrade 0007` y un nuevo `upgrade head` funcionan; la restricción rechaza valores inválidos.

### FR-002 — Contrato de ingresos

`POST /api/ingresos`, `PUT /api/ingresos/{id}`, `GET /api/ingresos` y `GET /api/ingresos/{id}` deben usar `tipo` en lugar de `categoria`.

```json
{
  "id": 1,
  "fecha": "2026-10-01",
  "descripcion": "Salario",
  "tipo": null,
  "valor": "3000.00"
}
```

Reglas:

- `tipo` es opcional.
- `tipo` acepta `null`, `NECESARIO`, `NO_NECESARIO` o `INVERSION`.
- Una cadena vacía o compuesta solo por espacios se normaliza a `null`.
- Un valor desconocido devuelve `422`.
- `categoria` deja de formar parte del contrato de ingresos.

**Verificación:** pruebas de schema, API y OpenAPI con los cuatro valores posibles.

### FR-003 — Formulario y listado de ingresos

La interfaz de ingresos debe mostrar:

- Un selector `Tipo (opcional)` con las opciones `Sin tipo`, `Necesario`, `No necesario` e `Inversión`.
- Una columna `Tipo` en el listado; los ingresos sin tipo muestran `—`.
- El tipo seleccionado al editar un ingreso existente.

**Verificación:** pruebas de `IncomeForm`, `IncomeList` y `IncomeSection`.

### FR-004 — Ingresos sin tipo

Un ingreso con `tipo = null` debe mantener el comportamiento actual:

- Se incluye en la base porcentual del mes.
- Participa en el cálculo de `asignado`.
- Puede quedar total o parcialmente en `sin_asignar`.
- Afecta el arrastre solo a través de los restantes de los rubros.

**Verificación:** las pruebas existentes de balance y de ingresos sin tipo siguen pasando.

### FR-005 — Ingresos tipados en el cálculo mensual

Para cada mes, el sistema debe separar:

```text
ingresos_sin_tipo = suma(ingresos donde tipo IS NULL)
ingresos_tipados[t] = suma(ingresos donde tipo = t)
ingresos_totales = ingresos_sin_tipo + suma(ingresos_tipados)
```

El cálculo debe ser:

```text
asignado[t] = ingresos_sin_tipo * porcentaje[t] / 100
disponible[t] = asignado[t] + arrastre[t] + ingresos_tipados[t]
restante[t] = disponible[t] - gastado[t]
```

- El ingreso tipado no se multiplica por porcentajes.
- El ingreso tipado se suma al rubro `t` del mes de su fecha.
- El ingreso tipado no se suma a ningún otro rubro.

**Verificación:** pruebas de cálculo y API con ingresos tipados y sin tipo en el mismo mes.

### FR-006 — Monto sin asignar

El monto sin asignar debe calcularse solo con los ingresos sin tipo:

```text
sin_asignar = max(ingresos_sin_tipo - suma(asignado), 0)
```

El ingreso tipado no debe aparecer en `sin_asignar`, porque ya fue asignado directamente a un rubro.

**Verificación:** un ingreso tipado no aumenta `sin_asignar`; un ingreso sin tipo sí puede aumentarlo.

### FR-007 — Arrastre

El restante de cada rubro debe incluir los ingresos tipados y participar en la cadena de arrastre existente:

- El restante de `NECESARIO` pasa al disponible de `NO_NECESARIO` del mes siguiente.
- El restante de `NO_NECESARIO` pasa al disponible de `NO_NECESARIO` del mes siguiente.
- El restante de `INVERSION` pasa al disponible de `INVERSION` del mes siguiente.
- Los positivos y negativos se arrastran.
- Diciembre pasa a enero del año siguiente.

**Verificación:** pruebas con ingreso tipado `NECESARIO`, `NO_NECESARIO` e `INVERSION` y verificación del mes siguiente.

### FR-008 — Balance anual

La tabla anual debe incluir, por rubro:

- `asignado` base: suma de los asignados porcentuales mensuales.
- `arrastre`: saldo inicial y transferencias según las reglas existentes.
- `ingresos_tipados`: suma de los ingresos tipados del año para ese rubro.
- `disponible`: `asignado + arrastre + ingresos_tipados`.
- `gastado`: gasto real anual.
- `restante`: disponible menos gastado, con la semántica de necesarios definida abajo.
- `porcentaje` ponderado.

Para necesarios:

```text
restante_anual = asignado_anual + ingresos_tipados_anuales - gastado_anual
```

Ese restante se transfiere a no necesarios en la cadena anual. Para no necesarios e inversión, el restante anual es el saldo final del año.

El porcentaje ponderado se calcula sobre los ingresos sin tipo:

```text
porcentaje_ponderado = asignado_anual / ingresos_sin_tipo_anuales * 100
```

Si no hay ingresos sin tipo, el porcentaje es `0.00`.

**Verificación:** prueba de API y componente con ingresos tipados en varios meses, incluyendo necesarios.

### FR-009 — Contrato de rubros con ingresos tipados

Cada rubro de la respuesta mensual y anual debe incluir:

- `porcentaje`.
- `asignado`.
- `arrastre`.
- `ingresos_tipados`.
- `disponible`.
- `gastado`.
- `restante`.

La suma visible debe cumplir:

```text
disponible = asignado + arrastre + ingresos_tipados
```

**Verificación:** pruebas de schema y de contrato OpenAPI.

### FR-010 — Interfaz del balance

La vista mensual y la tabla anual deben mostrar `Ingresos tipados` junto a `Asignado`, `Arrastre`, `Disponible`, `Gastado` y `Restante`.

La vista debe incluir una nota que explique que los ingresos con tipo se suman directamente al rubro y no se reparten por porcentajes. En necesarios se mantiene la indicación de que el restante se transfiere a no necesarios.

**Verificación:** pruebas de `MonthlyBalanceView` y revisión visual responsive.

### FR-011 — Importación de ingresos

Para archivos de importación de ingresos:

- La columna canónica `Categoría`/`Tipo` se interpreta como tipo opcional.
- Se aceptan los alias `Necesario`, `No necesario` e `Inversión`, sin distinguir mayúsculas ni acentos.
- También se aceptan los valores exactos `NECESARIO`, `NO_NECESARIO` e `INVERSION`.
- Un valor vacío o ausente produce `tipo = null`.
- Un valor desconocido deja la fila pendiente con un error en el campo `tipo`.
- El texto original se conserva en `filas_importacion.categoria` para auditoría.
- La fila pendiente permite corregir el tipo y contabilizar el ingreso.
- La importación de gastos conserva su comportamiento actual.

Debe existir una columna nullable `tipo` en `filas_importacion`, con la misma restricción de valores que `ingresos.tipo`.

**Verificación:** pruebas de parser, normalización, validación, importación, pendientes y commit.

### FR-012 — Resumen y gráficas

- `GET /api/resumen` debe seguir sumando todos los ingresos, incluidos los tipados, en `total_ingresos`.
- Las gráficas de gastos no cambian.
- El balance mensual y anual es el único cálculo que separa ingresos tipados y sin tipo.

**Verificación:** pruebas de resumen y gráficas sin cambios.

### FR-013 — Documentación y versión

La entrega debe actualizar:

- `README.md` con el contrato de ingresos y la semántica del balance.
- `AGENTS.md` con el estado de la especificación.
- `specs/README.md` con la fila 010.
- La versión a `1.2.0` en frontend, backend y lockfiles.
- La evidencia de validación en `tasks.md`.

**Verificación:** metadatos coherentes y smoke test de producción.

## 6. Requisitos no funcionales

### NFR-001 — Precisión monetaria

Los importes y porcentajes se calculan con `Decimal` y se almacenan con `NUMERIC`. Nunca se usa `float`.

### NFR-002 — Validación en servidor y base de datos

El tipo se valida en Pydantic y se refuerza con una restricción `CHECK` en PostgreSQL.

### NFR-003 — Convenciones de nombres

El contrato externo usa español (`tipo`, `ingresos_tipados`, `disponible`). El código interno usa inglés (`income_type`, `typed_incomes`, `available`). Los DTO de frontera conservan los nombres del contrato.

### NFR-004 — Pruebas

Debe haber pruebas unitarias de cálculos, pruebas de schema, integración contra PostgreSQL, OpenAPI, componentes y regresión de importación, resumen y gráficas.

### NFR-005 — Compatibilidad

No se deben romper los endpoints de gastos, resumen, importación, gráficas, salud, Docker Compose ni las funcionalidades existentes.

### NFR-006 — Sin dependencias nuevas

No se añaden librerías de backend ni de frontend.

### NFR-007 — Accesibilidad

El selector de tipo debe tener etiqueta asociada. La tabla y la nota del balance deben ser comprensibles con lector de pantalla.

### NFR-008 — Local y sin autenticación

La funcionalidad es local, de un solo usuario y sin autenticación. No se expone a Internet.

### NFR-009 — Migración destructiva controlada

La eliminación de `ingresos.categoria` requiere respaldo previo de la base y autorización explícita antes de ejecutarse en producción. La migración debe documentar los datos que se pierden.

## 7. Reglas de negocio

- **BR-001:** el tipo de ingreso es opcional.
- **BR-002:** los valores permitidos son los mismos que los tipos de gasto.
- **BR-003:** un ingreso sin tipo se reparte por porcentajes como hasta ahora.
- **BR-004:** un ingreso tipado no se incluye en la base porcentual.
- **BR-005:** un ingreso tipado se suma al disponible del rubro del mes de su fecha.
- **BR-006:** un ingreso tipado no se suma a `sin_asignar`.
- **BR-007:** el restante del rubro incluye los ingresos tipados y se arrastra según las reglas existentes.
- **BR-008:** la vista anual no cuenta dos veces el ingreso tipado: aparece en `ingresos_tipados` y en `disponible`, no en `asignado`.
- **BR-009:** el porcentaje ponderado anual usa los ingresos sin tipo como denominador.
- **BR-010:** en la importación de ingresos, un tipo desconocido deja la fila pendiente.
- **BR-011:** la categoría histórica libre se pierde al eliminar `ingresos.categoria`; solo se conservan los valores que coincidan exactamente con un tipo.
- **BR-012:** el total de ingresos del resumen global incluye los ingresos tipados.

## 8. Casos límite y errores

- Ingreso sin tipo: se comporta como antes.
- Ingreso con tipo y sin porcentajes configurados: el asignado es `0.00` y el disponible es el ingreso tipado más el arrastre.
- Ingreso tipado en un mes sin otros ingresos: no hay base porcentual; el disponible del rubro recibe el importe.
- Ingreso tipado `NECESARIO`: su restante se transfiere a `NO_NECESARIO` del mes siguiente.
- Ingreso tipado con restante negativo: el negativo se arrastra.
- Cambio de tipo o eliminación del ingreso: los meses posteriores se recalculan.
- Tipo inválido en API: `422`.
- Tipo inválido en importación: fila pendiente con error `tipo`.
- Categoría histórica desconocida: se pierde al migrar; el ingreso queda sin tipo.
- Año sin ingresos sin tipo pero con ingresos tipados: el porcentaje ponderado es `0.00`.
- La migración `downgrade` recupera la columna `categoria`, pero no los valores eliminados.

## 9. Fuera de alcance

- Categorías libres o configurables.
- Más de un tipo por ingreso.
- Cambios en el tipo de los gastos.
- Cambios en las gráficas de gastos.
- Autenticación, multiusuario o exposición a Internet.
- Nuevas dependencias.
- Edición masiva de tipos de ingresos.
- Recuperación automática de categorías históricas que no sean tipos válidos.

## 10. Criterios de aceptación

| Criterio | Descripción | Verificación |
|---|---|---|
| AC-001 | `ingresos.tipo` existe, es nullable y tiene restricción de valores. | Migración y pruebas de base de datos. |
| AC-002 | `ingresos.categoria` se elimina y la migración es reversible en estructura. | `upgrade` y `downgrade` en base de test. |
| AC-003 | La API acepta y devuelve `tipo` opcional; `categoria` ya no aparece. | Pruebas de schema, API y OpenAPI. |
| AC-004 | Un tipo inválido devuelve `422`; vacío se normaliza a `null`. | Pruebas de schema y API. |
| AC-005 | Un ingreso sin tipo mantiene el cálculo actual. | Pruebas de balance y regresión. |
| AC-006 | Un ingreso tipado no se pondera y se suma al disponible del rubro. | Pruebas de cálculo y API. |
| AC-007 | Un ingreso tipado no aumenta `sin_asignar`. | Pruebas de cálculo y API. |
| AC-008 | El restante con ingreso tipado se arrastra al mes siguiente. | Pruebas de integración. |
| AC-009 | La tabla anual incluye `ingresos_tipados` y no cuenta dos veces. | Pruebas de API y componente. |
| AC-010 | El porcentaje ponderado anual usa ingresos sin tipo. | Pruebas de cálculo y API. |
| AC-011 | La importación interpreta `Categoría` como tipo y deja pendientes los valores desconocidos. | Pruebas de importación y pendientes. |
| AC-012 | La UI muestra el selector, el listado y los ingresos tipados en el balance. | Pruebas de componentes. |
| AC-013 | El resumen global incluye los ingresos tipados y las gráficas no cambian. | Pruebas de resumen y gráficas. |
| AC-014 | La documentación, la versión 1.2.0 y la validación de producción están actualizadas. | Revisión documental y smoke test. |

## 11. Decisiones de negocio y supuestos

### D-001 — Reemplazar la categoría libre por tipo

**Propuesta:** eliminar `ingresos.categoria` y añadir `ingresos.tipo` nullable con los mismos valores de gastos.

**Alternativas:** mantener categoría y añadir tipo; renombrar categoría; conservar ambos campos.

**Impacto:** migración destructiva, contrato de ingresos, formulario, listado, importación y balance.

**Decisión aprobada:** se reemplaza la categoría libre por tipo, aceptando la pérdida de los valores históricos que no coincidan con un tipo.

### D-002 — Total de ingresos y monto sin asignar

**Propuesta:** `ingresos` muestra el total, incluidos los tipados; `sin_asignar` usa solo ingresos sin tipo.

**Alternativas:** excluir los tipados del total; incluirlos en `sin_asignar`; crear un campo separado para la base porcentual.

**Impacto:** contrato mensual, interfaz y pruebas.

**Decisión aprobada:** el total incluye los ingresos tipados y `sin_asignar` se calcula solo con ingresos sin tipo.

### D-003 — Importación de ingresos

**Propuesta:** interpretar `Categoría`/`Tipo` como tipo opcional. Los valores válidos se normalizan; los desconocidos dejan la fila pendiente. El texto original se conserva en la fila de importación para auditoría.

**Alternativas:** ignorar la categoría; importar siempre sin tipo; aceptar texto libre y mapear solo lo reconocible.

**Impacto:** normalización, validación, modelo de filas de importación, pendientes, commit y pruebas.

**Decisión aprobada:** se adopta la interpretación como tipo, con pendientes para valores desconocidos.

### D-004 — Porcentaje ponderado anual

**Propuesta:** calcular el porcentaje ponderado sobre los ingresos sin tipo.

**Alternativas:** usar el total de ingresos, incluidos los tipados; usar el asignado base sin denominador.

**Impacto:** cálculo anual y pruebas.

**Decisión aprobada:** el denominador son los ingresos sin tipo.

### D-005 — Exponer ingresos tipados en el contrato

**Propuesta:** añadir `ingresos_tipados` a cada rubro mensual y anual para que la suma visible sea `asignado + arrastre + ingresos_tipados = disponible`.

**Alternativas:** no exponerlo y explicar la diferencia solo en la interfaz; añadir un campo global de ingresos tipados.

**Impacto:** schema de balance, UI y pruebas.

**Decisión aprobada:** se expone `ingresos_tipados` por rubro.

### D-006 — Versión de la entrega

**Propuesta:** publicar la funcionalidad como versión `1.2.0`.

**Impacto:** `package.json`, `package-lock.json`, `pyproject.toml`, `uv.lock`, `main.py`, README y evidencia.

**Decisión aprobada:** la entrega se publica como `1.2.0`.

## 12. Resultado de validación

La revisión 1 fue validada el 2026-11-03 con 291 pruebas de backend y 100 de frontend, versión 1.2.0, migración `0008_add_income_type` y smoke test de producción. El tipo opcional, la exclusión de la base porcentual, el disponible por rubro, el arrastre, el balance anual y la importación con pendientes quedaron cubiertos. La migración destructiva se ejecutó en producción después de un respaldo previo.

## 13. Historial de revisiones

- Revisión 1: tipo opcional de ingresos, asignación directa al disponible, importación como tipo y migración destructiva de categoría.
