interface ErrorBannerProps {
  message: string
  onRetry: () => void
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="error-banner" role="alert">
      <p>{message}</p>
      <button
        type="button"
        className="button button--primary"
        onClick={onRetry}
      >
        Reintentar
      </button>
    </div>
  )
}
