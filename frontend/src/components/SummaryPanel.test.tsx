import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Summary } from '../types/summary'
import { SummaryPanel } from './SummaryPanel'

const summary: Summary = {
  total_ingresos: '1500.50',
  total_gastos: '500.00',
  balance: '1000.50',
  gastos_por_tipo: {
    NECESARIO: '300.00',
    NO_NECESARIO: '0.00',
    INVERSION: '200.00',
  },
}

describe('SummaryPanel', () => {
  it('renders totals and breakdown', () => {
    render(<SummaryPanel summary={summary} />)

    expect(screen.getByRole('heading', { name: 'Resumen' })).toBeInTheDocument()
    expect(screen.getByText('1.500,50')).toBeInTheDocument()
    expect(screen.getByText('500,00')).toBeInTheDocument()
    expect(screen.getByText('1.000,50')).toBeInTheDocument()
    expect(screen.getByText('Necesario')).toBeInTheDocument()
    expect(screen.getByText('No necesario')).toBeInTheDocument()
    expect(screen.getByText('Inversión')).toBeInTheDocument()
    expect(screen.getByText('300,00')).toBeInTheDocument()
    expect(screen.getByText('200,00')).toBeInTheDocument()
  })

  it('marks a negative balance', () => {
    render(<SummaryPanel summary={{ ...summary, balance: '-150.25' }} />)

    const balance = screen.getByText('-150,25')

    expect(balance.closest('article')).toHaveClass('summary-card--negative')
  })

  it('renders zero values for an empty summary', () => {
    render(
      <SummaryPanel
        summary={{
          total_ingresos: '0.00',
          total_gastos: '0.00',
          balance: '0.00',
          gastos_por_tipo: {
            NECESARIO: '0.00',
            NO_NECESARIO: '0.00',
            INVERSION: '0.00',
          },
        }}
      />,
    )

    expect(screen.getAllByText('0,00')).toHaveLength(6)
  })
})
