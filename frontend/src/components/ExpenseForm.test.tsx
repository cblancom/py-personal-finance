import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Expense } from '../types/expense'
import { ExpenseForm } from './ExpenseForm'

const expense: Expense = {
  id: 1,
  fecha: '2026-10-21',
  descripcion: 'Mercado',
  tipo: 'NO_NECESARIO',
  valor: '120.50',
}

describe('ExpenseForm', () => {
  it('submits a valid expense with the selected type', () => {
    const onSubmit = vi.fn()
    render(<ExpenseForm submitting={false} onSubmit={onSubmit} />)

    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: '  Curso  ' },
    })
    fireEvent.change(screen.getByLabelText('Tipo'), {
      target: { value: 'INVERSION' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '300.75' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar gasto' }))

    expect(onSubmit).toHaveBeenCalledWith({
      fecha: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
      descripcion: 'Curso',
      tipo: 'INVERSION',
      valor: '300.75',
    })
  })

  it('shows validation errors and does not submit invalid data', () => {
    const onSubmit = vi.fn()
    render(<ExpenseForm submitting={false} onSubmit={onSubmit} />)

    fireEvent.click(screen.getByRole('button', { name: 'Guardar gasto' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      'La descripción es obligatoria.',
    )
    expect(onSubmit).not.toHaveBeenCalled()

    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: 'Mercado' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '-1' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar gasto' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      'El valor debe ser mayor que 0.',
    )
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('fills the form in edit mode and can cancel', () => {
    const onSubmit = vi.fn()
    const onCancelEdit = vi.fn()
    render(
      <ExpenseForm
        initial={expense}
        submitting={false}
        onSubmit={onSubmit}
        onCancelEdit={onCancelEdit}
      />,
    )

    expect(screen.getByLabelText('Fecha')).toHaveValue(expense.fecha)
    expect(screen.getByLabelText('Descripción')).toHaveValue(
      expense.descripcion,
    )
    expect(screen.getByLabelText('Tipo')).toHaveValue(expense.tipo)
    expect(screen.getByLabelText('Valor')).toHaveValue(Number(expense.valor))
    expect(
      screen.getByRole('button', { name: 'Guardar cambios' }),
    ).toBeInTheDocument()

    fireEvent.click(
      screen.getByRole('button', { name: 'Cancelar edición' }),
    )

    expect(onCancelEdit).toHaveBeenCalled()
  })

  it('disables the submit button while submitting', () => {
    render(<ExpenseForm submitting onSubmit={vi.fn()} />)

    expect(
      screen.getByRole('button', { name: 'Guardando...' }),
    ).toBeDisabled()
  })
})
