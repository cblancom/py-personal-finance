import type { ExpenseChart } from '../types/charts'
import { request } from './client'

export function getExpenseChart(
  anio: number,
  signal?: AbortSignal,
): Promise<ExpenseChart> {
  return request<ExpenseChart>(
    `/api/graficos/gastos-mensuales?anio=${anio}`,
    { signal },
  )
}
