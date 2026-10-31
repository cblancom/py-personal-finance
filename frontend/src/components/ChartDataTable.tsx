import type { ExpenseChartMonth } from '../types/charts'
import { formatMoney } from '../utils/format'

const MONTH_NAMES = [
  'Enero',
  'Febrero',
  'Marzo',
  'Abril',
  'Mayo',
  'Junio',
  'Julio',
  'Agosto',
  'Septiembre',
  'Octubre',
  'Noviembre',
  'Diciembre',
]

interface ChartDataTableProps {
  months: ExpenseChartMonth[]
}

export function ChartDataTable({ months }: ChartDataTableProps) {
  return (
    <div className="chart-data-table">
      <table className="movement-table">
        <caption>Datos mensuales de gastos</caption>
        <thead>
          <tr>
            <th scope="col">Mes</th>
            <th scope="col" className="amount">
              Necesario
            </th>
            <th scope="col" className="amount">
              No necesario
            </th>
            <th scope="col" className="amount">
              Inversión
            </th>
          </tr>
        </thead>
        <tbody>
          {months.map((month) => (
            <tr key={month.mes}>
              <th scope="row">{MONTH_NAMES[month.mes - 1] ?? month.mes}</th>
              <td className="amount">
                {formatMoney(month.gastos_por_tipo.NECESARIO)}
              </td>
              <td className="amount">
                {formatMoney(month.gastos_por_tipo.NO_NECESARIO)}
              </td>
              <td className="amount">
                {formatMoney(month.gastos_por_tipo.INVERSION)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
