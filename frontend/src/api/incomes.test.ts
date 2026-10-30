import { afterEach, describe, expect, it, vi } from 'vitest'
import type { IncomePayload } from '../types/income'
import {
  createIncome,
  deleteIncome,
  listIncomes,
  updateIncome,
} from './incomes'

const payload: IncomePayload = {
  fecha: '2026-10-21',
  descripcion: 'Salario',
  categoria: null,
  valor: '1000.00',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('incomes API', () => {
  it('lists incomes', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(listIncomes()).resolves.toEqual([])

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/ingresos',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it('creates an income', async () => {
    const created = { id: 1, ...payload }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => created,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(createIncome(payload)).resolves.toEqual(created)

    expect(fetchMock).toHaveBeenCalledWith('/api/ingresos', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  })

  it('updates an income', async () => {
    const updated = { id: 1, ...payload, valor: '2000.00' }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => updated,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      updateIncome(1, { ...payload, valor: '2000.00' }),
    ).resolves.toEqual(updated)

    expect(fetchMock).toHaveBeenCalledWith('/api/ingresos/1', {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...payload, valor: '2000.00' }),
    })
  })

  it('deletes an income without parsing JSON', async () => {
    const json = vi.fn()
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204, json })
    vi.stubGlobal('fetch', fetchMock)

    await expect(deleteIncome(1)).resolves.toBeUndefined()

    expect(fetchMock).toHaveBeenCalledWith('/api/ingresos/1', {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    })
    expect(json).not.toHaveBeenCalled()
  })
})
