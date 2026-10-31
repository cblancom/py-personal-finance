import { useEffect, useState } from 'react'
import { getExpenseChart } from '../api/charts'
import { getPeriods } from '../api/monthlyBalance'
import { ErrorBanner } from './ErrorBanner'
import { ChartDataTable } from './ChartDataTable'
import { ExpenseChart } from './ExpenseChart'
import type { ChartMode, ExpenseChart as ExpenseChartData } from '../types/charts'
import type { BalancePeriods } from '../types/monthlyBalance'

const CURRENT_YEAR = new Date().getFullYear()

interface ChartSectionProps {
  refreshKey?: number
}

function hasExpenses(chart: ExpenseChartData): boolean {
  return chart.meses.some((month) =>
    Object.values(month.gastos_por_tipo).some((value) => Number(value) !== 0),
  )
}

export function ChartSection({ refreshKey = 0 }: ChartSectionProps) {
  const [periods, setPeriods] = useState<BalancePeriods | null>(null)
  const [selectedYear, setSelectedYear] = useState(CURRENT_YEAR)
  const [chart, setChart] = useState<ExpenseChartData | null>(null)
  const [mode, setMode] = useState<ChartMode>('bars')
  const [showTable, setShowTable] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [loadVersion, setLoadVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    async function load() {
      setLoading(true)
      setError(null)

      try {
        const [nextPeriods, nextChart] = await Promise.all([
          getPeriods(controller.signal),
          getExpenseChart(selectedYear, controller.signal),
        ])

        if (!active) {
          return
        }

        setPeriods(nextPeriods)
        setChart(nextChart)
      } catch {
        if (active) {
          setError('No se pudo cargar la gráfica de gastos.')
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      active = false
      controller.abort()
    }
  }, [selectedYear, refreshKey, loadVersion])

  const years = Array.from(
    new Set([selectedYear, ...(periods?.anios ?? [])]),
  ).sort((a, b) => b - a)

  const empty = chart !== null && !hasExpenses(chart)

  return (
    <section className="chart-section" aria-labelledby="chart-title">
      <div className="chart-header">
        <div>
          <h2 id="chart-title">Gastos por mes</h2>
          <p>Compara la evolución de tus gastos durante el año.</p>
        </div>

        <div className="chart-controls">
          <div className="field">
            <label htmlFor="chart-year">Año</label>
            <select
              id="chart-year"
              value={selectedYear}
              onChange={(event) => setSelectedYear(Number(event.target.value))}
              disabled={loading}
            >
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>

          <div
            className="chart-toggle"
            role="group"
            aria-label="Tipo de gráfica"
          >
            <button
              type="button"
              className="button button--ghost"
              aria-pressed={mode === 'bars'}
              onClick={() => setMode('bars')}
            >
              Barras
            </button>
            <button
              type="button"
              className="button button--ghost"
              aria-pressed={mode === 'lines'}
              onClick={() => setMode('lines')}
            >
              Líneas
            </button>
          </div>
        </div>
      </div>

      {loading && (
        <p className="status-message" role="status">
          Cargando gráfica...
        </p>
      )}

      {error && (
        <ErrorBanner
          message={error}
          onRetry={() => setLoadVersion((version) => version + 1)}
        />
      )}

      {!loading && !error && empty && (
        <p className="empty-state">No hay gastos registrados para este año.</p>
      )}

      {!loading && !error && chart !== null && !empty && (
        <>
          <ExpenseChart months={chart.meses} mode={mode} />
          <div className="chart-actions">
            <button
              type="button"
              className="button button--link"
              aria-expanded={showTable}
              onClick={() => setShowTable((current) => !current)}
            >
              {showTable ? 'Ocultar datos' : 'Ver datos'}
            </button>
          </div>
          {showTable && <ChartDataTable months={chart.meses} />}
        </>
      )}
    </section>
  )
}
