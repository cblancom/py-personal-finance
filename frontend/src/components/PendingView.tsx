import { useEffect, useState } from 'react'
import { ErrorBanner } from './ErrorBanner'
import {
  commitPending,
  discardPending,
  listPending,
  updatePending,
} from '../api/imports'
import { EXPENSE_TYPES, type ExpenseType } from '../types/expense'
import type {
  ImportPendingRow,
  ImportPendingUpdate,
} from '../types/import'
import { expenseTypeLabel } from '../utils/format'

interface PendingViewProps {
  onBack: () => void
  onChanged: () => void | Promise<void>
}

interface Draft {
  fecha: string
  descripcion: string
  valor: string
  categoria: string
  tipo_gasto: ExpenseType | ''
}

function toDraft(row: ImportPendingRow): Draft {
  return {
    fecha: row.fecha ?? '',
    descripcion: row.descripcion ?? '',
    valor: row.valor ?? '',
    categoria: row.categoria ?? '',
    tipo_gasto: row.tipo_gasto ?? '',
  }
}

function draftToPayload(
  row: ImportPendingRow,
  draft: Draft,
): ImportPendingUpdate {
  const payload: ImportPendingUpdate = {
    fecha: draft.fecha || null,
    descripcion: draft.descripcion || null,
    valor: draft.valor || null,
    categoria: draft.categoria || null,
  }
  if (row.tipo_movimiento === 'GASTO') {
    payload.tipo_gasto = draft.tipo_gasto || null
  }
  return payload
}

export function PendingView({ onBack, onChanged }: PendingViewProps) {
  const [rows, setRows] = useState<ImportPendingRow[]>([])
  const [drafts, setDrafts] = useState<Record<number, Draft>>({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [loadVersion, setLoadVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    async function load() {
      setLoading(true)
      setLoadError(null)

      try {
        const pending = await listPending(controller.signal)
        if (!active) {
          return
        }
        setRows(pending)
        setDrafts(
          Object.fromEntries(
            pending.map((row) => [row.id, toDraft(row)]),
          ) as Record<number, Draft>,
        )
      } catch {
        if (active) {
          setLoadError('No se pudieron cargar los pendientes.')
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      active = false
      controller.abort()
    }
  }, [loadVersion])

  function updateDraft<K extends keyof Draft>(
    id: number,
    field: K,
    value: Draft[K],
  ) {
    setDrafts((current) => ({
      ...current,
      [id]: {
        ...current[id],
        [field]: value,
      },
    }))
  }

  async function handleSave(row: ImportPendingRow) {
    const draft = drafts[row.id]
    if (!draft) {
      return
    }

    setBusyId(row.id)
    setActionError(null)

    try {
      const updated = await updatePending(
        row.id,
        draftToPayload(row, draft),
      )
      setRows((current) =>
        current.map((item) => (item.id === row.id ? updated : item)),
      )
      setDrafts((current) => ({
        ...current,
        [row.id]: toDraft(updated),
      }))
    } catch {
      setActionError(
        'No se pudo guardar el pendiente. Revisa los datos e inténtalo de nuevo.',
      )
    } finally {
      setBusyId(null)
    }
  }

  async function handleCommit(row: ImportPendingRow) {
    setBusyId(row.id)
    setActionError(null)

    try {
      await commitPending(row.id)
      setRows((current) => current.filter((item) => item.id !== row.id))
      await onChanged()
    } catch {
      setActionError(
        'No se pudo contabilizar el pendiente. Revisa los errores e inténtalo de nuevo.',
      )
      setLoadVersion((version) => version + 1)
    } finally {
      setBusyId(null)
    }
  }

  async function handleDiscard(row: ImportPendingRow) {
    if (!window.confirm('¿Descartar este registro pendiente?')) {
      return
    }

    setBusyId(row.id)
    setActionError(null)

    try {
      await discardPending(row.id)
      setRows((current) => current.filter((item) => item.id !== row.id))
      await onChanged()
    } catch {
      setActionError('No se pudo descartar el pendiente. Inténtalo de nuevo.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <section className="pending-view" aria-labelledby="pending-title">
      <div className="view-header">
        <div>
          <h2 id="pending-title">Pendientes</h2>
          <p>
            Corrige los registros incompletos antes de incorporarlos a la
            contabilidad.
          </p>
        </div>
        <button type="button" className="button button--ghost" onClick={onBack}>
          Volver
        </button>
      </div>

      {loading && (
        <p className="status-message" role="status">
          Cargando pendientes...
        </p>
      )}

      {loadError && (
        <ErrorBanner
          message={loadError}
          onRetry={() => setLoadVersion((version) => version + 1)}
        />
      )}

      {actionError && (
        <p className="form-error" role="alert">
          {actionError}
        </p>
      )}

      {!loading && !loadError && rows.length === 0 && (
        <p className="empty-state">No hay registros pendientes.</p>
      )}

      {!loading && rows.length > 0 && (
        <div className="pending-list">
          {rows.map((row) => {
            const draft = drafts[row.id] ?? toDraft(row)
            const isBusy = busyId === row.id
            const validationErrors = row.errores.filter(
              (error) => error.campo !== 'duplicado',
            )
            const canCommit = validationErrors.length === 0 && !isBusy

            return (
              <article
                key={row.id}
                className="pending-row"
                aria-labelledby={`pending-${row.id}-title`}
              >
                <h3 id={`pending-${row.id}-title`}>
                  {row.descripcion ?? 'Registro sin descripción'}
                </h3>
                <p className="pending-row__meta">
                  Lote {row.lote_id}, fila {row.numero_fila} ·{' '}
                  {row.tipo_movimiento === 'INGRESO' ? 'Ingreso' : 'Gasto'}
                </p>

                {row.posible_duplicado && (
                  <p className="pending-warning" role="status">
                    Posible duplicado: revisa el registro antes de
                    contabilizarlo.
                  </p>
                )}

                {validationErrors.length > 0 && (
                  <ul className="pending-errors" role="alert">
                    {validationErrors.map((error) => (
                      <li key={`${error.campo}-${error.mensaje}`}>
                        {error.mensaje}
                      </li>
                    ))}
                  </ul>
                )}

                <div className="pending-row__fields">
                  <div className="field">
                    <label htmlFor={`pending-${row.id}-fecha`}>Fecha</label>
                    <input
                      id={`pending-${row.id}-fecha`}
                      type="date"
                      value={draft.fecha}
                      onChange={(event) =>
                        updateDraft(row.id, 'fecha', event.target.value)
                      }
                      disabled={isBusy}
                    />
                  </div>

                  <div className="field">
                    <label htmlFor={`pending-${row.id}-descripcion`}>
                      Descripción
                    </label>
                    <input
                      id={`pending-${row.id}-descripcion`}
                      type="text"
                      maxLength={200}
                      value={draft.descripcion}
                      onChange={(event) =>
                        updateDraft(row.id, 'descripcion', event.target.value)
                      }
                      disabled={isBusy}
                    />
                  </div>

                  <div className="field">
                    <label htmlFor={`pending-${row.id}-valor`}>Valor</label>
                    <input
                      id={`pending-${row.id}-valor`}
                      type="text"
                      inputMode="decimal"
                      value={draft.valor}
                      onChange={(event) =>
                        updateDraft(row.id, 'valor', event.target.value)
                      }
                      disabled={isBusy}
                    />
                  </div>

                  <div className="field">
                    <label htmlFor={`pending-${row.id}-categoria`}>
                      Categoría
                    </label>
                    <input
                      id={`pending-${row.id}-categoria`}
                      type="text"
                      maxLength={100}
                      value={draft.categoria}
                      onChange={(event) =>
                        updateDraft(row.id, 'categoria', event.target.value)
                      }
                      disabled={isBusy}
                    />
                  </div>

                  {row.tipo_movimiento === 'GASTO' && (
                    <div className="field">
                      <label htmlFor={`pending-${row.id}-tipo`}>
                        Tipo de gasto
                      </label>
                      <select
                        id={`pending-${row.id}-tipo`}
                        value={draft.tipo_gasto}
                        onChange={(event) =>
                          updateDraft(
                            row.id,
                            'tipo_gasto',
                            event.target.value as ExpenseType | '',
                          )
                        }
                        disabled={isBusy}
                      >
                        <option value="">Sin tipo</option>
                        {EXPENSE_TYPES.map((type) => (
                          <option key={type} value={type}>
                            {expenseTypeLabel(type)}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>

                <div className="pending-row__actions">
                  <button
                    type="button"
                    className="button button--primary"
                    onClick={() => void handleSave(row)}
                    disabled={isBusy}
                  >
                    {isBusy ? 'Guardando...' : 'Guardar'}
                  </button>
                  <button
                    type="button"
                    className="button button--ghost"
                    onClick={() => void handleCommit(row)}
                    disabled={!canCommit}
                  >
                    Contabilizar
                  </button>
                  <button
                    type="button"
                    className="button button--link"
                    onClick={() => void handleDiscard(row)}
                    disabled={isBusy}
                  >
                    Descartar
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
