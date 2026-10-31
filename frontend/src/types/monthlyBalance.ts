import type { ExpenseType } from './expense'

export interface BalanceRubro {
  porcentaje: string
  asignado: string
  gastado: string
  restante: string
}

export type BalanceRubros = Record<ExpenseType, BalanceRubro>

export interface BalanceMovement {
  id: number
  fecha: string
  descripcion: string
  valor: string
}

export interface BalanceMovements {
  INGRESOS: BalanceMovement[]
  NECESARIO: BalanceMovement[]
  NO_NECESARIO: BalanceMovement[]
  INVERSION: BalanceMovement[]
}

interface BalanceBase {
  anio: number
  ingresos: string
  sin_asignar: string
  rubros: BalanceRubros
}

export interface MonthlyBalance extends BalanceBase {
  mes: number
  movimientos: BalanceMovements
}

export interface AnnualBalance extends BalanceBase {
  mes: null
}

export interface BalancePeriods {
  anio_actual: number
  anios: number[]
}

export type AllocationPercentages = Record<ExpenseType, string>

export interface MonthlyAllocationPayload {
  porcentajes: AllocationPercentages
}
