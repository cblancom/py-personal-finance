import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { listExpenses } from './api/expenses'
import { createIncome, listIncomes } from './api/incomes'
import { getSummary } from './api/summary'
import type { Expense } from './types/expense'
import type { Income } from './types/income'
import type { Summary } from './types/summary'
import App from './App'

vi.mock('./api/incomes', () => ({
  listIncomes: vi.fn(),
  createIncome: vi.fn(),
  updateIncome: vi.fn(),
  deleteIncome: vi.fn(),
}))

vi.mock('./api/expenses', () => ({
  listExpenses: vi.fn(),
  createExpense: vi.fn(),
  updateExpense: vi.fn(),
  deleteExpense: vi.fn(),
}))

vi.mock('./api/summary', () => ({
  getSummary: vi.fn(),
}))

const getSummaryMock = vi.mocked(getSummary)
const listIncomesMock = vi.mocked(listIncomes)
const listExpensesMock = vi.mocked(listExpenses)
const createIncomeMock = vi.mocked(createIncome)

const summary: Summary = {
  total_ingresos: '1000.00',
  total_gastos: '200.00',
  balance: '800.00',
  gastos_por_tipo: {
    NECESARIO: '200.00',
    NO_NECESARIO: '0.00',
    INVERSION: '0.00',
  },
}

const income: Income = {
  id: 1,
  fecha: '2026-10-21',
  descripcion: 'Salario',
  categoria: null,
  valor: '750.00',
}

const expense: Expense = {
  id: 1,
  fecha: '2026-10-20',
  descripcion: 'Mercado',
  tipo: 'NECESARIO',
  valor: '200.00',
}

beforeEach(() => {
  vi.clearAllMocks()
  getSummaryMock.mockResolvedValue(summary)
  listIncomesMock.mockResolvedValue([income])
  listExpensesMock.mockResolvedValue([expense])
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('App', () => {
  it('loads the summary, incomes and expenses', async () => {
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Resumen' }),
    ).toBeInTheDocument()
    expect(screen.getByText('$ 1.000,00')).toBeInTheDocument()
    expect(screen.getByText('$ 800,00')).toBeInTheDocument()
    expect(screen.getByText('$ 750,00')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Ingresos' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(
      screen.getByRole('heading', { name: 'Nuevo ingreso' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Salario')).toBeInTheDocument()
    expect(
      screen.getByRole('tablist', { name: 'Movimientos' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('tabpanel')).toHaveAttribute(
      'aria-labelledby',
      'incomes-tab',
    )
    expect(
      screen.getByText('Importes en pesos colombianos (COP).'),
    ).toBeInTheDocument()
    expect(getSummaryMock).toHaveBeenCalled()
    expect(listIncomesMock).toHaveBeenCalled()
    expect(listExpensesMock).toHaveBeenCalled()
  })

  it('shows loading while initial requests are pending', () => {
    getSummaryMock.mockReturnValue(new Promise<Summary>(() => {}))
    listIncomesMock.mockReturnValue(new Promise<Income[]>(() => {}))
    listExpensesMock.mockReturnValue(new Promise<Expense[]>(() => {}))

    render(<App />)

    expect(screen.getByRole('status')).toHaveTextContent('Cargando datos...')
    expect(
      screen.queryByRole('heading', { name: 'Resumen' }),
    ).not.toBeInTheDocument()
  })

  it('switches between income and expense tabs', async () => {
    render(<App />)

    await screen.findByRole('heading', { name: 'Nuevo ingreso' })
    fireEvent.click(screen.getByRole('tab', { name: 'Gastos' }))

    expect(screen.getByRole('tab', { name: 'Gastos' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(
      screen.getByRole('heading', { name: 'Nuevo gasto' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Mercado')).toBeInTheDocument()
    expect(screen.getByRole('tabpanel')).toHaveAttribute(
      'aria-labelledby',
      'expenses-tab',
    )
    expect(
      screen.queryByRole('heading', { name: 'Nuevo ingreso' }),
    ).not.toBeInTheDocument()
  })

  it('shows a load error and retries', async () => {
    getSummaryMock.mockRejectedValueOnce(new Error('down'))

    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudieron cargar los datos.',
    )
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(
      await screen.findByRole('heading', { name: 'Resumen' }),
    ).toBeInTheDocument()
  })

  it('reloads summary and lists after creating an income', async () => {
    const newIncome: Income = {
      id: 2,
      fecha: '2026-10-22',
      descripcion: 'Consultoría',
      categoria: null,
      valor: '1500.50',
    }
    const updatedSummary: Summary = {
      total_ingresos: '2500.50',
      total_gastos: '200.00',
      balance: '2300.50',
      gastos_por_tipo: {
        NECESARIO: '200.00',
        NO_NECESARIO: '0.00',
        INVERSION: '0.00',
      },
    }

    getSummaryMock
      .mockResolvedValueOnce(summary)
      .mockResolvedValueOnce(updatedSummary)
    listIncomesMock
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([newIncome])
    listExpensesMock.mockResolvedValue([])
    createIncomeMock.mockResolvedValue(newIncome)

    render(<App />)

    await screen.findByRole('heading', { name: 'Nuevo ingreso' })
    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: newIncome.descripcion },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: newIncome.valor },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar ingreso' }))

    await waitFor(() => expect(createIncomeMock).toHaveBeenCalled())
    expect(await screen.findByText('Consultoría')).toBeInTheDocument()
    expect(await screen.findByText('$ 2.500,50')).toBeInTheDocument()
  })
})
