import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  createExpense,
  deleteExpense,
  updateExpense,
} from '../api/expenses'
import type { Expense } from '../types/expense'
import { ExpenseSection } from './ExpenseSection'

vi.mock('../api/expenses', () => ({
  createExpense: vi.fn(),
  updateExpense: vi.fn(),
  deleteExpense: vi.fn(),
}))

const createExpenseMock = vi.mocked(createExpense)
const updateExpenseMock = vi.mocked(updateExpense)
const deleteExpenseMock = vi.mocked(deleteExpense)

const expense: Expense = {
  id: 1,
  fecha: '2026-10-21',
  descripcion: 'Mercado',
  tipo: 'NECESARIO',
  valor: '120.50',
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ExpenseSection', () => {
  it('creates an expense and refreshes data', async () => {
    createExpenseMock.mockResolvedValue({
      id: 2,
      fecha: '2026-10-21',
      descripcion: 'Mercado',
      tipo: 'NECESARIO',
      valor: '120.50',
    })
    const onChanged = vi.fn().mockResolvedValue(undefined)

    render(<ExpenseSection expenses={[]} onChanged={onChanged} />)

    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: 'Mercado' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '120.50' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar gasto' }))

    await waitFor(() => expect(createExpenseMock).toHaveBeenCalled())
    expect(createExpenseMock).toHaveBeenCalledWith(
      expect.objectContaining({
        descripcion: 'Mercado',
        tipo: 'NECESARIO',
        valor: '120.50',
      }),
    )
    expect(onChanged).toHaveBeenCalled()
  })

  it('edits an expense and refreshes data', async () => {
    updateExpenseMock.mockResolvedValue(expense)
    const onChanged = vi.fn().mockResolvedValue(undefined)

    render(<ExpenseSection expenses={[expense]} onChanged={onChanged} />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Editar gasto Mercado' }),
    )
    fireEvent.change(screen.getByLabelText('Tipo'), {
      target: { value: 'INVERSION' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '300.00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => expect(updateExpenseMock).toHaveBeenCalled())
    expect(updateExpenseMock).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        descripcion: 'Mercado',
        tipo: 'INVERSION',
        valor: '300.00',
      }),
    )
    expect(onChanged).toHaveBeenCalled()
  })

  it('deletes after confirmation and refreshes data', async () => {
    deleteExpenseMock.mockResolvedValue(undefined)
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const onChanged = vi.fn().mockResolvedValue(undefined)

    render(<ExpenseSection expenses={[expense]} onChanged={onChanged} />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Eliminar gasto Mercado' }),
    )

    await waitFor(() => expect(deleteExpenseMock).toHaveBeenCalledWith(1))
    expect(onChanged).toHaveBeenCalled()
  })

  it('does not delete when confirmation is cancelled', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(<ExpenseSection expenses={[expense]} onChanged={vi.fn()} />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Eliminar gasto Mercado' }),
    )

    expect(deleteExpenseMock).not.toHaveBeenCalled()
  })

  it('shows an error when saving fails', async () => {
    createExpenseMock.mockRejectedValue(new Error('fail'))

    render(<ExpenseSection expenses={[]} onChanged={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: 'Mercado' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '120.50' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar gasto' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudo guardar el gasto.',
    )
  })
})
