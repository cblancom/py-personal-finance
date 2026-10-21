import { useState } from 'react'
import { createExpense, deleteExpense, updateExpense } from '../api/expenses'
import type { Expense, ExpensePayload } from '../types/expense'
import { ExpenseForm } from './ExpenseForm'
import { ExpenseList } from './ExpenseList'

interface ExpenseSectionProps {
  expenses: Expense[]
  onChanged: () => void | Promise<void>
}

export function ExpenseSection({ expenses, onChanged }: ExpenseSectionProps) {
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formVersion, setFormVersion] = useState(0)

  const formKey = editingExpense
    ? `edit-${editingExpense.id}`
    : `new-${formVersion}`

  async function handleSubmit(payload: ExpensePayload) {
    setSubmitting(true)
    setError(null)

    try {
      if (editingExpense) {
        await updateExpense(editingExpense.id, payload)
      } else {
        await createExpense(payload)
      }

      setEditingExpense(null)
      setFormVersion((version) => version + 1)
      await onChanged()
    } catch {
      setError(
        'No se pudo guardar el gasto. Revisa los datos e inténtalo de nuevo.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  function handleEdit(expense: Expense) {
    setError(null)
    setEditingExpense(expense)
  }

  function handleCancelEdit() {
    setError(null)
    setEditingExpense(null)
  }

  async function handleDelete(expense: Expense) {
    if (!window.confirm(`¿Eliminar el gasto "${expense.descripcion}"?`)) {
      return
    }

    setError(null)

    try {
      await deleteExpense(expense.id)
      if (editingExpense?.id === expense.id) {
        setEditingExpense(null)
      }
      await onChanged()
    } catch {
      setError('No se pudo eliminar el gasto. Inténtalo de nuevo.')
    }
  }

  return (
    <section
      className="movement-section"
      aria-labelledby="expense-section-title"
    >
      <h2 id="expense-section-title">Gastos</h2>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      <ExpenseForm
        key={formKey}
        initial={editingExpense}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancelEdit={handleCancelEdit}
      />

      <ExpenseList
        expenses={expenses}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />
    </section>
  )
}
