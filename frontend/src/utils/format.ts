import type { ExpenseType } from '../types/expense'

const moneyFormatter = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const compactMoneyFormatter = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  notation: 'compact',
  maximumFractionDigits: 1,
})

const expenseTypeLabels: Record<ExpenseType, string> = {
  NECESARIO: 'Necesario',
  NO_NECESARIO: 'No necesario',
  INVERSION: 'Inversión',
}

export function formatMoney(value: string): string {
  if (value.trim() === '') {
    return value
  }

  const amount = Number(value)
  if (!Number.isFinite(amount)) {
    return value
  }

  return moneyFormatter.format(amount)
}

export function formatCompactMoney(value: number): string {
  if (!Number.isFinite(value)) {
    return ''
  }

  return compactMoneyFormatter.format(value)
}

export function formatDate(value: string): string {
  const [year, month, day] = value.split('-')
  if (!year || !month || !day) {
    return value
  }

  return `${day}/${month}/${year}`
}

export function todayIsoDate(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

export function expenseTypeLabel(type: ExpenseType): string {
  return expenseTypeLabels[type]
}
