import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ExpensePayload } from '../types/expense'
import {
  createExpense,
  deleteExpense,
  listExpenses,
  updateExpense,
} from './expenses'

const payload: ExpensePayload = {
  fecha: '2026-10-21',
  descripcion: 'Mercado',
  tipo: 'NECESARIO',
  valor: '120.50',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('expenses API', () => {
  it('lists expenses', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(listExpenses()).resolves.toEqual([])

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/gastos',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it('creates an expense', async () => {
    const created = { id: 1, ...payload }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => created,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(createExpense(payload)).resolves.toEqual(created)

    expect(fetchMock).toHaveBeenCalledWith('/api/gastos', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  })

  it('updates an expense', async () => {
    const updated = { id: 1, ...payload, tipo: 'INVERSION' }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => updated,
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(
      updateExpense(1, { ...payload, tipo: 'INVERSION' }),
    ).resolves.toEqual(updated)

    expect(fetchMock).toHaveBeenCalledWith('/api/gastos/1', {
      method: 'PUT',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...payload, tipo: 'INVERSION' }),
    })
  })

  it('deletes an expense without parsing JSON', async () => {
    const json = vi.fn()
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204, json })
    vi.stubGlobal('fetch', fetchMock)

    await expect(deleteExpense(1)).resolves.toBeUndefined()

    expect(fetchMock).toHaveBeenCalledWith('/api/gastos/1', {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    })
    expect(json).not.toHaveBeenCalled()
  })
})
