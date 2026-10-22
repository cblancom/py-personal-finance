import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Expense } from '../types/expense'
import { ExpenseList } from './ExpenseList'

const expense: Expense = {
  id: 1,
  fecha: '2026-10-21',
  descripcion: 'Mercado',
  tipo: 'NECESARIO',
  valor: '120.50',
}

describe('ExpenseList', () => {
  it('renders expenses and actions', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()
    render(
      <ExpenseList
        expenses={[expense]}
        onEdit={onEdit}
        onDelete={onDelete}
      />,
    )

    expect(screen.getByText('21/10/2026')).toBeInTheDocument()
    expect(screen.getByText('Mercado')).toBeInTheDocument()
    expect(screen.getByText('Necesario')).toBeInTheDocument()
    expect(screen.getByText('$ 120,50')).toBeInTheDocument()

    fireEvent.click(
      screen.getByRole('button', { name: 'Editar gasto Mercado' }),
    )
    fireEvent.click(
      screen.getByRole('button', { name: 'Eliminar gasto Mercado' }),
    )

    expect(onEdit).toHaveBeenCalledWith(expense)
    expect(onDelete).toHaveBeenCalledWith(expense)
  })

  it('shows an empty state', () => {
    render(<ExpenseList expenses={[]} onEdit={vi.fn()} onDelete={vi.fn()} />)

    expect(
      screen.getByText('No hay gastos registrados.'),
    ).toBeInTheDocument()
  })
})
