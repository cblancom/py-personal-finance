import type { Expense, ExpensePayload } from '../types/expense'
import { request } from './client'

export function listExpenses(signal?: AbortSignal): Promise<Expense[]> {
  return request<Expense[]>('/api/gastos', { signal })
}

export function createExpense(payload: ExpensePayload): Promise<Expense> {
  return request<Expense>('/api/gastos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function updateExpense(
  id: number,
  payload: ExpensePayload,
): Promise<Expense> {
  return request<Expense>(`/api/gastos/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function deleteExpense(id: number): Promise<void> {
  return request<void>(`/api/gastos/${id}`, { method: 'DELETE' })
}
