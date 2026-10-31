import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ExpenseChart } from '../types/charts'
import { getExpenseChart } from './charts'

const chart: ExpenseChart = {
  anio: 2026,
  meses: [
    {
      mes: 1,
      gastos_por_tipo: {
        NECESARIO: '100.00',
        NO_NECESARIO: '50.00',
        INVERSION: '20.00',
      },
    },
  ],
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('charts API', () => {
  it('loads the monthly expense series', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => chart,
    })
    vi.stubGlobal('fetch', fetchMock)
    const controller = new AbortController()

    await expect(getExpenseChart(2026, controller.signal)).resolves.toEqual(chart)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/graficos/gastos-mensuales?anio=2026',
      expect.objectContaining({
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      }),
    )
  })
})
