import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getAnnualBalance,
  getMonthlyBalance,
  getPeriods,
  updateAllocations,
} from '../api/monthlyBalance'
import type {
  AnnualBalance,
  BalancePeriods,
  MonthlyBalance,
} from '../types/monthlyBalance'
import { MonthlyBalanceView } from './MonthlyBalanceView'

vi.mock('../api/monthlyBalance', () => ({
  getPeriods: vi.fn(),
  getAnnualBalance: vi.fn(),
  getMonthlyBalance: vi.fn(),
  updateAllocations: vi.fn(),
}))

const getPeriodsMock = vi.mocked(getPeriods)
const getAnnualBalanceMock = vi.mocked(getAnnualBalance)
const getMonthlyBalanceMock = vi.mocked(getMonthlyBalance)
const updateAllocationsMock = vi.mocked(updateAllocations)

const currentYear = new Date().getFullYear()

const periods: BalancePeriods = {
  anio_actual: currentYear,
  anios: [currentYear, currentYear - 1],
}

const monthly: MonthlyBalance = {
  anio: currentYear,
  mes: 10,
  ingresos: '5000.00',
  sin_asignar: '0.00',
  rubros: {
    NECESARIO: {
      porcentaje: '50.00',
      asignado: '2500.00',
      gastado: '1000.00',
      restante: '1500.00',
    },
    NO_NECESARIO: {
      porcentaje: '30.00',
      asignado: '1500.00',
      gastado: '300.00',
      restante: '1200.00',
    },
    INVERSION: {
      porcentaje: '20.00',
      asignado: '1000.00',
      gastado: '200.00',
      restante: '800.00',
    },
  },
  movimientos: {
    INGRESOS: [
      {
        id: 1,
        fecha: `${currentYear}-10-01`,
        descripcion: 'Salario',
        valor: '5000.00',
      },
    ],
    NECESARIO: [
      {
        id: 2,
        fecha: `${currentYear}-10-02`,
        descripcion: 'Mercado',
        valor: '1000.00',
      },
    ],
    NO_NECESARIO: [
      {
        id: 3,
        fecha: `${currentYear}-10-03`,
        descripcion: 'Cine',
        valor: '300.00',
      },
    ],
    INVERSION: [
      {
        id: 4,
        fecha: `${currentYear}-10-04`,
        descripcion: 'Fondo indexado',
        valor: '200.00',
      },
    ],
  },
}

const updated: MonthlyBalance = {
  ...monthly,
  rubros: {
    NECESARIO: {
      porcentaje: '40.00',
      asignado: '2000.00',
      gastado: '1000.00',
      restante: '1000.00',
    },
    NO_NECESARIO: {
      porcentaje: '40.00',
      asignado: '2000.00',
      gastado: '300.00',
      restante: '1700.00',
    },
    INVERSION: {
      porcentaje: '20.00',
      asignado: '1000.00',
      gastado: '200.00',
      restante: '800.00',
    },
  },
}

const annual: AnnualBalance = {
  anio: currentYear,
  mes: null,
  ingresos: '5000.00',
  sin_asignar: '0.00',
  rubros: {
    NECESARIO: {
      porcentaje: '33.33',
      asignado: '1666.65',
      gastado: '1000.00',
      restante: '666.65',
    },
    NO_NECESARIO: {
      porcentaje: '33.33',
      asignado: '1666.65',
      gastado: '300.00',
      restante: '1366.65',
    },
    INVERSION: {
      porcentaje: '33.34',
      asignado: '1666.70',
      gastado: '200.00',
      restante: '1466.70',
    },
  },
}

beforeEach(() => {
  vi.clearAllMocks()
  getPeriodsMock.mockResolvedValue(periods)
  getAnnualBalanceMock.mockResolvedValue(annual)
  getMonthlyBalanceMock.mockResolvedValue(monthly)
  updateAllocationsMock.mockResolvedValue(updated)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('MonthlyBalanceView', () => {
  it('shows the annual balance by default', async () => {
    render(<MonthlyBalanceView />)

    expect(
      await screen.findByRole('heading', { name: 'Balance mensual' }),
    ).toBeInTheDocument()
    expect(await screen.findByText('Balance anual')).toBeInTheDocument()
    expect(screen.getByLabelText('Año')).toHaveValue(String(currentYear))
    expect(screen.getByLabelText('Mes')).toHaveValue('')
    expect(getAnnualBalanceMock).toHaveBeenCalledWith(
      currentYear,
      expect.any(AbortSignal),
    )
    expect(screen.getAllByText('33.33%')).toHaveLength(2)
  })

  it('loads the four monthly columns', async () => {
    render(<MonthlyBalanceView />)

    await screen.findByText('Balance anual')
    fireEvent.change(screen.getByLabelText('Mes'), {
      target: { value: '10' },
    })

    expect(
      await screen.findByRole('heading', { name: 'Gastos necesarios' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Gastos no necesarios' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Inversión' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Salario')).toBeInTheDocument()
    expect(screen.getByText('Mercado')).toBeInTheDocument()
    expect(screen.getByText('Cine')).toBeInTheDocument()
    expect(screen.getByText('Fondo indexado')).toBeInTheDocument()
    expect(screen.getByText('Sin asignar')).toBeInTheDocument()
    expect(getMonthlyBalanceMock).toHaveBeenCalledWith(
      currentYear,
      10,
      expect.any(AbortSignal),
    )
  })

  it('saves monthly percentages', async () => {
    render(<MonthlyBalanceView />)

    await screen.findByText('Balance anual')
    fireEvent.change(screen.getByLabelText('Mes'), {
      target: { value: '10' },
    })
    await screen.findByRole('heading', { name: 'Gastos necesarios' })

    fireEvent.change(screen.getByRole('textbox', { name: 'Necesario' }), {
      target: { value: '40.00' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: 'No necesario' }), {
      target: { value: '40.00' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: 'Inversión' }), {
      target: { value: '20.00' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Guardar porcentajes' }),
    )

    await waitFor(() =>
      expect(updateAllocationsMock).toHaveBeenCalledWith(
        currentYear,
        10,
        {
          NECESARIO: '40.00',
          NO_NECESARIO: '40.00',
          INVERSION: '20.00',
        },
      ),
    )
    expect(
      await screen.findByText('Porcentajes guardados.'),
    ).toBeInTheDocument()
    expect(screen.getAllByText('40.00%')).toHaveLength(2)
  })

  it('shows an empty state in columns without movements', async () => {
    getMonthlyBalanceMock.mockResolvedValue({
      ...monthly,
      movimientos: {
        INGRESOS: [],
        NECESARIO: [],
        NO_NECESARIO: [],
        INVERSION: [],
      },
    })
    render(<MonthlyBalanceView />)

    await screen.findByText('Balance anual')
    fireEvent.change(screen.getByLabelText('Mes'), {
      target: { value: '10' },
    })

    expect(await screen.findAllByText('Sin movimientos')).toHaveLength(4)
  })

  it('rejects percentages whose sum exceeds 100', async () => {
    render(<MonthlyBalanceView />)

    await screen.findByText('Balance anual')
    fireEvent.change(screen.getByLabelText('Mes'), {
      target: { value: '10' },
    })
    await screen.findByRole('heading', { name: 'Gastos necesarios' })

    fireEvent.change(screen.getByRole('textbox', { name: 'Necesario' }), {
      target: { value: '100.00' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: 'No necesario' }), {
      target: { value: '30.00' },
    })
    fireEvent.change(screen.getByRole('textbox', { name: 'Inversión' }), {
      target: { value: '20.00' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Guardar porcentajes' }),
    )

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent('La suma de los porcentajes no puede superar 100.')
    expect(updateAllocationsMock).not.toHaveBeenCalled()
  })

  it('shows a load error and retries', async () => {
    getAnnualBalanceMock.mockRejectedValueOnce(new Error('down'))
    render(<MonthlyBalanceView />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudo cargar el balance mensual.',
    )
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByText('Balance anual')).toBeInTheDocument()
  })
})
