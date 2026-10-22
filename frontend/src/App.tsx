import { useEffect, useState } from 'react'
import { listExpenses } from './api/expenses'
import { listIncomes } from './api/incomes'
import { getSummary } from './api/summary'
import { ErrorBanner } from './components/ErrorBanner'
import { ExpenseSection } from './components/ExpenseSection'
import { IncomeSection } from './components/IncomeSection'
import { SummaryPanel } from './components/SummaryPanel'
import type { Expense } from './types/expense'
import type { Income } from './types/income'
import type { Summary } from './types/summary'

type ActiveTab = 'incomes' | 'expenses'

function App() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [incomes, setIncomes] = useState<Income[]>([])
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [activeTab, setActiveTab] = useState<ActiveTab>('incomes')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [loadVersion, setLoadVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    async function loadData() {
      setLoading(true)
      setError(null)

      try {
        const [nextSummary, nextIncomes, nextExpenses] = await Promise.all([
          getSummary(controller.signal),
          listIncomes(controller.signal),
          listExpenses(controller.signal),
        ])

        if (!active) {
          return
        }

        setSummary(nextSummary)
        setIncomes(nextIncomes)
        setExpenses(nextExpenses)
      } catch {
        if (active) {
          setError(
            'No se pudieron cargar los datos. Verifica que la API esté disponible.',
          )
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void loadData()

    return () => {
      active = false
      controller.abort()
    }
  }, [loadVersion])

  function reloadData() {
    setLoadVersion((version) => version + 1)
  }

  return (
    <main>
      <header className="app-header">
        <h1>Py Personal Finance</h1>
        <p>Registra tus ingresos y gastos y consulta tu balance.</p>
        <p className="app-note">Importes en pesos colombianos (COP).</p>
      </header>

      {loading && summary === null && (
        <p className="status-message" role="status">
          Cargando datos...
        </p>
      )}

      {error && <ErrorBanner message={error} onRetry={reloadData} />}

      {summary && <SummaryPanel summary={summary} />}

      {summary && (
        <>
          <div className="tabs" role="tablist" aria-label="Movimientos">
            <button
              type="button"
              role="tab"
              id="incomes-tab"
              className="tab"
              aria-selected={activeTab === 'incomes'}
              onClick={() => setActiveTab('incomes')}
            >
              Ingresos
            </button>
            <button
              type="button"
              role="tab"
              id="expenses-tab"
              className="tab"
              aria-selected={activeTab === 'expenses'}
              onClick={() => setActiveTab('expenses')}
            >
              Gastos
            </button>
          </div>

          {activeTab === 'incomes' ? (
            <div
              role="tabpanel"
              id="incomes-panel"
              aria-labelledby="incomes-tab"
            >
              <IncomeSection incomes={incomes} onChanged={reloadData} />
            </div>
          ) : (
            <div
              role="tabpanel"
              id="expenses-panel"
              aria-labelledby="expenses-tab"
            >
              <ExpenseSection expenses={expenses} onChanged={reloadData} />
            </div>
          )}
        </>
      )}

      {loading && summary !== null && (
        <p className="status-message" role="status">
          Actualizando datos...
        </p>
      )}
    </main>
  )
}

export default App
