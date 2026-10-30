import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  createIncome,
  deleteIncome,
  updateIncome,
} from '../api/incomes'
import type { Income } from '../types/income'
import { IncomeSection } from './IncomeSection'

vi.mock('../api/incomes', () => ({
  createIncome: vi.fn(),
  updateIncome: vi.fn(),
  deleteIncome: vi.fn(),
}))

const createIncomeMock = vi.mocked(createIncome)
const updateIncomeMock = vi.mocked(updateIncome)
const deleteIncomeMock = vi.mocked(deleteIncome)

const income: Income = {
  id: 1,
  fecha: '2026-10-21',
  descripcion: 'Salario',
  categoria: null,
  valor: '1000.00',
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('IncomeSection', () => {
  it('creates an income and refreshes data', async () => {
    createIncomeMock.mockResolvedValue({
      id: 2,
      fecha: '2026-10-21',
      descripcion: 'Salario',
      categoria: null,
      valor: '1500.50',
    })
    const onChanged = vi.fn().mockResolvedValue(undefined)

    render(<IncomeSection incomes={[]} onChanged={onChanged} />)

    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: 'Salario' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '1500.50' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar ingreso' }))

    await waitFor(() => expect(createIncomeMock).toHaveBeenCalled())
    expect(createIncomeMock).toHaveBeenCalledWith(
      expect.objectContaining({
        descripcion: 'Salario',
        valor: '1500.50',
      }),
    )
    expect(onChanged).toHaveBeenCalled()
  })

  it('edits an income and refreshes data', async () => {
    updateIncomeMock.mockResolvedValue(income)
    const onChanged = vi.fn().mockResolvedValue(undefined)

    render(<IncomeSection incomes={[income]} onChanged={onChanged} />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Editar ingreso Salario' }),
    )
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '2000.00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))

    await waitFor(() => expect(updateIncomeMock).toHaveBeenCalled())
    expect(updateIncomeMock).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        descripcion: 'Salario',
        valor: '2000.00',
      }),
    )
    expect(onChanged).toHaveBeenCalled()
  })

  it('deletes after confirmation and refreshes data', async () => {
    deleteIncomeMock.mockResolvedValue(undefined)
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const onChanged = vi.fn().mockResolvedValue(undefined)

    render(<IncomeSection incomes={[income]} onChanged={onChanged} />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Eliminar ingreso Salario' }),
    )

    await waitFor(() => expect(deleteIncomeMock).toHaveBeenCalledWith(1))
    expect(onChanged).toHaveBeenCalled()
  })

  it('does not delete when confirmation is cancelled', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(<IncomeSection incomes={[income]} onChanged={vi.fn()} />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Eliminar ingreso Salario' }),
    )

    expect(deleteIncomeMock).not.toHaveBeenCalled()
  })

  it('shows an error when saving fails', async () => {
    createIncomeMock.mockRejectedValue(new Error('fail'))

    render(<IncomeSection incomes={[]} onChanged={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: 'Salario' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '1500.50' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar ingreso' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudo guardar el ingreso.',
    )
  })
})
