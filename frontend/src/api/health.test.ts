import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './client'
import { getHealth } from './health'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('getHealth', () => {
  it('requests the relative health endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok', database: 'ok' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(getHealth()).resolves.toEqual({
      status: 'ok',
      database: 'ok',
    })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/health',
      expect.objectContaining({
        headers: { Accept: 'application/json' },
      }),
    )
  })

  it('throws an ApiError when the API reports a failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ status: 'degraded', database: 'unavailable' }),
      }),
    )

    await expect(getHealth()).rejects.toBeInstanceOf(ApiError)
  })
})
