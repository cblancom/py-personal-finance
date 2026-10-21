export interface Income {
  id: number
  fecha: string
  descripcion: string
  valor: string
}

export type IncomePayload = Omit<Income, 'id'>
