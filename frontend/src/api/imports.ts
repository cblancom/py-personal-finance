import type {
  ImportBatch,
  ImportMovementType,
  ImportPendingCount,
  ImportPendingRow,
  ImportPendingUpdate,
} from '../types/import'
import { request } from './client'

export function uploadImport(
  file: File,
  movementType: ImportMovementType,
): Promise<ImportBatch> {
  const body = new FormData()
  body.append('archivo', file)
  body.append('tipo_movimiento', movementType)

  return request<ImportBatch>('/api/importaciones', {
    method: 'POST',
    body,
  })
}

export function listPending(signal?: AbortSignal): Promise<ImportPendingRow[]> {
  return request<ImportPendingRow[]>('/api/importaciones/pendientes', { signal })
}

export function countPending(signal?: AbortSignal): Promise<ImportPendingCount> {
  return request<ImportPendingCount>('/api/importaciones/pendientes/count', {
    signal,
  })
}

export function updatePending(
  id: number,
  payload: ImportPendingUpdate,
): Promise<ImportPendingRow> {
  return request<ImportPendingRow>(`/api/importaciones/pendientes/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function commitPending(id: number): Promise<ImportPendingRow> {
  return request<ImportPendingRow>(
    `/api/importaciones/pendientes/${id}/contabilizar`,
    { method: 'POST' },
  )
}

export function discardPending(id: number): Promise<void> {
  return request<void>(`/api/importaciones/pendientes/${id}`, {
    method: 'DELETE',
  })
}
