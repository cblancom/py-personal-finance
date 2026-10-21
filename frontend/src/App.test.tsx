import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the project name and placeholder', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'Py Personal Finance' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Interfaz en construcción.')).toBeInTheDocument()
  })
})
