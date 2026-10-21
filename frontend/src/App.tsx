import { useEffect, useState } from 'react'
import { getHealth } from './api/health'
import { ApiStatus, type ApiStatusValue } from './components/ApiStatus'

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatusValue>('loading')

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    async function checkHealth() {
      try {
        const health = await getHealth(controller.signal)
        if (!active) {
          return
        }
        setApiStatus(
          health.status === 'ok' && health.database === 'ok'
            ? 'ok'
            : 'unavailable',
        )
      } catch {
        if (active) {
          setApiStatus('unavailable')
        }
      }
    }

    void checkHealth()

    return () => {
      active = false
      controller.abort()
    }
  }, [])

  return (
    <main>
      <h1>Py Personal Finance</h1>
      <p>Interfaz en construcción.</p>
      <ApiStatus status={apiStatus} />
    </main>
  )
}

export default App
