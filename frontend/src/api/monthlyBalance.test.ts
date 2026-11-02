import { afterEach, describe, expect, it, vi } from 'vitest'
import type {
  AnnualBalance,
  BalancePeriods,
  MonthlyBalance,
} from '../types/monthlyBalance'
import {
  getAnnualBalance,
  getMonthlyBalance,
  getPeriods,
  updateAllocations,
} from './monthlyBalance'

const monthly: MonthlyBalance = {
  anio: 2026,
  mes: 10,
  ingresos: '5000.00',
  sin_asignar: '0.00',
  rubros: {
    NECESARIO: {
      porcentaje: '50.00',
      asignado: '2500.00',
      arrastre: '0.00',
      disponible: '2500.00',
      gastado: '1000.00',
      restante: '1500.00',
    },
    NO_NECESARIO: {
      porcentaje: '30.00',
      asignado: '1500.00',
      arrastre: '0.00',
      disponible: '1500.00',
      gastado: '300.00',
      restante: '1200.00',
    },
    INVERSION: {
      porcentaje: '20.00',
      asignado: '1000.00',
      arrastre: '0.00',
      disponible: '1000.00',
      gastado: '200.00',
      restante: '800.00',
    },
  },
  movimientos: {
    INGRESOS: [],
    NECESARIO: [],
    NO_NECESARIO: [],
    INVERSION: [],
  },
}

const annual: AnnualBalance = {
  anio: 2026,
  mes: null,
  ingresos: '5000.00',
  sin_asignar: '0.00',
  rubros: monthly.rubros,
}

const periods: BalancePeriods = {
  anio_actual: 2026,
  anios: [2026, 2025],
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('monthly balance API', () => {
  it('loads available periods', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => periods,
    })
    vi.stubGlobal('fetch', fetchMock)
    const controller = new AbortController()

    await expect(getPeriods(controller.signal)).resolves.toEqual(periods)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/balance-mensual/periodos',
      expect.objectContaining({
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it('loads a monthly balance', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => monthly,
    })
    vi.stubGlobal('fetch', fetchMock)
    const controller = new AbortController()

    await expect(
      getMonthlyBalance(2026, 10, controller.signal),
    ).resolves.toEqual(monthly)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/balance-mensual?anio=2026&mes=10',
      expect.objectContaining({
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it('loads an annual balance', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => annual,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(getAnnualBalance(2026)).resolves.toEqual(annual)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/balance-mensual?anio=2026',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it('updates monthly allocation percentages', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => monthly,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      updateAllocations(2026, 10, {
        NECESARIO: '50.00',
        NO_NECESARIO: '30.00',
        INVERSION: '20.00',
      }),
    ).resolves.toEqual(monthly)

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/balance-mensual/asignaciones/2026/10',
      {
        method: 'PUT',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          porcentajes: {
            NECESARIO: '50.00',
            NO_NECESARIO: '30.00',
            INVERSION: '20.00',
          },
        }),
      },
    )
  })
})
