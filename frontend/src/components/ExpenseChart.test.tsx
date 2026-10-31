import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { ExpenseChartMonth } from '../types/charts'
import { toChartData } from '../utils/chart'
import { ExpenseChart } from './ExpenseChart'

const months: ExpenseChartMonth[] = [
  {
    mes: 1,
    gastos_por_tipo: {
      NECESARIO: '100.00',
      NO_NECESARIO: '50.00',
      INVERSION: '20.00',
    },
  },
  {
    mes: 2,
    gastos_por_tipo: {
      NECESARIO: '0.00',
      NO_NECESARIO: '0.00',
      INVERSION: '0.00',
    },
  },
]

describe('ExpenseChart', () => {
  it('converts contract strings to chart numbers', () => {
    expect(toChartData(months)).toEqual([
      { mes: 1, NECESARIO: 100, NO_NECESARIO: 50, INVERSION: 20 },
      { mes: 2, NECESARIO: 0, NO_NECESARIO: 0, INVERSION: 0 },
    ])
  })

  it('renders the legend and the stacked bar mode', () => {
    const { container } = render(<ExpenseChart months={months} mode="bars" />)

    expect(container.querySelector('[data-mode="bars"]')).not.toBeNull()
    expect(screen.getByText('Necesario')).toBeInTheDocument()
    expect(screen.getByText('No necesario')).toBeInTheDocument()
    expect(screen.getByText('Inversión')).toBeInTheDocument()
  })

  it('renders the line mode', () => {
    const { container } = render(<ExpenseChart months={months} mode="lines" />)

    expect(container.querySelector('[data-mode="lines"]')).not.toBeNull()
    expect(
      screen.getByRole('img', { name: /líneas/i }),
    ).toBeInTheDocument()
  })
})
