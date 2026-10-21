import { useState } from 'react'
import { createIncome, deleteIncome, updateIncome } from '../api/incomes'
import type { Income, IncomePayload } from '../types/income'
import { IncomeForm } from './IncomeForm'
import { IncomeList } from './IncomeList'

interface IncomeSectionProps {
  incomes: Income[]
  onChanged: () => void | Promise<void>
}

export function IncomeSection({ incomes, onChanged }: IncomeSectionProps) {
  const [editingIncome, setEditingIncome] = useState<Income | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formVersion, setFormVersion] = useState(0)

  const formKey = editingIncome
    ? `edit-${editingIncome.id}`
    : `new-${formVersion}`

  async function handleSubmit(payload: IncomePayload) {
    setSubmitting(true)
    setError(null)

    try {
      if (editingIncome) {
        await updateIncome(editingIncome.id, payload)
      } else {
        await createIncome(payload)
      }

      setEditingIncome(null)
      setFormVersion((version) => version + 1)
      await onChanged()
    } catch {
      setError(
        'No se pudo guardar el ingreso. Revisa los datos e inténtalo de nuevo.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  function handleEdit(income: Income) {
    setError(null)
    setEditingIncome(income)
  }

  function handleCancelEdit() {
    setError(null)
    setEditingIncome(null)
  }

  async function handleDelete(income: Income) {
    if (!window.confirm(`¿Eliminar el ingreso "${income.descripcion}"?`)) {
      return
    }

    setError(null)

    try {
      await deleteIncome(income.id)
      if (editingIncome?.id === income.id) {
        setEditingIncome(null)
      }
      await onChanged()
    } catch {
      setError('No se pudo eliminar el ingreso. Inténtalo de nuevo.')
    }
  }

  return (
    <section className="movement-section" aria-labelledby="income-section-title">
      <h2 id="income-section-title">Ingresos</h2>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <IncomeForm
        key={formKey}
        initial={editingIncome}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancelEdit={handleCancelEdit}
      />

      <IncomeList
        incomes={incomes}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
    </section>
  )
}
