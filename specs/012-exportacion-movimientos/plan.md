# Plan técnico 012 — Exportación de ingresos y gastos

- Estado: validado (T-001 a T-006 completadas).
- Especificación: [`spec.md`](spec.md).
- Fase: 10.
- Iteración: 1.3.0.

## 1. Resumen de la solución

Se añade una exportación de movimientos reimportable:

- `GET /api/exportaciones/ingresos?formato=csv|xlsx`
- `GET /api/exportaciones/gastos?formato=csv|xlsx`

Los archivos usan las mismas cabeceras y reglas que la importación. La interfaz añade una sección `Exportar movimientos` dentro de `ImportView` y renombra el botón principal de `Importar` a `Importar/Exportar`.

No se añaden dependencias: CSV con la biblioteca estándar y XLSX con `openpyxl`, ya instalado.

## 2. Contrato de API

### Endpoints

```text
GET /api/exportaciones/ingresos?formato=csv
GET /api/exportaciones/ingresos?formato=xlsx
GET /api/exportaciones/gastos?formato=csv
GET /api/exportaciones/gastos?formato=xlsx
```

`formato` es obligatorio y acepta `csv` o `xlsx`. Cualquier otro valor devuelve `422`.

### Respuesta

- `200` con el archivo como adjunto.
- `Content-Disposition: attachment; filename="ingresos_YYYYMMDD_HHMMSS.csv"`.
- `Content-Type: text/csv; charset=utf-8` para CSV.
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` para XLSX.
- `422` para formato inválido.

### Columnas

Ingresos:

```text
Fecha,Descripcion,Valor,Categoria
```

Gastos:

```text
Fecha,Descripcion,Valor,Tipo de gasto
```

Reglas:

- `Fecha` en ISO `YYYY-MM-DD`.
- `Valor` como string con dos decimales.
- Ingresos sin tipo: `Categoria` vacía.
- Gastos: `Tipo de gasto` con `NECESARIO`, `NO_NECESARIO` o `INVERSION`.
- Orden `fecha ASC, id ASC`.
- Sin filas: solo cabecera.

## 3. Backend

### Servicio

Crear `backend/app/services/exports.py` con funciones puras para construir los bytes:

```text
export_incomes_csv(incomes) -> bytes
export_incomes_xlsx(incomes) -> bytes
export_expenses_csv(expenses) -> bytes
export_expenses_xlsx(expenses) -> bytes
```

O una función común con tipo de movimiento y formato. La consulta a base de datos se hace en la ruta o en un helper del servicio.

### CSV

- `csv.writer` con `lineterminator="\n"`.
- `io.StringIO` y codificación final `utf-8-sig` para incluir BOM.
- Delimitador coma y decimal con punto.
- `csv.writer` se encarga de citar comas, comillas y saltos de línea.

### XLSX

- `openpyxl.Workbook`.
- Una hoja: `Ingresos` o `Gastos`.
- Cabecera en la fila 1.
- Fechas como string ISO y valores como string con dos decimales para preservar precisión.
- Guardar en `BytesIO` y devolver `getvalue()`.

### Rutas

Crear `backend/app/api/routes/exports.py`:

- `APIRouter(prefix="/exportaciones", tags=["exportaciones"])`.
- `GET /ingresos` y `GET /gastos`.
- Validar `formato` con `Literal["csv", "xlsx"]` o enum.
- Consultar ingresos/gastos con `select(...).order_by(fecha, id)`.
- Devolver `Response` con bytes, MIME y `Content-Disposition`.

Registrar el router en `backend/app/main.py` con `prefix="/api"`.

No se crea migración ni tabla.

## 4. Frontend

### Cliente API

Crear `frontend/src/api/exports.ts`:

```text
downloadIncomes(format: ExportFormat): Promise<DownloadedFile>
downloadExpenses(format: ExportFormat): Promise<DownloadedFile>
```

La descarga:

1. Hace `fetch` a `/api/exportaciones/...`.
2. Comprueba `response.ok` y lanza `ApiError` si falla.
3. Obtiene `response.blob()`.
4. Lee `Content-Disposition` para el nombre o construye el nombre en el cliente.
5. Crea un enlace temporal y dispara la descarga.

No se reutiliza `request()` porque este espera JSON.

### Componente

Crear `frontend/src/components/ExportSection.tsx`:

- Selector `Formato` con `CSV` y `XLSX`.
- Botones `Exportar ingresos` y `Exportar gastos`.
- Estado `Preparando...` por botón.
- Error visible con `role="alert"`.
- Sin navegación ni estado global.

Integrarlo en `ImportView`, debajo del formulario de importación.

### Cabecera

Cambiar el botón de `App.tsx` de `Importar` a `Importar/Exportar`.

La vista puede mantener el título `Importar movimientos` o cambiarlo a `Importar/Exportar movimientos`; se recomienda el segundo para coherencia.

## 5. Compatibilidad con la importación

La prueba principal es de ida y vuelta:

1. Crear ingresos y gastos de prueba en la base de test.
2. Exportar ingresos y gastos en CSV y XLSX.
3. Importar cada archivo con el `tipo_movimiento` correspondiente.
4. Comparar fecha, descripción, valor y tipo.

También se prueba con:

- Descripciones con acentos.
- Descripciones con comas y comillas.
- Descripciones con saltos de línea.
- Ingresos sin tipo.
- Gastos de los tres tipos.
- Exportaciones vacías.

## 6. Archivos afectados

### Backend

- `backend/app/services/exports.py`
- `backend/app/api/routes/exports.py`
- `backend/app/main.py`
- `backend/tests/api/test_exports_schema.py` o equivalente
- `backend/tests/api/test_exports_openapi.py`
- `backend/tests/integration/test_exports.py`

### Frontend

- `frontend/src/api/exports.ts`
- `frontend/src/api/exports.test.ts`
- `frontend/src/components/ExportSection.tsx`
- `frontend/src/components/ExportSection.test.tsx`
- `frontend/src/components/ImportView.tsx`
- `frontend/src/components/ImportView.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/index.css` solo si la sección necesita estilos nuevos.

### Documentación y versión

- `README.md` con los endpoints y el alcance del backup.
- `AGENTS.md` al validar.
- `specs/README.md` con la fila 012.
- Metadatos de versión `1.3.0` al publicar.

## 7. Pruebas

### Backend

```bash
cd backend
uv run pytest tests/api/test_exports_schema.py tests/api/test_exports_openapi.py tests/integration/test_exports.py
uv run ruff check .
uv run ruff format --check .
```

Casos:

- CSV de ingresos y gastos.
- XLSX de ingresos y gastos.
- Cabeceras y MIME.
- `Content-Disposition`.
- Formato inválido.
- Exportación vacía.
- Ida y vuelta con importación.
- Caracteres especiales.

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

Casos:

- Cliente de descarga con `fetch` y `blob`.
- Botones de ingresos y gastos.
- Selector CSV/XLSX.
- Estado `Preparando...`.
- Error visible.
- Botón `Importar/Exportar` en `App`.
- Sección de exportación en `ImportView`.

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Archivo no reimportable | Prueba de ida y vuelta con el parser real. |
| Pérdida de precisión monetaria | Serializar `Decimal` como string con dos decimales. |
| CSV mal interpretado por Excel | UTF-8 con BOM y comillas estándar. |
| Descripciones con comas o saltos | Usar `csv.writer` y probar casos especiales. |
| Duplicados al reimportar | Documentar que la restauración es sobre base limpia. |
| Confusión con backup completo | Documentar que no incluye asignaciones, pendientes ni historial. |
| Memoria con muchos movimientos | Aceptable para el MVP local; sin streaming en esta versión. |

## 9. Aprobación y siguiente paso

La especificación 012 está aprobada en sus decisiones D-001 a D-005. El plan fue aprobado y T-001 a T-006 quedaron completadas y validadas.

No se modifica `legacy/`. No se añaden dependencias. No se altera la importación existente.
