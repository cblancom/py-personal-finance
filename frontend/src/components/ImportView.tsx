import { useRef, useState, type FormEvent } from 'react'
import { ApiError } from '../api/client'
import { uploadImport } from '../api/imports'
import type {
  ImportBatch,
  ImportMovementType,
} from '../types/import'

interface ImportViewProps {
  onBack: () => void
  onImported: (batch: ImportBatch) => void | Promise<void>
  onOpenPending?: () => void
}

function fileCountLabel(count: number): string {
  return `${count} ${count === 1 ? 'fila' : 'filas'}`
}

function importErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 413) {
      return 'El archivo es demasiado grande.'
    }
    if (error.status === 415) {
      return 'El archivo debe ser CSV o XLSX.'
    }
    if (error.status === 422) {
      return 'El archivo no tiene el formato esperado.'
    }
  }
  return 'No se pudo importar el archivo. Inténtalo de nuevo.'
}

export function ImportView({
  onBack,
  onImported,
  onOpenPending,
}: ImportViewProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [movementType, setMovementType] =
    useState<ImportMovementType>('INGRESO')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ImportBatch | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (file === null) {
      setError('Selecciona un archivo CSV o XLSX.')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const batch = await uploadImport(file, movementType)
      setResult(batch)
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      await onImported(batch)
    } catch (caught) {
      setError(importErrorMessage(caught))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="import-view" aria-labelledby="import-title">
      <div className="view-header">
        <div>
          <h2 id="import-title">Importar movimientos</h2>
          <p>
            Sube un archivo CSV o XLSX con fecha, descripción, valor y
            categoría.
          </p>
        </div>
        <button type="button" className="button button--ghost" onClick={onBack}>
          Volver
        </button>
      </div>

      <form className="import-form" onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="import-file">Archivo CSV o XLSX</label>
          <input
            ref={fileInputRef}
            id="import-file"
            type="file"
            accept=".csv,.xlsx"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null)
              setError(null)
              setResult(null)
            }}
            disabled={submitting}
          />
        </div>

        <div className="field">
          <label htmlFor="import-movement-type">Tipo de movimiento</label>
          <select
            id="import-movement-type"
            value={movementType}
            onChange={(event) => {
              setMovementType(event.target.value as ImportMovementType)
              setError(null)
              setResult(null)
            }}
            disabled={submitting}
          >
            <option value="INGRESO">Ingreso</option>
            <option value="GASTO">Gasto</option>
          </select>
        </div>

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <div className="form-actions">
          <button
            type="submit"
            className="button button--primary"
            disabled={submitting || file === null}
          >
            {submitting ? 'Importando...' : 'Importar archivo'}
          </button>
        </div>
      </form>

      {result && (
        <section
          className="import-result"
          aria-live="polite"
          aria-labelledby="import-result-title"
        >
          <h3 id="import-result-title">Resultado de la importación</h3>
          <p>
            {result.nombre_archivo}: {fileCountLabel(result.total_filas)} en
            total.
          </p>
          <dl>
            <div>
              <dt>Importadas</dt>
              <dd>{fileCountLabel(result.filas_importadas)}</dd>
            </div>
            <div>
              <dt>Pendientes</dt>
              <dd>{fileCountLabel(result.filas_pendientes)}</dd>
            </div>
            <div>
              <dt>Descartadas</dt>
              <dd>{fileCountLabel(result.filas_descartadas)}</dd>
            </div>
          </dl>
          {result.filas_pendientes > 0 && onOpenPending && (
            <button
              type="button"
              className="button button--ghost"
              onClick={onOpenPending}
            >
              Revisar pendientes
            </button>
          )}
        </section>
      )}
    </section>
  )
}
