import type { ExpenseType } from './expense'

export interface ExpenseChartMonth {
  mes: number
  gastos_por_tipo: Record<ExpenseType, string>
}

export interface ExpenseChart {
  anio: number
  meses: ExpenseChartMonth[]
}

export type ChartMode = 'bars' | 'lines'
