# Especificación 007 — Importación de ingresos y gastos desde Excel y CSV

- Estado: aprobada.
- Fase: 5.
- Iteración: MVP+.
- Dependencias: `specs/002-api-ingresos/`, `specs/003-api-gastos/`, `specs/004-api-resumen/`, `specs/005-interfaz-mvp/`.
- Plan: `plan.md` (aprobado).
- Tareas: `tasks.md` (aprobadas).

## 1. Contexto y problema

El MVP permite registrar ingresos y gastos manualmente, uno por uno. No existe una forma de incorporar movimientos históricos que el usuario ya tiene en hojas de cálculo o archivos CSV.

El usuario necesita importar archivos con las columnas `Fecha`, `Descripción`, `Valor` y `Categoría`. Los archivos reales no siempre están completos: puede faltar una fecha, una descripción, un valor o una categoría; puede haber valores inválidos; y un mismo movimiento puede aparecer más de una vez.

La aplicación actual tiene limitaciones relevantes para este caso:

- `ingresos` no tiene categoría.
- `gastos` usa `tipo` con los valores `NECESARIO`, `NO_NECESARIO` e `INVERSION`.
- El resumen solo suma `ingresos` y `gastos`.
- No existe un concepto de importación, lote, fila pendiente ni estado de revisión.
- La interfaz no tiene una pantalla de importación ni una bandeja de pendientes.

La funcionalidad debe incorporar movimientos completos a la contabilidad, conservar los incompletos para corrección manual y garantizar que los pendientes nunca alteren los indicadores financieros.

Esta especificación es documental. No implementa código, migraciones, dependencias ni cambios de infraestructura.

## 2. Usuarios y actores

- **Propietario/operador:** único usuario de la aplicación. Selecciona archivos, revisa resultados, corrige pendientes, contabiliza o descarta.
- **Desarrollador:** implementa y mantiene el importador, las tablas de staging y las pantallas.
- **Agente de implementación:** trabaja siguiendo `constitution.md`, `AGENTS.md` y esta especificación.
- **Sistema:** valida archivos y filas, persiste pendientes, contabiliza movimientos y calcula el indicador de pendientes.

No hay autenticación, roles ni usuarios remotos.

## 3. Historias de usuario y flujos

### US-001 — Importar un archivo

Como usuario, quiero seleccionar un archivo Excel o CSV y elegir si contiene ingresos o gastos para incorporar los movimientos completos a la contabilidad.

**Flujo esperado:**

1. El usuario abre la pantalla de importación.
2. Selecciona un archivo `.csv` o `.xlsx`.
3. Indica el tipo de movimiento del archivo: ingreso o gasto.
4. El sistema valida formato, tamaño, columnas y filas.
5. Las filas completas y válidas se incorporan a la contabilidad.
6. Las filas incompletas o inválidas quedan pendientes.
7. El sistema muestra un resumen con totales y errores.

### US-002 — Revisar pendientes

Como usuario, quiero ver los registros que no se incorporaron para saber qué información falta o es inválida.

**Flujo esperado:**

1. La pantalla principal muestra un botón de pendientes con un indicador.
2. El usuario abre la bandeja.
3. Ve cada fila pendiente con su número de fila, lote, datos disponibles y errores.
4. Puede distinguir campos faltantes de campos inválidos.
5. Los pendientes no aparecen en el resumen financiero.

### US-003 — Corregir y contabilizar

Como usuario, quiero completar o corregir un pendiente y contabilizarlo cuando sea válido.

**Flujo esperado:**

1. El usuario edita fecha, descripción, valor, categoría o tipo según falte.
2. Guarda los cambios.
3. El sistema revalida la fila y actualiza sus errores.
4. Si la fila es válida, el usuario puede contabilizarla.
5. El sistema crea el movimiento en `ingresos` o `gastos` y marca la fila como importada.
6. El resumen y el indicador se actualizan.

### US-004 — Descartar un pendiente

Como usuario, quiero descartar un registro que no quiero contabilizar.

**Flujo esperado:**

1. El usuario elige descartar.
2. El sistema pide confirmación.
3. La fila deja de aparecer entre los pendientes.
4. No se crea ningún movimiento.
5. El indicador se actualiza.

### US-005 — Detectar duplicados

Como usuario, quiero que el sistema me advierta cuando un movimiento parece repetido para decidir si lo contabilizo o lo descarto.

**Flujo esperado:**

1. El sistema normaliza los datos de cada fila.
2. Compara la fila con otras filas del mismo lote y con importaciones anteriores.
3. Si encuentra una coincidencia, deja la fila pendiente con una advertencia de posible duplicado.
4. El usuario decide si contabilizar o descartar.
5. Un pendiente ya contabilizado no puede contabilizarse otra vez.

### US-006 — Proteger los totales

Como usuario, quiero que ningún registro pendiente afecte el total de ingresos, el total de gastos, el balance ni el desglose por tipo.

**Flujo esperado:**

1. La importación guarda los pendientes en tablas separadas.
2. El resumen solo consulta `ingresos` y `gastos`.
3. La prueba de resumen confirma que los pendientes no alteran los cálculos.
4. Al contabilizar un pendiente, el resumen se actualiza solo después de crear el movimiento.

## 4. Requisitos funcionales

### FR-001 — Carga de archivos Excel y CSV

La interfaz debe permitir seleccionar un archivo `.csv` o `.xlsx` y enviarlo al backend.

- El archivo se envía como `multipart/form-data`.
- El usuario debe indicar si el archivo contiene ingresos o gastos.
- La interfaz debe aceptar únicamente las extensiones y tipos permitidos.
- El backend debe validar la extensión, el tipo de contenido y el tamaño; no debe confiar solo en la extensión.
- La carga debe mostrar estado de envío y un resultado claro.
- No se admiten `.xls`, `.xlsm`, `.xlsb`, PDF ni archivos comprimidos.

**Verificación:** un CSV y un XLSX válidos producen un lote; una extensión no permitida produce un error controlado.

### FR-002 — Estructura y columnas del archivo

El sistema debe identificar las columnas `Fecha`, `Descripción`, `Valor` y `Categoría`.

- La primera fila con contenido se considera cabecera.
- Para Excel se usa la primera hoja del libro.
- Los nombres de columna se comparan sin distinguir mayúsculas, acentos ni espacios externos.
- Se aceptan alias equivalentes documentados para las columnas obligatorias.
- `Fecha`, `Descripción` y `Valor` son obligatorios.
- `Categoría` es obligatoria para gastos y opcional para ingresos.
- Las columnas adicionales se ignoran sin alterar los datos.
- Si faltan cabeceras obligatorias, el archivo se rechaza completo y no se crea ningún movimiento.

**Verificación:** un archivo con cabeceras equivalentes se procesa; uno sin `Valor` se rechaza sin efectos.

### FR-003 — Validación individual de filas

Cada fila debe validarse por separado:

- Fecha válida.
- Descripción no vacía, recortada, máximo 200 caracteres.
- Valor numérico mayor que 0, máximo 12 dígitos y 2 decimales.
- Categoría o tipo válido según el tipo de movimiento.
- Fila completamente vacía: se ignora y no se cuenta.
- Los errores deben incluir el número de fila y el campo afectado.
- Los valores inválidos no deben convertirse a `float` para cálculos monetarios.

**Verificación:** una fila inválida queda pendiente con errores de campo; una fila válida sigue el flujo de contabilización.

### FR-004 — Tipos de movimiento y categoría

La importación debe distinguir ingresos y gastos.

- El usuario selecciona un tipo por archivo: `INGRESO` o `GASTO`.
- No se admiten archivos mixtos en esta versión.
- Para gastos, la columna `Categoría` se normaliza a `NECESARIO`, `NO_NECESARIO` o `INVERSION`.
- Se aceptan variantes de mayúsculas, acentos y separadores documentadas.
- Una categoría de gasto desconocida deja la fila pendiente para que el usuario elija el tipo.
- Para ingresos, la categoría es opcional y se conserva como texto libre.
- El tipo de movimiento y la categoría original deben conservarse en la fila de importación para auditoría.

**Verificación:** un gasto con categoría equivalente se contabiliza; una categoría desconocida queda pendiente; un ingreso conserva o marca su categoría según la decisión aprobada.

### FR-005 — Clasificación de filas completas e incompletas

Después de validar cada fila, el sistema debe clasificarla como:

- **Completa:** todos los campos obligatorios son válidos y no requiere revisión.
- **Pendiente:** falta información, hay un valor inválido, la categoría no es reconocible o existe una posible duplicidad.
- **Descartada:** el usuario decidió no contabilizarla.

Las filas completas se contabilizan en la misma operación de importación. Las pendientes se persisten. Las descartadas no afectan la contabilidad.

**Verificación:** un archivo parcial produce movimientos para las filas completas y filas pendientes para el resto.

### FR-006 — Persistencia de lotes y pendientes

Cada importación debe crear un lote persistente con:

- Identificador.
- Nombre del archivo.
- Tipo de archivo.
- Tipo de movimiento.
- Tamaño.
- Número total de filas de datos.
- Número de filas importadas.
- Número de filas pendientes.
- Fecha de creación.

Cada fila de importación debe persistir:

- Lote al que pertenece.
- Número de fila original.
- Tipo de movimiento.
- Fecha, descripción, valor y categoría originales, aunque sean inválidos o estén ausentes.
- Datos crudos necesarios para auditoría.
- Errores de validación.
- Estado: `PENDIENTE`, `IMPORTADO` o `DESCARTADO`.
- Referencia al movimiento creado, si fue importada.

Los pendientes deben sobrevivir a cierres, reinicios y reconstrucciones de la aplicación.

**Verificación:** tras reiniciar los contenedores, los pendientes siguen disponibles y el resumen no cambia.

### FR-007 — Contabilización automática de filas completas

Las filas completas y válidas deben crear movimientos en `ingresos` o `gastos`:

- En una sola transacción con el lote y las filas de importación.
- Sin duplicar movimientos si se reintenta la operación.
- Sin contabilizar filas pendientes o descartadas.
- Actualizando los contadores del lote.
- Manteniendo la referencia entre la fila de importación y el movimiento.

Si falla una operación de base de datos durante el proceso, el lote completo debe revertirse. Los errores de validación de filas no revierten las filas válidas.

**Verificación:** una importación parcial crea solo los movimientos válidos; un fallo de base de datos no deja un lote a medias.

### FR-008 — Bandeja de pendientes

Debe existir una pantalla de pendientes accesible desde la interfaz principal.

- Lista únicamente filas con estado `PENDIENTE`.
- Muestra lote, número de fila, tipo, datos disponibles y errores.
- Permite filtrar por lote si se implementa, pero no es obligatorio en la primera versión.
- Muestra un estado vacío cuando no hay pendientes.
- Es responsive y accesible.
- No muestra datos de filas importadas o descartadas en la vista principal.

**Verificación:** los pendientes aparecen tras una importación parcial y desaparecen al contabilizarlos o descartarlos.

### FR-009 — Edición y guardado de pendientes

El usuario debe poder corregir un pendiente:

- Fecha.
- Descripción.
- Valor.
- Categoría o tipo, según el tipo de movimiento.
- Tipo de gasto cuando la categoría no sea reconocible.

El sistema debe:

- Revalidar después de guardar.
- Actualizar la lista de errores.
- Conservar el estado pendiente mientras haya errores.
- Impedir contabilizar una fila inválida.
- Permitir guardar borradores parciales.

**Verificación:** al corregir todos los campos, la fila deja de tener errores y puede contabilizarse; mientras falte un campo, la contabilización se rechaza.

### FR-010 — Contabilización manual de pendientes

El usuario debe poder contabilizar un pendiente cuando esté completo y válido.

- El backend debe revalidar todos los campos; no confía en el estado del frontend.
- La operación debe ser transaccional.
- Debe crear exactamente un movimiento.
- Debe actualizar la fila a `IMPORTADO`.
- Debe registrar la referencia al movimiento.
- Debe rechazar con `409` si la fila ya fue contabilizada o descartada.
- Debe rechazar con `422` si todavía tiene errores.
- Debe actualizar el resumen y el indicador de pendientes.

**Verificación:** un pendiente válido se contabiliza una vez; un segundo intento no duplica el movimiento.

### FR-011 — Descarte de pendientes

El usuario debe poder descartar un pendiente con confirmación.

- El descarte no crea movimientos.
- El pendiente deja de contar para el indicador.
- El registro se conserva con estado `DESCARTADO` para auditoría.
- Una fila descartada no puede contabilizarse sin una acción explícita de restauración, que queda fuera de alcance.

**Verificación:** tras descartar, el indicador baja y el resumen no cambia.

### FR-012 — Indicador de pendientes

La interfaz debe mostrar un botón o acceso a pendientes con un indicador cuando el conteo sea mayor que cero.

- El conteo debe venir de un endpoint respaldado por PostgreSQL.
- El indicador debe actualizarse después de importar, contabilizar o descartar.
- Debe incluir un texto accesible, no solo color.
- Debe desaparecer cuando el conteo sea cero.
- Un error de red no debe mostrar un conteo inventado; debe mostrar el estado de error correspondiente.

**Verificación:** el indicador refleja el número persistido y se actualiza tras cada mutación.

### FR-013 — Aislamiento de los cálculos financieros

Las filas pendientes, descartadas y los metadatos de importación no deben participar en:

- Total de ingresos.
- Total de gastos.
- Balance.
- Desglose por tipo.
- Cualquier otro indicador financiero.

Solo los movimientos de `ingresos` y `gastos` participan en el resumen.

**Verificación:** pruebas de resumen con pendientes demuestran que los totales son idénticos a los de una base sin pendientes.

### FR-014 — Gestión de duplicados

El sistema debe detectar posibles duplicados sin impedir movimientos legítimos repetidos.

- La detección se basa en una huella normalizada de tipo, fecha, descripción, valor y categoría/tipo.
- Se comparan filas dentro del mismo archivo.
- Se comparan filas con importaciones anteriores.
- Una coincidencia deja la fila pendiente con una advertencia de posible duplicado.
- El usuario puede contabilizarla después de revisarla o descartarla.
- La contabilización de una fila ya importada debe rechazarse con `409`.
- No se aplica una restricción única que prohíba duplicados legítimos.

**Verificación:** dos filas idénticas en un archivo generan una fila pendiente por duplicado; una fila repetida en otra importación se marca para revisión.

### FR-015 — Errores de importación y transacciones

Los errores de archivo deben ser claros y en español:

- Archivo vacío.
- Extensión o tipo no permitido.
- Archivo demasiado grande.
- Demasiadas filas.
- Codificación no soportada.
- Cabeceras faltantes.
- Hoja vacía o sin filas de datos.
- Error de lectura del Excel o CSV.

Los errores de fila se guardan en la fila pendiente, no abortan el archivo completo. Los errores de estructura o de archivo abortan la importación completa sin crear movimientos.

La importación, la contabilización y el descarte deben ser transaccionales y resistentes a reintentos.

**Verificación:** un archivo sin `Valor` no crea movimientos; un archivo con una fila inválida crea pendientes y conserva las filas válidas.

### FR-016 — Seguridad, límites y privacidad

El sistema debe:

- Limitar el tamaño del archivo y la cantidad de filas.
- Validar extensión y tipo de contenido.
- Rechazar hojas de cálculo con macros.
- Evitar path traversal usando solo el nombre base del archivo.
- Leer Excel en modo de solo lectura y sin ejecutar fórmulas.
- No registrar el contenido financiero de las filas en logs.
- No registrar credenciales, rutas internas ni trazas técnicas en la respuesta al usuario.
- No añadir dependencias sin justificación aprobada.

Los límites aprobados son 10 MiB y 5.000 filas de datos por archivo.

**Verificación:** un archivo que supera el límite se rechaza con `413`; un archivo con extensión no permitida se rechaza con `415`; los logs no contienen descripciones ni valores.

### FR-017 — Pantallas de importación y pendientes

La interfaz debe incorporar:

- Un acceso visible a la importación desde la pantalla principal.
- Una pantalla de importación con selector de archivo, selector de tipo, estado de envío, resumen y errores.
- Una pantalla de pendientes con edición, guardado, contabilización y descarte.
- Un botón de regreso a la pantalla principal.
- Un indicador de pendientes en el acceso.
- Estados de carga, error y vacío.
- Etiquetas accesibles, foco visible y navegación por teclado.
- Formato COP y fechas locales en la visualización.

No se usa router ni una librería de estado global. La navegación se resuelve con estado local de la aplicación.

**Verificación:** el usuario puede completar el flujo importar → revisar → corregir → contabilizar/descartar sin recargar la página.

## 5. Requisitos no funcionales

### NFR-001 — Precisión monetaria

Los valores importados, pendientes y contabilizados deben usar `Decimal` en Python y `NUMERIC(12, 2)` en PostgreSQL. No se usa `float` para almacenar, comparar ni calcular dinero.

### NFR-002 — Integridad transaccional

La creación del lote, las filas, los movimientos y las referencias debe ser atómica. Una contabilización no puede crear dos movimientos para la misma fila.

### NFR-003 — Seguridad y privacidad

Los archivos son entradas no confiables. Se validan tamaño, extensión, tipo y estructura. No se ejecutan macros ni fórmulas. Los datos financieros no se escriben en logs.

### NFR-004 — Rendimiento acotado

El procesamiento debe respetar los límites de tamaño y filas. Los archivos se leen de forma secuencial y no se cargan indefinidamente en memoria. La interfaz no debe bloquearse durante la carga.

### NFR-005 — Accesibilidad

Las pantallas nuevas deben usar etiquetas asociadas, mensajes de error accesibles, foco visible, contraste suficiente y estados que no dependan solo del color.

### NFR-006 — Mantenibilidad

Se reutilizan los patrones actuales de FastAPI, SQLAlchemy, Pydantic, React, Vitest y Testing Library. No se crea una arquitectura paralela.

### NFR-007 — Observabilidad segura

Los logs deben incluir identificadores de lote, conteos y estado, pero no valores, descripciones, nombres de archivo con datos sensibles ni credenciales.

### NFR-008 — Compatibilidad

Los endpoints existentes de ingresos, gastos y resumen deben seguir funcionando. Los cambios de contrato deben ser aditivos o estar justificados por esta especificación.

### NFR-009 — Dependencias justificadas

Las dependencias necesarias para Excel y multipart deben añadirse al backend con versión fijada y justificación en el plan. No se añaden dependencias al frontend si la plataforma nativa es suficiente.

### NFR-010 — Pruebas y trazabilidad

Cada regla de importación, persistencia, contabilización, descarte, duplicado y aislamiento financiero debe tener pruebas automatizadas o evidencia explícita.

## 6. Reglas de negocio

- **BR-001:** la aplicación sigue siendo local, de un solo usuario y sin autenticación.
- **BR-002:** un archivo contiene un solo tipo de movimiento: ingresos o gastos.
- **BR-003:** solo las filas completas, válidas y no descartadas pueden contabilizarse.
- **BR-004:** los pendientes no afectan ningún cálculo financiero.
- **BR-005:** la categoría de un gasto se normaliza a `tipo`; una categoría desconocida requiere corrección manual.
- **BR-006:** la categoría de un ingreso es opcional y se almacena en un campo opcional.
- **BR-007:** los duplicados son advertencias, no bloqueos absolutos; el usuario decide.
- **BR-008:** una fila importada no puede volver a contabilizarse.
- **BR-009:** descartar un pendiente no crea ni elimina movimientos contables.
- **BR-010:** eliminar o editar un movimiento ya importado no devuelve automáticamente la fila a pendientes.
- **BR-011:** los archivos y filas respetan los límites aprobados.
- **BR-012:** el indicador de pendientes se obtiene del backend, no de un contador local.

## 7. Casos límite y errores

- Archivo vacío: rechazo con `422`.
- Archivo con extensión no permitida: rechazo con `415`.
- Archivo que supera el tamaño: rechazo con `413`.
- Archivo con más filas que el máximo: rechazo con `422`.
- CSV con codificación no soportada: rechazo con `422` y mensaje claro.
- CSV con delimitador no reconocido: rechazo si no se pueden identificar columnas.
- Excel sin hojas o con hoja vacía: rechazo con `422`.
- Excel con múltiples hojas: se procesa solo la primera; se informa en la respuesta.
- Cabeceras faltantes: rechazo completo sin movimientos.
- Cabeceras con alias válidos: se aceptan.
- Columnas adicionales: se ignoran.
- Fila vacía: se omite.
- Fecha ausente o inválida: pendiente.
- Descripción ausente, vacía o demasiado larga: pendiente.
- Valor ausente, no numérico, cero o negativo: pendiente.
- Valor con más de 2 decimales o más de 12 dígitos: pendiente.
- Categoría de gasto desconocida: pendiente.
- Categoría de ingreso según decisión pendiente: pendiente o se conserva.
- Fila duplicada: pendiente con advertencia.
- Archivo repetido: sus filas se comparan con importaciones anteriores y se marcan como posibles duplicados.
- Fila válida e inválida en el mismo archivo: las válidas se contabilizan; las inválidas quedan pendientes.
- Fallo de base de datos durante la importación: rollback del lote completo.
- Fallo al contabilizar: no se crea el movimiento ni se marca la fila.
- Contabilización concurrente: una operación gana; la otra recibe `409`.
- Movimiento importado eliminado: la fila conserva su estado de importada; no se reencola automáticamente.
- Movimiento importado editado: la fila no se modifica automáticamente.
- Error de red al cargar el indicador: la interfaz muestra error; no inventa un conteo.
- Nginx con límite de cuerpo menor que el archivo: se devuelve un error controlado; el límite debe configurarse de forma coherente.

## 8. Fuera de alcance

- Exportación a Excel o CSV.
- Importación desde PDF, `.xls`, `.xlsm`, `.xlsb`, Google Sheets, APIs bancarias o correo.
- Macros y ejecución de fórmulas.
- Procesamiento de varias hojas del mismo libro.
- Mapeo interactivo de columnas o previsualización completa antes de importar.
- Categorías configurables, árbol de categorías o gestión de presupuestos.
- Detección automática de duplicados contra movimientos manuales que no provienen de importaciones.
- Fusión automática de duplicados.
- Historial completo de importaciones en la interfaz.
- Restauración de pendientes descartados.
- Edición masiva.
- Importación programada o en segundo plano.
- Autenticación, multiusuario, Internet, TLS o acceso remoto.
- Paginación de pendientes si el volumen máximo no lo exige.
- Cambios en la arquitectura general o en el resumen financiero.

## 9. Criterios de aceptación verificables

| ID | Criterio | Evidencia |
|---|---|---|
| AC-001 | Un CSV válido de ingresos se importa y crea movimientos. | Prueba de API e integración. |
| AC-002 | Un XLSX válido de gastos se importa y crea movimientos. | Prueba de API e integración. |
| AC-003 | Las cabeceras se identifican con alias y sin distinguir mayúsculas/acentos. | Pruebas del parser. |
| AC-004 | Las filas incompletas o inválidas quedan pendientes y no crean movimientos. | Prueba de importación parcial. |
| AC-005 | Los pendientes persisten tras reiniciar la aplicación. | Prueba de integración y reinicio de contenedores. |
| AC-006 | Un pendiente se puede corregir, guardar y contabilizar. | Pruebas de API y frontend. |
| AC-007 | Un pendiente se puede descartar sin afectar la contabilidad. | Pruebas de API y frontend. |
| AC-008 | El indicador de pendientes viene del backend y se actualiza. | Prueba de conteo y componentes. |
| AC-009 | Los duplicados se marcan como pendientes para revisión. | Pruebas del detector y API. |
| AC-010 | Los archivos inválidos producen errores claros y no crean movimientos. | Pruebas de archivos vacíos, extensión, tamaño y cabeceras. |
| AC-011 | Los límites de tamaño y filas se aplican. | Pruebas de límites y respuesta `413`/`422`. |
| AC-012 | Una fila no puede contabilizarse dos veces. | Prueba de concurrencia/reintento. |
| AC-013 | Los pendientes no alteran el resumen financiero. | Prueba comparativa de resumen. |
| AC-014 | Las pantallas de importación y pendientes son accesibles y responsive. | Pruebas de componentes y revisión visual. |
| AC-015 | Las pruebas y validaciones de backend y frontend pasan. | Comandos canónicos. |
| AC-016 | La documentación refleja el contrato y los límites aprobados. | Revisión de README, AGENTS y esta especificación. |

## 10. Decisiones de negocio y supuestos

Las decisiones D-001 a D-012 fueron revisadas y aprobadas. Se conservan las alternativas e impactos como contexto para la implementación.

### D-001 — Tipo de movimiento por archivo

**Propuesta:** un archivo contiene solo ingresos o solo gastos; el usuario selecciona el tipo antes de subirlo.

**Alternativas:** detectar el tipo por categoría, admitir archivos mixtos o añadir una columna de tipo.

**Impacto:** afecta el formulario de carga, el parser, el modelo de lote y la validación de categoría.

**Decisión aprobada:** se acepta la propuesta.

### D-002 — Categoría de los ingresos

**Propuesta:** añadir `categoria` opcional a `ingresos`, conservarla en el movimiento y mostrarla en la interfaz de ingresos.

**Alternativas:** ignorar la categoría de ingresos; guardarla solo en la fila de importación; añadir una tabla de categorías.

**Impacto:** migración, schemas, contrato de la API, formularios y listados de ingresos.

**Decisión aprobada:** se acepta la propuesta siempre y cuando el campo `categoria` sea opcional en los ingresos. No será obligatorio para crear ni editar un ingreso.

### D-003 — Categoría de los gastos

**Propuesta:** `Categoría` se normaliza a `tipo` (`NECESARIO`, `NO_NECESARIO`, `INVERSION`); no se añade una categoría libre a `gastos`.

**Alternativas:** añadir `categoria` libre a `gastos`; usar una tabla de categorías; aceptar solo valores exactos.

**Impacto:** normalización, pendientes y modelo de gastos.

**Decisión aprobada:** se acepta la propuesta.

### D-004 — Contabilización automática de filas completas

**Propuesta:** las filas completas y válidas se contabilizan durante la importación; las incompletas quedan pendientes.

**Alternativa:** previsualizar todo y requerir confirmación antes de crear movimientos.

**Impacto:** flujo de usuario, transacciones y respuesta de la API.

**Decisión aprobada:** se acepta la propuesta.

### D-005 — Duplicados

**Propuesta:** marcar el duplicado como pendiente con advertencia; el usuario decide si contabiliza o descarta. No se aplica una restricción única.

**Alternativas:** rechazar automáticamente; importar automáticamente; comparar también con movimientos manuales.

**Impacto:** huella, estados, bandeja de pendientes y riesgo de doble contabilización.

**Decisión aprobada:** se acepta la propuesta.

### D-006 — Guardado de pendientes inválidos

**Propuesta:** permitir guardar cambios parciales aunque sigan existiendo errores; la contabilización exige validación completa.

**Alternativa:** rechazar el guardado hasta que todos los campos sean válidos.

**Impacto:** UX, esquemas de actualización y errores.

**Decisión aprobada:** se acepta la propuesta.

### D-007 — Descarte

**Propuesta:** descarte lógico con estado `DESCARTADO`, sin borrar la fila. El indicador excluye descartados.

**Alternativa:** borrado físico de la fila pendiente.

**Impacto:** auditoría, conteo y modelo de datos.

**Decisión aprobada:** se acepta la propuesta.

### D-008 — Movimiento importado editado o eliminado

**Propuesta:** la fila de importación conserva su estado y auditoría; no se reencola automáticamente. Si el movimiento se elimina, la referencia puede quedar nula.

**Alternativas:** reencolar el pendiente al eliminar; borrar la fila de importación; impedir la eliminación.

**Impacto:** integridad referencial y comportamiento del usuario.

**Decisión aprobada:** se acepta la propuesta.

### D-009 — Límites de archivo

**Propuesta:** 10 MiB y 5.000 filas de datos por archivo.

**Alternativas:** otros límites según uso real.

**Impacto:** validación, Nginx, rendimiento y mensajes de error.

**Decisión aprobada:** se acepta la propuesta.

### D-010 — Formatos de fecha, valor y codificación

**Propuesta:**

- Excel: celdas de fecha y números.
- CSV: UTF-8 con BOM opcional; fechas ISO `YYYY-MM-DD` o `DD/MM/YYYY`.
- Valores: punto o coma decimal, sin símbolos de moneda; se normalizan a `Decimal`.

**Alternativas:** aceptar más formatos locales, detectar codificaciones, aceptar símbolos y separadores de miles.

**Impacto:** parser, normalización y pruebas.

**Decisión aprobada:** se acepta la propuesta.

### D-011 — Hojas y columnas adicionales

**Propuesta:** procesar solo la primera hoja; ignorar columnas adicionales; aceptar alias de cabecera.

**Alternativas:** rechazar columnas adicionales o permitir seleccionar hoja.

**Impacto:** parser y mensajes de error.

**Decisión aprobada:** se acepta la propuesta.

### D-012 — Historial de importaciones

**Propuesta:** no incluir una pantalla de historial en esta versión; conservar lotes y filas para auditoría y para el futuro.

**Alternativa:** añadir historial ahora.

**Impacto:** alcance de frontend y endpoints.

**Decisión aprobada:** se acepta la propuesta. El historial no se implementa en la especificación 007.

**Visión futura del historial:** en una especificación posterior, el historial mostrará los lotes ordenados por fecha descendente, con nombre de archivo, tipo de movimiento, total de filas, filas importadas, pendientes y descartadas. Permitirá abrir un lote para consultar sus filas y volver a los pendientes que sigan abiertos. No incluirá edición masiva ni reimportación automática.

### Supuestos técnicos que no requieren decisión de negocio

- Se usa `Decimal` y `NUMERIC(12, 2)`.
- Los pendientes se guardan en tablas separadas de `ingresos` y `gastos`.
- El resumen no se modifica para incluir pendientes.
- La importación se procesa en una transacción por lote.
- La contabilización de un pendiente se hace con bloqueo y revalidación en el servidor.
- El frontend no parsea archivos; solo los envía.
- La API conserva el contrato en español y el código interno en inglés.
- No se modifica `legacy/`.

### Estado de las decisiones

No quedan preguntas de negocio pendientes. Las decisiones D-001 a D-012 están aprobadas; el plan y las tareas también están aprobados. La implementación avanza por tareas.

## 11. Resultado de validación

Pendiente. Se completa al implementar y validar la especificación.
