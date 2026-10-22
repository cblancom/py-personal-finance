import type { Income } from '../types/income'
import { formatDate, formatMoney } from '../utils/format'

interface IncomeListProps {
  incomes: Income[]
  onEdit: (income: Income) => void
  onDelete: (income: Income) => void
}

export function IncomeList({ incomes, onEdit, onDelete }: IncomeListProps) {
  return (
    <div className="movement-list">
      <h3>Ingresos registrados</h3>

      {incomes.length === 0 ? (
        <p className="empty-state">No hay ingresos registrados.</p>
      ) : (
        <table className="movement-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Descripción</th>
              <th className="amount">Valor</th>
              <th className="actions">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {incomes.map((income) => (
              <tr key={income.id}>
                <td>{formatDate(income.fecha)}</td>
                <td>{income.descripcion}</td>
                <td className="amount">{formatMoney(income.valor)}</td>
                <td className="movement-actions">
                  <button
                    type="button"
                    className="button button--link"
                    onClick={() => onEdit(income)}
                    aria-label={`Editar ingreso ${income.descripcion}`}
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    className="button button--link"
                    onClick={() => onDelete(income)}
                    aria-label={`Eliminar ingreso ${income.descripcion}`}
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
