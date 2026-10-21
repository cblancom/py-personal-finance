import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Summary } from '../types/summary'
import { getSummary } from './summary'

const summary: Summary = {
  total_ingresos: '1000.00',
  total_gastos: '500.00',
  balance: '500.00',
  gastos_por_tipo: {
    NECESARIO: '300.00',
    NO_NECESARIO: '0.00',
    INVERSION: '200.00',
  },
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('summary API', () => {
  it('gets the summary', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => summary,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(getSummary()).resolves.toEqual(summary)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/resumen',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })
})
