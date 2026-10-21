export const EXPENSE_TYPES = [
  'NECESARIO',
  'NO_NECESARIO',
  'INVERSION',
] as const

export type ExpenseType = (typeof EXPENSE_TYPES)[number]

export interface Expense {
  id: number
  fecha: string
  descripcion: string
  tipo: ExpenseType
  valor: string
}

export type ExpensePayload = Omit<Expense, 'id'>
