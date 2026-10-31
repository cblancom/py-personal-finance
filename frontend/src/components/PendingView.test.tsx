import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  commitPending,
  discardAllPending,
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
  discardAllPending: vi.fn(),
}))

const listPendingMock = vi.mocked(listPending)
const updatePendingMock = vi.mocked(updatePending)
const commitPendingMock = vi.mocked(commitPending)
const discardPendingMock = vi.mocked(discardPending)
const discardAllPendingMock = vi.mocked(discardAllPending)

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
    { campo: 'tipo_gasto', mensaje: 'El tipo de gasto es obligatorio.' },
  ],
  posible_duplicado: false,
  duplicado_de_id: null,
}

const updated: ImportPendingRow = {
  ...pending,
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
  discardAllPendingMock.mockResolvedValue({ descartados: 1 })
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
      screen.getByText('El tipo de gasto es obligatorio.'),
    ).toBeInTheDocument()
    expect(screen.queryByLabelText('Categoría')).not.toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Contabilizar' }),
    ).toBeDisabled()
  })

  it('saves and commits a pending row', async () => {
    const onChanged = vi.fn()
    render(<PendingView onBack={vi.fn()} onChanged={onChanged} />)

    await screen.findByText('Mercado')
    fireEvent.change(screen.getByLabelText('Tipo de gasto'), {
      target: { value: 'NO_NECESARIO' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(updatePendingMock).toHaveBeenCalled())
    expect(updatePendingMock).toHaveBeenCalledWith(1, {
      fecha: '2026-10-21',
      descripcion: 'Mercado',
      valor: '120.50',
      tipo_gasto: 'NO_NECESARIO',
    })

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

  it('discards all pending rows after confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const onChanged = vi.fn()
    render(<PendingView onBack={vi.fn()} onChanged={onChanged} />)

    await screen.findByText('Mercado')
    fireEvent.click(screen.getByRole('button', { name: 'Descartar todo' }))

    await waitFor(() => expect(discardAllPendingMock).toHaveBeenCalledTimes(1))
    expect(onChanged).toHaveBeenCalled()
    expect(
      await screen.findByText('No hay registros pendientes.'),
    ).toBeInTheDocument()
  })

  it('does not discard all when confirmation is cancelled', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<PendingView onBack={vi.fn()} onChanged={vi.fn()} />)

    await screen.findByText('Mercado')
    fireEvent.click(screen.getByRole('button', { name: 'Descartar todo' }))

    expect(discardAllPendingMock).not.toHaveBeenCalled()
  })

  it('disables discard all when there are no pending rows', async () => {
    listPendingMock.mockResolvedValue([])
    render(<PendingView onBack={vi.fn()} onChanged={vi.fn()} />)

    expect(
      await screen.findByText('No hay registros pendientes.'),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Descartar todo' }),
    ).toBeDisabled()
  })

  it('shows category only for income pending rows', async () => {
    listPendingMock.mockResolvedValue([
      {
        ...pending,
        tipo_movimiento: 'INGRESO',
        categoria: 'Nómina',
        tipo_gasto: null,
        errores: [],
      },
    ])
    render(<PendingView onBack={vi.fn()} onChanged={vi.fn()} />)

    expect(await screen.findByLabelText('Categoría')).toHaveValue('Nómina')
    expect(screen.queryByLabelText('Tipo de gasto')).not.toBeInTheDocument()
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

  it('allows committing a possible duplicate after review', async () => {
    const duplicate: ImportPendingRow = {
      ...updated,
      posible_duplicado: true,
      errores: [
        {
          campo: 'duplicado',
          mensaje: 'Posible duplicado; revisa antes de contabilizar.',
        },
      ],
    }
    listPendingMock.mockResolvedValue([duplicate])
    commitPendingMock.mockResolvedValue({ ...duplicate, estado: 'IMPORTADO' })
    const onChanged = vi.fn()
    render(<PendingView onBack={vi.fn()} onChanged={onChanged} />)

    expect(await screen.findByText(/Posible duplicado/)).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Contabilizar' }),
    ).toBeEnabled()

    fireEvent.click(screen.getByRole('button', { name: 'Contabilizar' }))

    await waitFor(() => expect(commitPendingMock).toHaveBeenCalledWith(1))
    expect(onChanged).toHaveBeenCalled()
  })
})
