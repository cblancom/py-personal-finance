import { afterEach, describe, expect, it, vi } from 'vitest'
import type {
  ImportBatch,
  ImportPendingCount,
  ImportPendingRow,
} from '../types/import'
import {
  commitPending,
  countPending,
  discardAllPending,
  discardPending,
  listPending,
  updatePending,
  uploadImport,
} from './imports'

const batch: ImportBatch = {
  id: 1,
  nombre_archivo: 'movimientos.csv',
  tipo_archivo: 'CSV',
  tipo_movimiento: 'GASTO',
  tamano_bytes: 120,
  total_filas: 1,
  filas_importadas: 1,
  filas_pendientes: 0,
  filas_descartadas: 0,
  created_at: '2026-10-29T12:00:00Z',
}

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
  errores: [{ campo: 'tipo_gasto', mensaje: 'El tipo de gasto es obligatorio.' }],
  posible_duplicado: false,
  duplicado_de_id: null,
}

const count: ImportPendingCount = { pendientes: 1 }

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('imports API', () => {
  it('uploads a file as multipart form data', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => batch,
    })
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['contenido'], 'movimientos.csv', {
      type: 'text/csv',
    })

    await expect(uploadImport(file, 'GASTO')).resolves.toEqual(batch)

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/importaciones',
      expect.objectContaining({
        method: 'POST',
        headers: { Accept: 'application/json' },
      }),
    )
    expect(init.body).toBeInstanceOf(FormData)
    const body = init.body as FormData
    expect(body.get('archivo')).toBe(file)
    expect(body.get('tipo_movimiento')).toBe('GASTO')
  })

  it('lists pending rows', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [pending],
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(listPending()).resolves.toEqual([pending])

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/importaciones/pendientes',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it('counts pending rows', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => count,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(countPending()).resolves.toEqual(count)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/importaciones/pendientes/count',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it('updates a pending row', async () => {
    const updated = { ...pending, categoria: 'Mercado' }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => updated,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      updatePending(1, { categoria: 'Mercado', tipo_gasto: 'NECESARIO' }),
    ).resolves.toEqual(updated)

    expect(fetchMock).toHaveBeenCalledWith('/api/importaciones/pendientes/1', {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        categoria: 'Mercado',
        tipo_gasto: 'NECESARIO',
      }),
    })
  })

  it('commits a pending row', async () => {
    const imported = { ...pending, estado: 'IMPORTADO' as const }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => imported,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(commitPending(1)).resolves.toEqual(imported)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/importaciones/pendientes/1/contabilizar',
      {
        method: 'POST',
        headers: { Accept: 'application/json' },
      },
    )
  })

  it('discards a pending row without parsing JSON', async () => {
    const json = vi.fn()
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(discardPending(1)).resolves.toBeUndefined()

    expect(fetchMock).toHaveBeenCalledWith('/api/importaciones/pendientes/1', {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    })
    expect(json).not.toHaveBeenCalled()
  })

  it('discards all pending rows', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ descartados: 3 }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(discardAllPending()).resolves.toEqual({ descartados: 3 })

    expect(fetchMock).toHaveBeenCalledWith('/api/importaciones/pendientes', {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    })
  })
})
