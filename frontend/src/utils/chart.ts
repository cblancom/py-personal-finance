import type { ExpenseChartMonth } from '../types/charts'

export interface ChartPoint {
  mes: number
  NECESARIO: number
  NO_NECESARIO: number
  INVERSION: number
}

export function toChartData(months: ExpenseChartMonth[]): ChartPoint[] {
  return months.map((month) => ({
    mes: month.mes,
    NECESARIO: Number(month.gastos_por_tipo.NECESARIO),
    NO_NECESARIO: Number(month.gastos_por_tipo.NO_NECESARIO),
    INVERSION: Number(month.gastos_por_tipo.INVERSION),
  }))
}
