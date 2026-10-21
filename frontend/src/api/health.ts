import type { HealthResponse } from '../types/health'
import { request } from './client'

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health', { signal })
}
