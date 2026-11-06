import type { DownloadedFile, ExportFormat } from '../types/export'
import { ApiError } from './client'

const EXPORT_ACCEPT =
  'text/csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, */*'

function filenameFromDisposition(header: string | null, fallback: string): string {
  if (!header) {
    return fallback
  }

  const match = /filename="?([^";]+)"?/i.exec(header)
  return match?.[1] ?? fallback
}

async function download(path: string, fallback: string): Promise<DownloadedFile> {
  const response = await fetch(path, {
    headers: { Accept: EXPORT_ACCEPT },
  })

  if (!response.ok) {
    throw new ApiError(response.status)
  }

  const blob = await response.blob()
  const filename = filenameFromDisposition(
    response.headers.get('Content-Disposition'),
    fallback,
  )
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.append(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)

  return { filename }
}

export function downloadIncomes(format: ExportFormat): Promise<DownloadedFile> {
  return download(
    `/api/exportaciones/ingresos?formato=${format}`,
    `ingresos.${format}`,
  )
}

export function downloadExpenses(format: ExportFormat): Promise<DownloadedFile> {
  return download(
    `/api/exportaciones/gastos?formato=${format}`,
    `gastos.${format}`,
  )
}
