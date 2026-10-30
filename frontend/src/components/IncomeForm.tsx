import { useState, type FormEvent } from 'react'
import type { Income, IncomePayload } from '../types/income'
import { todayIsoDate } from '../utils/format'
import { validateMovementInput } from '../utils/validation'

interface IncomeFormProps {
  initial?: Income | null
  submitting: boolean
  onSubmit: (payload: IncomePayload) => void
  onCancelEdit?: () => void
}

export function IncomeForm({
  initial = null,
  submitting,
  onSubmit,
  onCancelEdit,
}: IncomeFormProps) {
  const isEditing = initial !== null
  const [fecha, setFecha] = useState(initial?.fecha ?? todayIsoDate())
  const [descripcion, setDescripcion] = useState(initial?.descripcion ?? '')
  const [categoria, setCategoria] = useState(initial?.categoria ?? '')
  const [valor, setValor] = useState(initial?.valor ?? '')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const validationError = validateMovementInput({ fecha, descripcion, valor })
    if (validationError) {
      setError(validationError)
      return
    }

    setError(null)
    onSubmit({
      fecha,
      descripcion: descripcion.trim(),
      categoria: categoria.trim() || null,
      valor,
    })
  }

  return (
    <form className="movement-form" onSubmit={handleSubmit} noValidate>
      <h3>{isEditing ? 'Editar ingreso' : 'Nuevo ingreso'}</h3>

      <div className="field">
        <label htmlFor="income-fecha">Fecha</label>
        <input
          id="income-fecha"
          type="date"
          value={fecha}
          onChange={(event) => setFecha(event.target.value)}
          disabled={submitting}
        />
      </div>

      <div className="field">
        <label htmlFor="income-descripcion">Descripción</label>
        <input
          id="income-descripcion"
          type="text"
          maxLength={200}
          value={descripcion}
          onChange={(event) => setDescripcion(event.target.value)}
          disabled={submitting}
        />
      </div>

      <div className="field">
        <label htmlFor="income-categoria">Categoría (opcional)</label>
        <input
          id="income-categoria"
          type="text"
          maxLength={100}
          value={categoria}
          onChange={(event) => setCategoria(event.target.value)}
          disabled={submitting}
        />
      </div>

      <div className="field">
        <label htmlFor="income-valor">Valor</label>
        <input
          id="income-valor"
          type="number"
          min="0.01"
          step="0.01"
          value={valor}
          onChange={(event) => setValor(event.target.value)}
          disabled={submitting}
        />
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
          disabled={submitting}
        >
          {submitting
            ? 'Guardando...'
            : isEditing
              ? 'Guardar cambios'
              : 'Guardar ingreso'}
        </button>
        {isEditing && onCancelEdit && (
          <button
            type="button"
            className="button button--ghost"
            onClick={onCancelEdit}
            disabled={submitting}
          >
            Cancelar edición
          </button>
        )}
      </div>
    </form>
  )
}
