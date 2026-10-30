export interface Income {
  id: number
  fecha: string
  descripcion: string
  categoria: string | null
  valor: string
}

export type IncomePayload = Omit<Income, 'id'>
