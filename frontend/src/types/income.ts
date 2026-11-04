import type { ExpenseType } from './expense'

export interface Income {
  id: number
  fecha: string
  descripcion: string
  tipo: ExpenseType | null
  valor: string
}

export type IncomePayload = Omit<Income, 'id'>
