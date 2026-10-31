import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import { uploadImport } from '../api/imports'
import type { ImportBatch } from '../types/import'
import { ImportView } from './ImportView'

vi.mock('../api/imports', () => ({
  uploadImport: vi.fn(),
}))

const uploadImportMock = vi.mocked(uploadImport)

const batch: ImportBatch = {
  id: 1,
  nombre_archivo: 'movimientos.csv',
  tipo_archivo: 'CSV',
  tipo_movimiento: 'GASTO',
  tamano_bytes: 120,
  total_filas: 3,
  filas_importadas: 2,
  filas_pendientes: 1,
  filas_descartadas: 0,
  created_at: '2026-10-29T12:00:00Z',
}

function selectFile(name = 'movimientos.csv'): void {
  const file = new File(['contenido'], name, { type: 'text/csv' })
  fireEvent.change(screen.getByLabelText('Archivo CSV o XLSX'), {
    target: { files: [file] },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ImportView', () => {
  it('requires a file before submitting', () => {
    render(<ImportView onBack={vi.fn()} onImported={vi.fn()} />)

    expect(
      screen.getByRole('button', { name: 'Importar archivo' }),
    ).toBeDisabled()
  })

  it('uploads a selected file and shows the result', async () => {
    uploadImportMock.mockResolvedValue(batch)
    const onImported = vi.fn()
    const onOpenPending = vi.fn()
    render(
      <ImportView
        onBack={vi.fn()}
        onImported={onImported}
        onOpenPending={onOpenPending}
      />,
    )

    selectFile()
    fireEvent.change(screen.getByLabelText('Tipo de movimiento'), {
      target: { value: 'GASTO' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Importar archivo' }))

    expect(
      await screen.findByRole('heading', { name: 'Resultado de la importación' }),
    ).toBeInTheDocument()
    expect(uploadImportMock).toHaveBeenCalledWith(
      expect.any(File),
      'GASTO',
    )
    expect(onImported).toHaveBeenCalledWith(batch)
    expect(screen.getByText(/movimientos.csv/)).toBeInTheDocument()

    fireEvent.click(
      screen.getByRole('button', { name: 'Revisar pendientes' }),
    )
    expect(onOpenPending).toHaveBeenCalled()
  })

  it('shows a clear error for an unsupported file', async () => {
    uploadImportMock.mockRejectedValue(new ApiError(415))
    render(<ImportView onBack={vi.fn()} onImported={vi.fn()} />)

    selectFile('movimientos.txt')
    fireEvent.click(screen.getByRole('button', { name: 'Importar archivo' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'El archivo debe ser CSV o XLSX.',
    )
  })

  it('calls onBack', () => {
    const onBack = vi.fn()
    render(<ImportView onBack={onBack} onImported={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: 'Volver' }))

    expect(onBack).toHaveBeenCalled()
  })

  it.each([
    [413, 'El archivo es demasiado grande.'],
    [422, 'El archivo no tiene el formato esperado.'],
  ])('maps HTTP %s to a clear message', async (status, message) => {
    uploadImportMock.mockRejectedValue(new ApiError(status))
    render(<ImportView onBack={vi.fn()} onImported={vi.fn()} />)

    selectFile()
    fireEvent.click(screen.getByRole('button', { name: 'Importar archivo' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(message)
  })

  it('disables the submit button while importing', async () => {
    let resolveImport: (value: ImportBatch) => void = () => undefined
    uploadImportMock.mockReturnValue(
      new Promise<ImportBatch>((resolve) => {
        resolveImport = resolve
      }),
    )
    render(<ImportView onBack={vi.fn()} onImported={vi.fn()} />)

    selectFile()
    fireEvent.click(screen.getByRole('button', { name: 'Importar archivo' }))

    expect(
      screen.getByRole('button', { name: 'Importando...' }),
    ).toBeDisabled()

    resolveImport(batch)
    expect(
      await screen.findByRole('heading', { name: 'Resultado de la importación' }),
    ).toBeInTheDocument()
  })
})
