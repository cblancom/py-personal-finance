import type { Expense } from '../types/expense'
import { expenseTypeLabel, formatDate, formatMoney } from '../utils/format'

interface ExpenseListProps {
  expenses: Expense[]
  onEdit: (expense: Expense) => void
  onDelete: (expense: Expense) => void
}

export function ExpenseList({
  expenses,
  onEdit,
  onDelete,
}: ExpenseListProps) {
  return (
    <div className="movement-list">
      <h3>Gastos registrados</h3>

      {expenses.length === 0 ? (
        <p className="empty-state">No hay gastos registrados.</p>
      ) : (
        <table className="movement-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Descripción</th>
              <th>Tipo</th>
              <th>Valor</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((expense) => (
              <tr key={expense.id}>
                <td>{formatDate(expense.fecha)}</td>
                <td>{expense.descripcion}</td>
                <td>{expenseTypeLabel(expense.tipo)}</td>
                <td>{formatMoney(expense.valor)}</td>
                <td className="movement-actions">
                  <button
                    type="button"
                    onClick={() => onEdit(expense)}
                    aria-label={`Editar gasto ${expense.descripcion}`}
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(expense)}
                    aria-label={`Eliminar gasto ${expense.descripcion}`}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
