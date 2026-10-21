export type ApiStatusValue = 'loading' | 'ok' | 'unavailable'

const statusMessages: Record<ApiStatusValue, string> = {
  loading: 'Consultando API...',
  ok: 'API disponible',
  unavailable: 'API no disponible',
}

interface ApiStatusProps {
  status: ApiStatusValue
}

export function ApiStatus({ status }: ApiStatusProps) {
  return (
    <p
      className={`api-status api-status--${status}`}
      role="status"
      aria-live="polite"
    >
      {statusMessages[status]}
    </p>
  )
}
