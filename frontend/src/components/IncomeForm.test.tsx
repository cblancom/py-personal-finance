import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Income } from '../types/income'
import { IncomeForm } from './IncomeForm'

const income: Income = {
  id: 1,
  fecha: '2026-10-21',
  descripcion: 'Salario',
  valor: '1000.00',
}

describe('IncomeForm', () => {
  it('submits a valid income with a trimmed description', () => {
    const onSubmit = vi.fn()
    render(<IncomeForm submitting={false} onSubmit={onSubmit} />)

    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: '  Salario  ' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '1500.50' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar ingreso' }))

    expect(onSubmit).toHaveBeenCalledWith({
      fecha: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
      descripcion: 'Salario',
      valor: '1500.50',
    })
  })

  it('shows validation errors and does not submit invalid data', () => {
    const onSubmit = vi.fn()
    render(<IncomeForm submitting={false} onSubmit={onSubmit} />)

    fireEvent.click(screen.getByRole('button', { name: 'Guardar ingreso' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      'La descripción es obligatoria.',
    )
    expect(onSubmit).not.toHaveBeenCalled()

    fireEvent.change(screen.getByLabelText('Descripción'), {
      target: { value: 'Salario' },
    })
    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '0' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar ingreso' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      'El valor debe ser mayor que 0.',
    )

    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '1.234' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar ingreso' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      'El valor admite como máximo 2 decimales.',
    )

    fireEvent.change(screen.getByLabelText('Valor'), {
      target: { value: '10000000000.00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar ingreso' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      'El valor admite como máximo 12 dígitos.',
    )
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('fills the form in edit mode and can cancel', () => {
    const onSubmit = vi.fn()
    const onCancelEdit = vi.fn()
    render(
      <IncomeForm
        initial={income}
        submitting={false}
        onSubmit={onSubmit}
        onCancelEdit={onCancelEdit}
      />,
    )

    expect(screen.getByLabelText('Fecha')).toHaveValue(income.fecha)
    expect(screen.getByLabelText('Descripción')).toHaveValue(
      income.descripcion,
    )
    expect(screen.getByLabelText('Valor')).toHaveValue(Number(income.valor))
    expect(
      screen.getByRole('button', { name: 'Guardar cambios' }),
    ).toBeInTheDocument()

    fireEvent.click(
      screen.getByRole('button', { name: 'Cancelar edición' }),
    )

    expect(onCancelEdit).toHaveBeenCalled()
  })

  it('disables the submit button while submitting', () => {
    render(<IncomeForm submitting onSubmit={vi.fn()} />)

    expect(
      screen.getByRole('button', { name: 'Guardando...' }),
    ).toBeDisabled()
  })
})
