import { useState, type FormEvent } from 'react'
import {
  EXPENSE_TYPES,
  type Expense,
  type ExpensePayload,
  type ExpenseType,
} from '../types/expense'
import { expenseTypeLabel, todayIsoDate } from '../utils/format'
import { validateMovementInput } from '../utils/validation'

interface ExpenseFormProps {
  initial?: Expense | null
  submitting: boolean
  onSubmit: (payload: ExpensePayload) => void
  onCancelEdit?: () => void
}

export function ExpenseForm({
  initial = null,
  submitting,
  onSubmit,
  onCancelEdit,
}: ExpenseFormProps) {
  const isEditing = initial !== null
  const [fecha, setFecha] = useState(initial?.fecha ?? todayIsoDate())
  const [descripcion, setDescripcion] = useState(initial?.descripcion ?? '')
  const [tipo, setTipo] = useState<ExpenseType>(
    initial?.tipo ?? 'NECESARIO',
  )
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
      tipo,
      valor,
    })
  }

  return (
    <form className="movement-form" onSubmit={handleSubmit} noValidate>
      <h3>{isEditing ? 'Editar gasto' : 'Nuevo gasto'}</h3>

      <div className="field">
        <label htmlFor="expense-fecha">Fecha</label>
        <input
          id="expense-fecha"
          type="date"
          value={fecha}
          onChange={(event) => setFecha(event.target.value)}
          disabled={submitting}
        />
      </div>

      <div className="field">
        <label htmlFor="expense-descripcion">Descripción</label>
        <input
          id="expense-descripcion"
          type="text"
          maxLength={200}
          value={descripcion}
          onChange={(event) => setDescripcion(event.target.value)}
          disabled={submitting}
        />
      </div>

      <div className="field">
        <label htmlFor="expense-tipo">Tipo</label>
        <select
          id="expense-tipo"
          value={tipo}
          onChange={(event) => setTipo(event.target.value as ExpenseType)}
          disabled={submitting}
        >
          {EXPENSE_TYPES.map((option) => (
            <option key={option} value={option}>
              {expenseTypeLabel(option)}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label htmlFor="expense-valor">Valor</label>
        <input
          id="expense-valor"
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
        <button type="submit" disabled={submitting}>
          {submitting
            ? 'Guardando...'
            : isEditing
              ? 'Guardar cambios'
              : 'Guardar gasto'}
        </button>
        {isEditing && onCancelEdit && (
          <button type="button" onClick={onCancelEdit} disabled={submitting}>
            Cancelar edición
          </button>
        )}
      </div>
    </form>
  )
}
