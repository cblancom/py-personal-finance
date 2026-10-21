import { EXPENSE_TYPES } from '../types/expense'
import type { Summary } from '../types/summary'
import { expenseTypeLabel, formatMoney } from '../utils/format'

interface SummaryPanelProps {
  summary: Summary
}

export function SummaryPanel({ summary }: SummaryPanelProps) {
  const isNegativeBalance = summary.balance.startsWith('-')

  return (
    <section className="summary" aria-labelledby="summary-title">
      <h2 id="summary-title">Resumen</h2>

      <div className="summary__totals">
        <article className="summary-card">
          <h3>Total ingresos</h3>
          <p>{formatMoney(summary.total_ingresos)}</p>
        </article>
        <article className="summary-card">
          <h3>Total gastos</h3>
          <p>{formatMoney(summary.total_gastos)}</p>
        </article>
        <article
          className={`summary-card${isNegativeBalance ? ' summary-card--negative' : ''}`}
        >
          <h3>Balance</h3>
          <p>{formatMoney(summary.balance)}</p>
        </article>
      </div>

      <div className="summary__breakdown">
        <h3>Gastos por tipo</h3>
        <ul>
          {EXPENSE_TYPES.map((type) => (
            <li key={type}>
              <span>{expenseTypeLabel(type)}</span>
              <strong>{formatMoney(summary.gastos_por_tipo[type])}</strong>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
