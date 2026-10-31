import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ChartMode, ExpenseChartMonth } from '../types/charts'
import type { ExpenseType } from '../types/expense'
import { toChartData } from '../utils/chart'
import {
  expenseTypeLabel,
  formatCompactMoney,
  formatMoney,
} from '../utils/format'

const MONTH_LABELS = [
  'Ene',
  'Feb',
  'Mar',
  'Abr',
  'May',
  'Jun',
  'Jul',
  'Ago',
  'Sep',
  'Oct',
  'Nov',
  'Dic',
]

const SERIES: ExpenseType[] = ['NECESARIO', 'NO_NECESARIO', 'INVERSION']

const COLORS: Record<ExpenseType, string> = {
  NECESARIO: '#a33d3d',
  NO_NECESARIO: '#c58a2b',
  INVERSION: '#0e6b5c',
}


interface ExpenseChartProps {
  months: ExpenseChartMonth[]
  mode: ChartMode
}

function monthLabel(value: number): string {
  return MONTH_LABELS[value - 1] ?? String(value)
}

function tooltipFormatter(value: unknown): string {
  return formatMoney(String(value))
}

function tooltipLabel(value: unknown): string {
  return monthLabel(Number(value))
}

export function ExpenseChart({ months, mode }: ExpenseChartProps) {
  const data = toChartData(months)

  return (
    <div
      className="expense-chart"
      data-mode={mode}
      role="img"
      aria-label={`Gráfica de gastos mensuales en ${
        mode === 'bars' ? 'barras apiladas' : 'líneas'
      }`}
    >
      <div className="expense-chart__legend" aria-label="Categorías">
        {SERIES.map((type) => (
          <span key={type}>
            <i style={{ backgroundColor: COLORS[type] }} aria-hidden="true" />
            {expenseTypeLabel(type)}
          </span>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={320}>
        {mode === 'bars' ? (
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#b9c7cc" vertical={false} />
            <XAxis dataKey="mes" tickFormatter={monthLabel} tickLine={false} />
            <YAxis tickFormatter={formatCompactMoney} tickLine={false} axisLine={false} />
            <Tooltip
              formatter={tooltipFormatter}
              labelFormatter={tooltipLabel}
              cursor={{ fill: 'rgba(23, 37, 43, 0.06)' }}
            />
            {SERIES.map((type) => (
              <Bar
                key={type}
                dataKey={type}
                name={expenseTypeLabel(type)}
                stackId="gastos"
                fill={COLORS[type]}
              />
            ))}
          </BarChart>
        ) : (
          <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#b9c7cc" vertical={false} />
            <XAxis dataKey="mes" tickFormatter={monthLabel} tickLine={false} />
            <YAxis tickFormatter={formatCompactMoney} tickLine={false} axisLine={false} />
            <Tooltip formatter={tooltipFormatter} labelFormatter={tooltipLabel} />
            {SERIES.map((type) => (
              <Line
                key={type}
                type="monotone"
                dataKey={type}
                name={expenseTypeLabel(type)}
                stroke={COLORS[type]}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}
