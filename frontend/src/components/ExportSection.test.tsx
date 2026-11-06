import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { downloadExpenses, downloadIncomes } from '../api/exports'
import type { DownloadedFile } from '../types/export'
import { ExportSection } from './ExportSection'

vi.mock('../api/exports', () => ({
  downloadIncomes: vi.fn(),
  downloadExpenses: vi.fn(),
}))

const downloadIncomesMock = vi.mocked(downloadIncomes)
const downloadExpensesMock = vi.mocked(downloadExpenses)

const downloaded: DownloadedFile = { filename: 'movimientos.csv' }

beforeEach(() => {
  vi.clearAllMocks()
  downloadIncomesMock.mockResolvedValue(downloaded)
  downloadExpensesMock.mockResolvedValue(downloaded)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ExportSection', () => {
  it('exports incomes as CSV by default', async () => {
    render(<ExportSection />)

    expect(screen.getByLabelText('Formato')).toHaveValue('csv')
    fireEvent.click(
      screen.getByRole('button', { name: 'Exportar ingresos' }),
    )

    await waitFor(() =>
      expect(downloadIncomesMock).toHaveBeenCalledWith('csv'),
    )
  })

  it('exports expenses in the selected format', async () => {
    render(<ExportSection />)

    fireEvent.change(screen.getByLabelText('Formato'), {
      target: { value: 'xlsx' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Exportar gastos' }),
    )

    await waitFor(() =>
      expect(downloadExpensesMock).toHaveBeenCalledWith('xlsx'),
    )
  })

  it('shows a preparing state and disables both buttons', async () => {
    let resolveDownload: (value: DownloadedFile) => void = () => undefined
    downloadIncomesMock.mockReturnValue(
      new Promise<DownloadedFile>((resolve) => {
        resolveDownload = resolve
      }),
    )
    render(<ExportSection />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Exportar ingresos' }),
    )

    expect(
      screen.getByRole('button', { name: 'Preparando...' }),
    ).toBeDisabled()
    expect(
      screen.getByRole('button', { name: 'Exportar gastos' }),
    ).toBeDisabled()

    resolveDownload(downloaded)

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Exportar ingresos' }),
      ).toBeEnabled(),
    )
  })

  it('shows an accessible error when the download fails', async () => {
    downloadExpensesMock.mockRejectedValue(new Error('fail'))
    render(<ExportSection />)

    fireEvent.click(
      screen.getByRole('button', { name: 'Exportar gastos' }),
    )

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudo exportar el archivo.',
    )
  })
})
