import type { Summary } from '../types/summary'
import { request } from './client'

export function getSummary(signal?: AbortSignal): Promise<Summary> {
  return request<Summary>('/api/resumen', { signal })
}
