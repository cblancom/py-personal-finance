import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('renders the project name and placeholder', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))

    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'Py Personal Finance' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Interfaz en construcción.')).toBeInTheDocument()
  })

  it('shows the loading state while the health request is pending', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))

    render(<App />)

    expect(screen.getByRole('status')).toHaveTextContent('Consultando API...')
  })

  it('shows the available state when the API responds successfully', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'ok', database: 'ok' }),
      }),
    )

    render(<App />)

    expect(await screen.findByText('API disponible')).toBeInTheDocument()
  })

  it('shows the unavailable state when the API responds with an error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ status: 'degraded', database: 'unavailable' }),
      }),
    )

    render(<App />)

    expect(await screen.findByText('API no disponible')).toBeInTheDocument()
  })

  it('shows the unavailable state when the request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network down')))

    render(<App />)

    expect(await screen.findByText('API no disponible')).toBeInTheDocument()
  })
})
