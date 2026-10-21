import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, request } from './client'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('request', () => {
  it('parses a JSON response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ value: 1 }),
      }),
    )

    await expect(request<{ value: number }>('/api/test')).resolves.toEqual({
      value: 1,
    })
  })

  it('returns undefined for 204 without parsing JSON', async () => {
    const json = vi.fn()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, status: 204, json }),
    )

    await expect(
      request<void>('/api/test', { method: 'DELETE' }),
    ).resolves.toBeUndefined()
    expect(json).not.toHaveBeenCalled()
  })

  it('throws ApiError for a failed response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        json: async () => ({ detail: [] }),
      }),
    )

    await expect(request('/api/test')).rejects.toBeInstanceOf(ApiError)
  })

  it('sends the Accept header', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    })
    vi.stubGlobal('fetch', fetchMock)

    await request('/api/test')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/test',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })
})
