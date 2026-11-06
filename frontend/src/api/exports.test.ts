import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './client'
import { downloadExpenses, downloadIncomes } from './exports'

const createObjectURL = vi.fn(() => 'blob:test')
const revokeObjectURL = vi.fn()

beforeEach(() => {
  vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function downloadResponse(disposition: string | null, blob = new Blob(['contenido'])) {
  return {
    ok: true,
    status: 200,
    headers: {
      get: vi.fn(() => disposition),
    },
    blob: vi.fn().mockResolvedValue(blob),
  }
}

describe('exports API', () => {
  it('downloads incomes as CSV', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      downloadResponse('attachment; filename="ingresos_20261106_120000.csv"'),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(downloadIncomes('csv')).resolves.toEqual({
      filename: 'ingresos_20261106_120000.csv',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/exportaciones/ingresos?formato=csv',
      {
        headers: {
          Accept:
            'text/csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, */*',
        },
      },
    )
    expect(createObjectURL).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:test')
  })

  it('downloads expenses as XLSX', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      downloadResponse('attachment; filename="gastos_20261106_120000.xlsx"'),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(downloadExpenses('xlsx')).resolves.toEqual({
      filename: 'gastos_20261106_120000.xlsx',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/exportaciones/gastos?formato=xlsx',
      expect.any(Object),
    )
  })

  it('uses a fallback filename when Content-Disposition is absent', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(downloadResponse(null)))

    await expect(downloadIncomes('csv')).resolves.toEqual({
      filename: 'ingresos.csv',
    })
  })

  it('throws ApiError when the download fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      }),
    )

    await expect(downloadExpenses('csv')).rejects.toBeInstanceOf(ApiError)
  })
})
