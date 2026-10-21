import type { Income, IncomePayload } from '../types/income'
import { request } from './client'

export function listIncomes(signal?: AbortSignal): Promise<Income[]> {
  return request<Income[]>('/api/ingresos', { signal })
}

export function createIncome(payload: IncomePayload): Promise<Income> {
  return request<Income>('/api/ingresos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateIncome(id: number, payload: IncomePayload): Promise<Income> {
  return request<Income>(`/api/ingresos/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function deleteIncome(id: number): Promise<void> {
  return request<void>(`/api/ingresos/${id}`, { method: 'DELETE' })
}
