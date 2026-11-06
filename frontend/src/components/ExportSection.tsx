import { useState } from 'react'
import { downloadExpenses, downloadIncomes } from '../api/exports'
import type { ExportFormat } from '../types/export'

type ExportResource = 'incomes' | 'expenses'

export function ExportSection() {
  const [format, setFormat] = useState<ExportFormat>('csv')
  const [downloading, setDownloading] = useState<ExportResource | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleDownload(resource: ExportResource) {
    setDownloading(resource)
    setError(null)

    try {
      if (resource === 'incomes') {
        await downloadIncomes(format)
      } else {
        await downloadExpenses(format)
      }
    } catch {
      setError('No se pudo exportar el archivo. Inténtalo de nuevo.')
    } finally {
      setDownloading(null)
    }
  }

  const disabled = downloading !== null

  return (
    <section
      className="export-section"
      aria-labelledby="export-title"
      aria-busy={downloading !== null}
    >
      <h3 id="export-title">Exportar movimientos</h3>
      <p>
        Descarga un respaldo de tus movimientos guardados para volver a
        importarlo cuando lo necesites.
      </p>

      <div className="export-controls">
        <div className="field">
          <label htmlFor="export-format">Formato</label>
          <select
            id="export-format"
            value={format}
            onChange={(event) =>
              setFormat(event.target.value as ExportFormat)
            }
            disabled={disabled}
          >
            <option value="csv">CSV</option>
            <option value="xlsx">XLSX</option>
          </select>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="button button--ghost"
            onClick={() => void handleDownload('incomes')}
            disabled={disabled}
          >
            {downloading === 'incomes' ? 'Preparando...' : 'Exportar ingresos'}
          </button>
          <button
            type="button"
            className="button button--ghost"
            onClick={() => void handleDownload('expenses')}
            disabled={disabled}
          >
            {downloading === 'expenses' ? 'Preparando...' : 'Exportar gastos'}
          </button>
        </div>
      </div>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </section>
  )
}
