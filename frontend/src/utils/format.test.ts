import { describe, expect, it } from 'vitest'
import { expenseTypeLabel, formatDate, formatMoney } from './format'

describe('formatMoney', () => {
  it('formats amounts with es-CO separators and two decimals', () => {
    expect(formatMoney('1500.5')).toBe('1.500,50')
    expect(formatMoney('9999999999.99')).toBe('9.999.999.999,99')
  })

  it('formats zero and negative amounts', () => {
    expect(formatMoney('0.00')).toBe('0,00')
    expect(formatMoney('-150.25')).toBe('-150,25')
  })

  it('returns non-numeric input unchanged', () => {
    expect(formatMoney('')).toBe('')
    expect(formatMoney('abc')).toBe('abc')
  })
})

describe('formatDate', () => {
  it('formats an ISO date without shifting the day', () => {
    expect(formatDate('2026-10-21')).toBe('21/10/2026')
  })

  it('returns invalid input unchanged', () => {
    expect(formatDate('invalid')).toBe('invalid')
  })
})

describe('expenseTypeLabel', () => {
  it('maps API values to Spanish labels', () => {
    expect(expenseTypeLabel('NECESARIO')).toBe('Necesario')
    expect(expenseTypeLabel('NO_NECESARIO')).toBe('No necesario')
    expect(expenseTypeLabel('INVERSION')).toBe('Inversión')
  })
})
