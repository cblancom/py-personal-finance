import type {
  AllocationPercentages,
  AnnualBalance,
  BalancePeriods,
  MonthlyAllocationPayload,
  MonthlyBalance,
} from '../types/monthlyBalance'
import { request } from './client'

export function getPeriods(signal?: AbortSignal): Promise<BalancePeriods> {
  return request<BalancePeriods>('/api/balance-mensual/periodos', { signal })
}

export function getMonthlyBalance(
  anio: number,
  mes: number,
  signal?: AbortSignal,
): Promise<MonthlyBalance> {
  return request<MonthlyBalance>(
    `/api/balance-mensual?anio=${anio}&mes=${mes}`,
    { signal },
  )
}

export function getAnnualBalance(
  anio: number,
  signal?: AbortSignal,
): Promise<AnnualBalance> {
  return request<AnnualBalance>(`/api/balance-mensual?anio=${anio}`, {
    signal,
  })
}

export function updateAllocations(
  anio: number,
  mes: number,
  porcentajes: AllocationPercentages,
): Promise<MonthlyBalance> {
  const payload: MonthlyAllocationPayload = { porcentajes }

  return request<MonthlyBalance>(
    `/api/balance-mensual/asignaciones/${anio}/${mes}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  )
}
