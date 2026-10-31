import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { getExpenseChart } from '../api/charts'
import { getPeriods } from '../api/monthlyBalance'
import type { ExpenseChart } from '../types/charts'
import type { BalancePeriods } from '../types/monthlyBalance'
import { ChartSection } from './ChartSection'

vi.mock('../api/charts', () => ({
  getExpenseChart: vi.fn(),
}))

vi.mock('../api/monthlyBalance', () => ({
  getPeriods: vi.fn(),
}))

const getExpenseChartMock = vi.mocked(getExpenseChart)
const getPeriodsMock = vi.mocked(getPeriods)

const currentYear = new Date().getFullYear()

const periods: BalancePeriods = {
  anio_actual: currentYear,
  anios: [currentYear, currentYear - 1],
}

function emptyMonth(month: number) {
  return {
    mes: month,
    gastos_por_tipo: {
      NECESARIO: '0.00',
      NO_NECESARIO: '0.00',
      INVERSION: '0.00',
    },
  }
}

const chart: ExpenseChart = {
  anio: currentYear,
  meses: [
    {
      mes: 1,
      gastos_por_tipo: {
        NECESARIO: '100.00',
        NO_NECESARIO: '50.00',
        INVERSION: '20.00',
      },
    },
    ...Array.from({ length: 11 }, (_, index) => emptyMonth(index + 2)),
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
  getPeriodsMock.mockResolvedValue(periods)
  getExpenseChartMock.mockResolvedValue(chart)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ChartSection', () => {
  it('loads the chart and switches between bars and lines without refetching', async () => {
    render(<ChartSection />)

    expect(
      await screen.findByRole('heading', { name: 'Gastos por mes' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('img', { name: /barras apiladas/i }),
    ).toBeInTheDocument()
    expect(getExpenseChartMock).toHaveBeenCalledWith(
      currentYear,
      expect.any(AbortSignal),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Líneas' }))

    expect(screen.getByRole('img', { name: /líneas/i })).toBeInTheDocument()
    expect(getExpenseChartMock).toHaveBeenCalledTimes(1)
  })

  it('changes the year and reloads the series', async () => {
    render(<ChartSection />)

    await screen.findByRole('heading', { name: 'Gastos por mes' })
    fireEvent.change(screen.getByLabelText('Año'), {
      target: { value: String(currentYear - 1) },
    })

    await waitFor(() =>
      expect(getExpenseChartMock).toHaveBeenCalledWith(
        currentYear - 1,
        expect.any(AbortSignal),
      ),
    )
  })

  it('reloads when the refresh key changes', async () => {
    const { rerender } = render(<ChartSection refreshKey={0} />)

    await screen.findByRole('heading', { name: 'Gastos por mes' })
    expect(getExpenseChartMock).toHaveBeenCalledTimes(1)

    rerender(<ChartSection refreshKey={1} />)

    await waitFor(() => expect(getExpenseChartMock).toHaveBeenCalledTimes(2))
  })

  it('shows the accessible data table', async () => {
    render(<ChartSection />)

    await screen.findByRole('heading', { name: 'Gastos por mes' })
    fireEvent.click(screen.getByRole('button', { name: 'Ver datos' }))

    expect(
      screen.getByRole('table', { name: 'Datos mensuales de gastos' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Enero')).toBeInTheDocument()
    expect(screen.getByText('$ 100,00')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Ocultar datos' }),
    ).toBeInTheDocument()
  })

  it('shows an empty state when the year has no expenses', async () => {
    getExpenseChartMock.mockResolvedValue({
      anio: currentYear,
      meses: Array.from({ length: 12 }, (_, index) => emptyMonth(index + 1)),
    })
    render(<ChartSection />)

    expect(
      await screen.findByText('No hay gastos registrados para este año.'),
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('img', { name: /gastos mensuales/i }),
    ).not.toBeInTheDocument()
  })

  it('shows an error and retries', async () => {
    getExpenseChartMock.mockRejectedValueOnce(new Error('down'))
    render(<ChartSection />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudo cargar la gráfica de gastos.',
    )
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(
      await screen.findByRole('img', { name: /barras apiladas/i }),
    ).toBeInTheDocument()
  })
})
