# Especificación 008 — Balance mensual

- Estado: validada (revisión 3).
- Fase: 6.
- Iteración: 1.1.
- Dependencias: `specs/002-api-ingresos/`, `specs/003-api-gastos/`, `specs/004-api-resumen/`, `specs/005-interfaz-mvp/`.
- Plan: `plan.md` (aprobado; revisión 3 implementada y validada).
- Tareas: `tasks.md` (T-001 a T-015 completadas).

## 1. Contexto y problema

La aplicación permite registrar ingresos y gastos, clasificar los gastos y consultar un resumen global. El usuario necesita una vista periódica para saber cuánto dinero tiene disponible en cada rubro de gasto y cuánto ha invertido.

El resumen global no responde a esta necesidad porque mezcla todos los meses y no permite comparar la planeación con el gasto real de un periodo. Además, el usuario quiere asignar porcentajes distintos de sus ingresos a cada rubro en cada mes.

Esta especificación añade una vista de balance mensual y anual, con asignaciones porcentuales persistidas por mes. La revisión 3 incorpora el arrastre de saldos entre meses y entre años.

## 2. Usuarios y actores

- **Usuario propietario:** consulta el balance de un mes o de un año y ajusta sus porcentajes.
- **Frontend:** muestra los selectores, la tabla y el formulario de porcentajes.
- **Backend:** agrega ingresos y gastos, calcula asignaciones y persiste los porcentajes.
- **PostgreSQL:** almacena las asignaciones mensuales y ejecuta las agregaciones.

No hay autenticación, roles ni multiusuario.

## 3. Historias de usuario y flujos

### US-001 — Consultar un mes

Como usuario, quiero seleccionar un año y un mes para ver los movimientos del mes y cuánto me queda disponible en cada rubro.

**Flujo:**

1. El usuario abre la pestaña `Balance mensual`.
2. Selecciona un año y un mes.
3. El sistema consulta ingresos, gastos, inversiones y porcentajes del mes.
4. La interfaz muestra cuatro columnas: ingresos, gastos necesarios, gastos no necesarios e inversión.
5. Cada columna lista sus movimientos con fecha, descripción y valor.
6. Si no hay movimientos, la columna muestra un estado vacío y su total en cero.

### US-002 — Consultar el año

Como usuario, quiero ver el balance general de un año cuando no selecciono un mes.

**Flujo:**

1. El usuario abre la pestaña `Balance mensual`.
2. El selector de mes queda en `Todos`.
3. El sistema agrega los doce meses del año seleccionado.
4. La tabla muestra asignado, arrastre, disponible, gastado, restante y porcentaje ponderado por rubro.

### US-003 — Asignar porcentajes mensuales

Como usuario, quiero asignar un porcentaje de los ingresos del mes a cada rubro y guardarlo para ese mes.

**Flujo:**

1. El usuario selecciona un mes.
2. Edita los porcentajes de `NECESARIO`, `NO_NECESARIO` e `INVERSION`.
3. Guarda los cambios.
4. El sistema valida los porcentajes y los persiste para ese año y mes.
5. La vista se actualiza con los nuevos montos asignados y restantes.

### US-004 — Ver dinero sin asignar

Como usuario, quiero saber cuánto de mis ingresos no he asignado a ningún rubro.

**Flujo:**

1. El usuario selecciona un mes con porcentajes que suman menos de 100%.
2. La interfaz muestra el monto sin asignar.
3. El monto sin asignar se calcula con los ingresos del periodo menos la suma de los montos asignados.

### US-005 — Ver un restante negativo

Como usuario, quiero saber cuándo gasté más de lo asignado en un rubro.

**Flujo:**

1. El gasto real del rubro supera el monto asignado.
2. El restante se muestra con signo negativo.
3. La interfaz no oculta ni recorta el valor.

### US-006 — Arrastrar saldos entre meses

Como usuario, quiero que el saldo restante de cada rubro pase al mes siguiente para no perderlo ni ignorar un faltante.

**Flujo:**

1. El sistema calcula el restante de cada rubro en el mes.
2. El restante de gastos necesarios pasa al disponible de gastos no necesarios del mes siguiente.
3. El restante de gastos no necesarios pasa al disponible de gastos no necesarios del mes siguiente.
4. El restante de inversión pasa al disponible de inversión del mes siguiente.
5. Los restantes positivos y negativos se arrastran.
6. Diciembre del año n pasa a enero del año n+1.

## 4. Requisitos funcionales

### FR-001 — Pestaña de balance mensual

La interfaz debe incluir una pestaña `Balance mensual` junto a las pestañas existentes `Ingresos` y `Gastos`.

**Verificación:** la pestaña existe, es accesible y muestra su panel al activarse.

### FR-002 — Selectores de año y mes

La vista debe incluir dos menús desplegables:

- Año: años disponibles y año actual.
- Mes: `Todos` y los doce meses.

El año actual es el valor inicial. `Todos` es el valor inicial del mes y representa la vista anual.

Si el usuario no selecciona un año, se usa el año actual. Si no selecciona un mes, se muestra el balance anual del año seleccionado.

**Verificación:** los selectores cambian la consulta y la vista anual se muestra con `Todos`.

### FR-003 — Vista mensual en cuatro columnas

Con un mes seleccionado, la vista debe mostrar cuatro columnas:

- `Ingresos`.
- `Gastos necesarios`.
- `Gastos no necesarios`.
- `Inversión`.

Cada columna debe listar los movimientos del mes con tres subcolumnas:

- `Fecha`.
- `Descripción`.
- `Valor`.

Al final de cada columna debe mostrarse su total. Las columnas de gastos necesarios, gastos no necesarios e inversión deben mostrar además su monto asignado, el arrastre recibido, el disponible y el restante. La columna de ingresos debe mostrar el total de ingresos y el monto sin asignar.

Las columnas deben mostrar un estado vacío cuando no tengan movimientos. La vista debe mantener las cuatro columnas alineadas y apilarse verticalmente en pantallas estrechas.

**Verificación:** las cuatro columnas aparecen siempre, con sus movimientos, totales y restantes; una columna sin movimientos muestra un estado vacío.

### FR-004 — Porcentajes mensuales editables

Con un mes seleccionado, el usuario debe poder editar el porcentaje de cada uno de los tres rubros y guardarlo.

- Los porcentajes se editan en una fila superior a las columnas de gastos e inversión.
- Cada porcentaje se guarda para el año y mes seleccionados.
- Los porcentajes de un mes no afectan a otros meses.
- Guardar un mes no modifica los movimientos financieros.
- Los porcentajes se expresan con dos decimales.

**Verificación:** dos meses distintos conservan porcentajes distintos después de recargar la vista.

### FR-005 — Cálculo del monto asignado

El monto asignado base a cada rubro se calcula como:

```text
asignado = ingresos_del_mes * porcentaje / 100
```

El resultado se normaliza a dos decimales con `Decimal`. El disponible añade el arrastre del mes anterior según FR-019.

**Verificación:** pruebas con ingresos y porcentajes que producen centavos.

### FR-006 — Cálculo del restante

El restante de cada rubro se calcula como:

```text
disponible = asignado + arrastre
restante = disponible - gasto_real_del_rubro
```

El restante puede ser negativo.

**Verificación:** pruebas con restante positivo, cero y negativo.

### FR-007 — Dinero invertido

El rubro `INVERSION` usa los gastos con tipo `INVERSION`. No se crea un tipo de movimiento nuevo.

**Verificación:** un gasto `INVERSION` aumenta el gasto real y el restante del rubro de inversión.

### FR-008 — Dinero sin asignar

Cuando la suma de los porcentajes es menor que 100%, la vista debe mostrar el monto sin asignar.

```text
sin_asignar = ingresos_del_periodo - suma(asignados)
```

Si el cálculo produce un valor negativo por redondeo, se normaliza a `0.00`.

**Verificación:** con porcentajes que suman 80%, se muestra el 20% restante como monto sin asignar.

### FR-009 — Vista anual

Cuando no hay un mes seleccionado, la vista debe mostrar una tabla agregada con el balance general del año seleccionado. La vista anual no lista movimientos individuales.

La tabla anual debe incluir, por rubro:

- Monto asignado base anual.
- Arrastre recibido.
- Disponible.
- Gasto real anual.
- Restante.
- Porcentaje ponderado.

El monto asignado anual es la suma de los montos base de cada mes. El porcentaje ponderado se calcula como:

```text
porcentaje_ponderado = asignado_anual / ingresos_anuales * 100
```

Si no hay ingresos anuales, el porcentaje ponderado es `0.00`.

La tabla anual debe ser coherente con el arrastre:

- En necesarios, `arrastre` es `0.00` y el restante se muestra como el monto transferido a no necesarios.
- En no necesarios, `arrastre` incluye el saldo inicial de enero más las transferencias de necesarios del año.
- En inversión, `arrastre` es el saldo inicial de enero.
- `disponible = asignado + arrastre`.
- El restante de no necesarios e inversión es el saldo final del año.
- No se suman restantes mensuales de forma ingenua, porque el saldo de necesarios se transfiere a no necesarios y se contaría dos veces.

**Verificación:** pruebas con meses de distintos ingresos y porcentajes.

### FR-010 — Año actual por defecto

Si no hay año seleccionado, la API y la interfaz usan el año actual.

**Verificación:** una consulta sin `anio` devuelve el año actual.

### FR-011 — Persistencia de asignaciones

Debe existir una tabla de asignaciones mensuales con una fila por año y mes.

La tabla debe almacenar:

- Año.
- Mes.
- Porcentaje de gastos necesarios.
- Porcentaje de gastos no necesarios.
- Porcentaje de inversión.

La combinación año/mes debe ser única.

**Verificación:** guardar dos veces el mismo mes actualiza la fila existente y no duplica registros.

### FR-012 — Validación de porcentajes

Cada porcentaje debe estar entre 0 y 100, con máximo dos decimales.

La suma de los tres porcentajes no puede superar 100.

Si la suma es menor que 100, la operación es válida y el resto queda sin asignar.

**Verificación:** valores negativos, mayores que 100, con más decimales o con suma mayor que 100 devuelven `422`.

### FR-013 — Consulta de periodos disponibles

La API debe devolver los años disponibles para el selector. La lista incluye los años con ingresos, gastos o asignaciones, más el año actual, ordenados de forma descendente.

**Verificación:** un año con movimientos aparece una sola vez y el año actual siempre está presente.

### FR-014 — Contrato de API

La API debe exponer:

- `GET /api/balance-mensual?anio=2026&mes=10`: balance mensual.
- `GET /api/balance-mensual?anio=2026`: balance anual.
- `GET /api/balance-mensual`: balance anual del año actual.
- `GET /api/balance-mensual/periodos`: años disponibles.
- `PUT /api/balance-mensual/asignaciones/2026/10`: guardar porcentajes del mes.

Los importes y porcentajes se transportan como strings decimales con dos decimales.

**Verificación:** las rutas aparecen en OpenAPI y las respuestas respetan el contrato.

### FR-015 — Respuesta mensual con movimientos

La respuesta mensual debe incluir los totales por rubro y los movimientos de las cuatro columnas:

```json
{
  "anio": 2026,
  "mes": 10,
  "ingresos": "5000.00",
  "sin_asignar": "0.00",
  "rubros": {
    "NECESARIO": {
      "porcentaje": "50.00",
      "asignado": "2500.00",
      "arrastre": "0.00",
      "disponible": "2500.00",
      "gastado": "1000.00",
      "restante": "1500.00"
    },
    "NO_NECESARIO": {
      "porcentaje": "30.00",
      "asignado": "1500.00",
      "arrastre": "1500.00",
      "disponible": "3000.00",
      "gastado": "300.00",
      "restante": "2700.00"
    },
    "INVERSION": {
      "porcentaje": "20.00",
      "asignado": "1000.00",
      "arrastre": "0.00",
      "disponible": "1000.00",
      "gastado": "200.00",
      "restante": "800.00"
    }
  },
  "movimientos": {
    "INGRESOS": [
      {
        "id": 1,
        "fecha": "2026-10-01",
        "descripcion": "Salario",
        "valor": "5000.00"
      }
    ],
    "NECESARIO": [
      {
        "id": 2,
        "fecha": "2026-10-02",
        "descripcion": "Mercado",
        "valor": "1000.00"
      }
    ],
    "NO_NECESARIO": [
      {
        "id": 3,
        "fecha": "2026-10-03",
        "descripcion": "Cine",
        "valor": "300.00"
      }
    ],
    "INVERSION": [
      {
        "id": 4,
        "fecha": "2026-10-04",
        "descripcion": "Fondo indexado",
        "valor": "200.00"
      }
    ]
  }
}
```

Los movimientos se ordenan por fecha y, ante empate, por id. Cada item incluye `id`, `fecha`, `descripcion` y `valor`.

**Verificación:** las claves, los cuatro grupos de movimientos, el orden y los strings decimales son los esperados.

### FR-016 — Respuesta anual

La respuesta anual usa la estructura agregada de `rubros`, con `mes: null`, `porcentaje` ponderado, `arrastre` y `disponible`. No incluye `movimientos`.

**Verificación:** la respuesta anual incluye `mes: null`, los tres rubros y los porcentajes ponderados, y no lista movimientos individuales.

### FR-017 — Estados de interfaz

La vista debe mostrar:

- Carga al consultar un periodo.
- Error con opción de reintentar.
- Estado vacío con valores en cero.
- Error de validación al guardar porcentajes.
- Confirmación visible del guardado exitoso.

**Verificación:** pruebas de componentes para carga, error, vacío y guardado.

### FR-018 — Independencia del resumen global

La nueva funcionalidad no debe modificar el endpoint `/api/resumen` ni los cálculos globales existentes.

**Verificación:** las pruebas existentes de resumen siguen pasando.

### FR-019 — Arrastre mensual entre rubros

El saldo restante de cada mes debe arrastrarse al mes siguiente:

- El restante de `NECESARIO` se suma al disponible de `NO_NECESARIO` del mes siguiente.
- El restante de `NO_NECESARIO` se suma al disponible de `NO_NECESARIO` del mes siguiente.
- El restante de `INVERSION` se suma al disponible de `INVERSION` del mes siguiente.
- Los restantes positivos y negativos se arrastran.
- El arrastre de necesarios no se suma al disponible de necesarios del mes siguiente.

**Verificación:** pruebas con restantes positivos y negativos en los tres rubros.

### FR-020 — Arrastre entre años

El arrastre no se reinicia en enero. Diciembre del año `n` pasa a enero del año `n+1` con las mismas reglas de FR-019.

**Verificación:** prueba con diciembre de un año y enero del año siguiente.

### FR-021 — Inicio del historial y recálculo dinámico

El cálculo del arrastre parte del primer mes con ingresos, gastos o asignaciones. Antes de ese mes el arrastre es `0.00`.

El arrastre se calcula dinámicamente al consultar. Si se modifican ingresos, gastos o porcentajes de un mes anterior, se recalculan todos los meses posteriores.

**Verificación:** prueba que modifica un mes anterior y verifica el cambio en el mes siguiente.

### FR-022 — Contrato de arrastre

Cada rubro de la respuesta debe incluir:

- `porcentaje`.
- `asignado`.
- `arrastre`.
- `disponible`.
- `gastado`.
- `restante`.

`sin_asignar` sigue siendo el ingreso no asignado y no incluye el arrastre.

**Verificación:** pruebas de schema y API.

### FR-023 — Vista anual con arrastre

La tabla anual debe mostrar `Asignado`, `Arrastre`, `Disponible`, `Gastado` y `Restante` por rubro, con la semántica definida en FR-009.

**Verificación:** prueba de componente y API con arrastre entre meses.

## 5. Requisitos no funcionales

### NFR-001 — Precisión monetaria

Los importes y porcentajes se calculan con `Decimal` y se almacenan con `NUMERIC`. Nunca se usa `float`.

### NFR-002 — Agregación en servidor

Los ingresos y gastos se agregan con `SUM` y `GROUP BY` en PostgreSQL. No se cargan todos los movimientos en memoria para calcular totales.

### NFR-003 — Convenciones de nombres

La ruta y los campos externos usan español. Clases, funciones, variables y componentes internos usan inglés. Los DTO de frontera conservan los nombres del contrato.

### NFR-004 — Pruebas

Debe haber pruebas unitarias de cálculos, pruebas de API, integración contra PostgreSQL, OpenAPI y pruebas de componentes.

### NFR-005 — Accesibilidad

Los selectores deben tener etiquetas asociadas. La tabla debe ser navegable y comprensible con lector de pantalla. Los errores y confirmaciones deben ser visibles y accesibles.

### NFR-006 — Sin dependencias nuevas

No se añaden librerías de frontend ni backend.

### NFR-007 — Compatibilidad

No se deben romper las APIs de ingresos, gastos, resumen, importación, salud, el frontend ni Docker Compose.

### NFR-008 — Local y sin autenticación

La funcionalidad es local, de un solo usuario y sin autenticación. No se expone a Internet.

## 6. Reglas de negocio

- **BR-001:** los porcentajes son independientes por año y mes.
- **BR-002:** cada porcentaje está entre 0 y 100.
- **BR-003:** la suma de los tres porcentajes no supera 100.
- **BR-004:** un mes sin asignación se interpreta con 0% en los tres rubros.
- **BR-005:** `asignado = ingresos_del_periodo * porcentaje / 100`.
- **BR-006:** `disponible = asignado + arrastre` y `restante = disponible - gastado`; puede ser negativo.
- **BR-007:** `sin_asignar = ingresos - suma(asignados)`; se normaliza a cero si el redondeo lo deja negativo.
- **BR-008:** el rubro de inversión usa gastos `INVERSION`.
- **BR-009:** la vista anual usa la cadena de arrastre y no suma restantes mensuales de forma ingenua.
- **BR-010:** el porcentaje anual es ponderado por los ingresos anuales.
- **BR-011:** sin ingresos en el periodo, los montos asignados son `0.00`.
- **BR-012:** el año actual es el valor por defecto.
- **BR-013:** un mes sin movimientos sigue siendo consultable y editable.
- **BR-014:** el restante de necesarios pasa al disponible de no necesarios del mes siguiente.
- **BR-015:** el restante de no necesarios pasa al disponible de no necesarios del mes siguiente.
- **BR-016:** el restante de inversión pasa al disponible de inversión del mes siguiente.
- **BR-017:** los restantes positivos y negativos se arrastran.
- **BR-018:** el arrastre no se reinicia en enero; diciembre pasa a enero del año siguiente.
- **BR-019:** el arrastre se recalcula dinámicamente al cambiar datos históricos.

## 7. Casos límite y errores

- Sin ingresos ni gastos: todos los importes en `"0.00"`.
- Sin porcentajes guardados: 0% y asignado `"0.00"`.
- Porcentajes que suman 100%: sin asignar `"0.00"`.
- Porcentajes que suman menos de 100%: se muestra el monto sin asignar.
- Porcentajes que suman más de 100%: `422`.
- Porcentaje negativo o mayor que 100: `422`.
- Porcentaje con más de dos decimales: `422`.
- Ingresos o gastos con fechas de otro año: no se incluyen.
- Mes sin ingresos pero con gastos: asignado `"0.00"` y restante negativo.
- Año sin datos: tabla con ceros y año actual disponible.
- Error de red: la vista conserva los datos y permite reintentar.
- Cambio de ingresos después de asignar: los montos asignados y restantes se recalculan con los ingresos actuales.
- Octubre con restante positivo en necesarios: noviembre lo recibe en no necesarios.
- Octubre con restante negativo en necesarios: noviembre lo descuenta de no necesarios.
- Diciembre con restante: enero del año siguiente lo recibe según las mismas reglas.
- Sin datos anteriores: el primer mes parte con arrastre `0.00`.
- Cambio de un mes anterior: se recalculan todos los meses posteriores.
- Vista anual: no se suman restantes mensuales de forma ingenua; se usa la semántica de FR-009.

## 8. Fuera de alcance

- Presupuestos por categorías libres.
- Edición masiva de varios meses.
- Gráficos y reportes exportables.
- Metas de ahorro.
- Autenticación y multiusuario.
- Historial de cambios de porcentajes.
- Comparación entre años.
- Movimientos recurrentes.

## 9. Criterios de aceptación

| Criterio | Descripción | Verificación |
|---|---|---|
| AC-001 | La pestaña `Balance mensual` existe y es accesible. | Prueba de `App`. |
| AC-002 | Los selectores de año y mes funcionan y el año actual es el inicial. | Prueba de componente. |
| AC-003 | La vista mensual muestra cuatro columnas con fecha, descripción, valor, total, arrastre, disponible y restante donde aplica. | Prueba de componente y API. |
| AC-004 | La vista anual aparece con `Todos` e incluye arrastre y disponible. | Prueba de API y componente. |
| AC-005 | Los porcentajes se guardan por mes y no afectan otros meses. | Prueba de integración. |
| AC-006 | La suma menor que 100 muestra el monto sin asignar. | Prueba de cálculo y componente. |
| AC-007 | La suma mayor que 100 devuelve `422`. | Prueba de API. |
| AC-008 | El restante negativo se muestra sin recortes. | Prueba de cálculo y componente. |
| AC-009 | El rubro `INVERSION` usa gastos de tipo `INVERSION`. | Prueba de integración. |
| AC-010 | El porcentaje anual es ponderado por los ingresos. | Prueba de cálculo y API. |
| AC-011 | Los periodos disponibles incluyen el año actual y los años con datos. | Prueba de API. |
| AC-012 | Las rutas y schemas aparecen en OpenAPI. | Prueba de OpenAPI. |
| AC-013 | La vista maneja carga, error, vacío y guardado. | Pruebas de componentes. |
| AC-014 | El resumen global y las funcionalidades existentes no cambian. | Suite completa. |
| AC-015 | El restante positivo de necesarios se suma a no necesarios del mes siguiente. | Prueba de cálculo y API. |
| AC-016 | Los restantes negativos se arrastran y reducen el disponible siguiente. | Prueba de cálculo y API. |
| AC-017 | No necesarios e inversión se arrastran de forma independiente. | Prueba de cálculo y API. |
| AC-018 | Diciembre pasa a enero del año siguiente sin reinicio. | Prueba de integración. |
| AC-019 | El arrastre se recalcula al modificar datos históricos. | Prueba de integración. |
| AC-020 | La vista anual muestra Asignado, Arrastre, Disponible, Gastado y Restante sin doble conteo. | Prueba de cálculo, API y componente. |

## 10. Decisiones de negocio y supuestos

### D-001 — Porcentajes menores que 100

**Propuesta:** permitir que la suma sea menor que 100 y mostrar el monto sin asignar.

**Alternativas:** exigir exactamente 100; impedir guardar; repartir el resto automáticamente.

**Impacto:** validación, cálculo y visualización.

**Decisión aprobada:** se permite una suma menor que 100 y se muestra el monto sin asignar.

### D-002 — Año por defecto

**Propuesta:** usar el año actual cuando no hay año seleccionado.

**Alternativas:** usar el último año con datos; mostrar todos los años.

**Impacto:** valor inicial y contrato de consulta.

**Decisión aprobada:** se usa el año actual.

### D-003 — Porcentaje anual ponderado

**Propuesta:** mostrar el porcentaje anual ponderado por los ingresos del año.

**Alternativas:** promedio simple de los porcentajes mensuales; no mostrar porcentaje anual.

**Impacto:** cálculo y tabla anual.

**Decisión aprobada:** se muestra el porcentaje ponderado por ingresos.

### D-004 — Restante negativo e inversión

**Propuesta:** permitir restante negativo y calcular inversión con gastos `INVERSION`.

**Alternativas:** recortar el restante a cero; crear un tipo de movimiento separado.

**Impacto:** cálculo y semántica de la tabla.

**Decisión aprobada:** se permite restante negativo y se usa el tipo `INVERSION`.

### D-005 — Una fila por mes

**Propuesta:** almacenar una fila por año y mes con los tres porcentajes.

**Alternativas:** una fila por rubro; tres tablas separadas; configuración global.

**Impacto:** modelo de datos, validación y migración.

**Decisión aprobada:** una fila por año y mes.

### D-006 — Vista mensual en cuatro columnas

**Propuesta:** mostrar los movimientos del mes en cuatro columnas: ingresos, gastos necesarios, gastos no necesarios e inversión. Cada columna tendrá fecha, descripción, valor y total; los tres rubros de gasto/inversión mostrarán además asignado y restante.

**Alternativas:** mantener una tabla agregada de rubros; mostrar una sola columna de gastos; mostrar los movimientos en una lista única.

**Impacto:** contrato de respuesta, componente de frontend y pruebas.

**Decisión aprobada:** se usa una vista mensual de cuatro columnas y la vista anual sigue siendo una tabla agregada.

### D-007 — Arrastre de saldos

**Propuesta:** arrastrar los saldos entre meses sin reiniciar en enero. El restante de necesarios pasa a no necesarios del mes siguiente; no necesarios e inversión se arrastran de forma independiente. Positivos y negativos se arrastran. La vista anual usa Asignado, Arrastre, Disponible, Gastado y Restante.

**Alternativas:** no arrastrar; reiniciar en enero; arrastrar necesarios a necesarios; mostrar solo el saldo mensual.

**Impacto:** cálculo mensual/anual, contrato de API, UI y pruebas.

**Decisión aprobada:** se acepta el arrastre continuo, incluyendo diciembre a enero del año siguiente, y el cálculo dinámico.

## 11. Resultado de validación

La revisión 2 fue validada el 2026-10-31 con 256 pruebas de backend y 88 de frontend, migración `0007` y smoke test de producción. La vista mensual de cuatro columnas, los porcentajes mensuales, el monto sin asignar y la vista anual ponderada quedaron cubiertos por pruebas de cálculo, API, integración y componentes.

La revisión 3 fue validada el 2026-10-31 con 272 pruebas de backend y 99 de frontend, versión 1.1.0 y smoke test de producción. El arrastre continuo, el paso diciembre→enero, el contrato con `arrastre`/`disponible` y la tabla anual sin doble conteo quedaron cubiertos.

## 12. Historial de revisiones

- Revisión 1: especificación inicial aprobada.
- Revisión 2: vista mensual de cuatro columnas con movimientos, fecha y totales; vista anual agregada.
- Revisión 3: arrastre continuo de saldos, necesario a no necesario, no necesario e inversión independientes, y tabla anual con arrastre.
