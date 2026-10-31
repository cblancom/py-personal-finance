import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  commitPending,
  discardPending,
  listPending,
  updatePending,
} from '../api/imports'
import type { ImportPendingRow } from '../types/import'
import { PendingView } from './PendingView'

vi.mock('../api/imports', () => ({
  listPending: vi.fn(),
  updatePending: vi.fn(),
  commitPending: vi.fn(),
  discardPending: vi.fn(),
}))

const listPendingMock = vi.mocked(listPending)
const updatePendingMock = vi.mocked(updatePending)
const commitPendingMock = vi.mocked(commitPending)
const discardPendingMock = vi.mocked(discardPending)

const pending: ImportPendingRow = {
  id: 1,
  lote_id: 1,
  numero_fila: 2,
  tipo_movimiento: 'GASTO',
  fecha: '2026-10-21',
  descripcion: 'Mercado',
  valor: '120.50',
  categoria: null,
  tipo_gasto: null,
  estado: 'PENDIENTE',
  errores: [
    { campo: 'categoria', mensaje: 'La categoría es obligatoria para gastos.' },
  ],
  posible_duplicado: false,
  duplicado_de_id: null,
}

const updated: ImportPendingRow = {
  ...pending,
  categoria: 'No Necesario',
  tipo_gasto: 'NO_NECESARIO',
  errores: [],
}

beforeEach(() => {
  vi.clearAllMocks()
  listPendingMock.mockResolvedValue([pending])
  updatePendingMock.mockResolvedValue(updated)
  commitPendingMock.mockResolvedValue({
    ...updated,
    estado: 'IMPORTADO',
  })
  discardPendingMock.mockResolvedValue(undefined)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('PendingView', () => {
  it('loads pending rows with their validation errors', async () => {
    render(<PendingView onBack={vi.fn()} onChanged={vi.fn()} />)

    expect(
      await screen.findByRole('heading', { name: 'Pendientes' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Mercado')).toBeInTheDocument()
    expect(
      screen.getByText('La categoría es obligatoria para gastos.'),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Contabilizar' }),
    ).toBeDisabled()
  })

  it('saves and commits a pending row', async () => {
    const onChanged = vi.fn()
    render(<PendingView onBack={vi.fn()} onChanged={onChanged} />)

    await screen.findByText('Mercado')
    fireEvent.change(screen.getByLabelText('Categoría'), {
      target: { value: 'No Necesario' },
    })
    fireEvent.change(screen.getByLabelText('Tipo de gasto'), {
      target: { value: 'NO_NECESARIO' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(updatePendingMock).toHaveBeenCalled())
    expect(updatePendingMock).toHaveBeenCalledWith(
      1,
      expect.objectContaining({
        descripcion: 'Mercado',
        valor: '120.50',
        categoria: 'No Necesario',
        tipo_gasto: 'NO_NECESARIO',
      }),
    )

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Contabilizar' }),
      ).toBeEnabled(),
    )
    fireEvent.click(screen.getByRole('button', { name: 'Contabilizar' }))

    await waitFor(() => expect(commitPendingMock).toHaveBeenCalledWith(1))
    expect(onChanged).toHaveBeenCalled()
    expect(
      await screen.findByText('No hay registros pendientes.'),
    ).toBeInTheDocument()
  })

  it('discards a pending row after confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const onChanged = vi.fn()
    render(<PendingView onBack={vi.fn()} onChanged={onChanged} />)

    await screen.findByText('Mercado')
    fireEvent.click(screen.getByRole('button', { name: 'Descartar' }))

    await waitFor(() => expect(discardPendingMock).toHaveBeenCalledWith(1))
    expect(onChanged).toHaveBeenCalled()
    expect(
      await screen.findByText('No hay registros pendientes.'),
    ).toBeInTheDocument()
  })

  it('does not discard when confirmation is cancelled', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<PendingView onBack={vi.fn()} onChanged={vi.fn()} />)

    await screen.findByText('Mercado')
    fireEvent.click(screen.getByRole('button', { name: 'Descartar' }))

    expect(discardPendingMock).not.toHaveBeenCalled()
  })

  it('shows a load error and retries', async () => {
    listPendingMock.mockRejectedValueOnce(new Error('down'))
    render(<PendingView onBack={vi.fn()} onChanged={vi.fn()} />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudieron cargar los pendientes.',
    )
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByText('Mercado')).toBeInTheDocument()
  })
})
