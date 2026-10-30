import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Income } from '../types/income'
import { IncomeList } from './IncomeList'

const income: Income = {
  id: 1,
  fecha: '2026-10-21',
  descripcion: 'Salario',
  categoria: 'Nómina',
  valor: '1500.50',
}

describe('IncomeList', () => {
  it('renders incomes and actions', () => {
    const onEdit = vi.fn()
    const onDelete = vi.fn()
    render(
      <IncomeList incomes={[income]} onEdit={onEdit} onDelete={onDelete} />,
    )

    expect(screen.getByText('21/10/2026')).toBeInTheDocument()
    expect(screen.getByText('Salario')).toBeInTheDocument()
    expect(screen.getByText('Nómina')).toBeInTheDocument()
    expect(screen.getByText('$ 1.500,50')).toBeInTheDocument()

    fireEvent.click(
      screen.getByRole('button', { name: 'Editar ingreso Salario' }),
    )
    fireEvent.click(
      screen.getByRole('button', { name: 'Eliminar ingreso Salario' }),
    )

    expect(onEdit).toHaveBeenCalledWith(income)
    expect(onDelete).toHaveBeenCalledWith(income)
  })

  it('shows an empty state', () => {
    render(<IncomeList incomes={[]} onEdit={vi.fn()} onDelete={vi.fn()} />)

    expect(
      screen.getByText('No hay ingresos registrados.'),
    ).toBeInTheDocument()
  })
})
