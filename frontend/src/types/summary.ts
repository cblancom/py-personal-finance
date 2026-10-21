import type { ExpenseType } from './expense'

export interface Summary {
  total_ingresos: string
  total_gastos: string
  balance: string
  gastos_por_tipo: Record<ExpenseType, string>
}
