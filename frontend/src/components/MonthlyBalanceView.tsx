import { useEffect, useState } from 'react'
import { ErrorBanner } from './ErrorBanner'
import {
  getAnnualBalance,
  getMonthlyBalance,
  getPeriods,
  updateAllocations,
} from '../api/monthlyBalance'
import { EXPENSE_TYPES } from '../types/expense'
import type {
  AllocationPercentages,
  AnnualBalance,
  BalanceMovement,
  BalancePeriods,
  MonthlyBalance,
} from '../types/monthlyBalance'
import {
  expenseTypeLabel,
  formatDate,
  formatMoney,
} from '../utils/format'

const CURRENT_YEAR = new Date().getFullYear()

const MONTHS = [
  'Enero',
  'Febrero',
  'Marzo',
  'Abril',
  'Mayo',
  'Junio',
  'Julio',
  'Agosto',
  'Septiembre',
  'Octubre',
  'Noviembre',
  'Diciembre',
]

const EMPTY_PERCENTAGES: AllocationPercentages = {
  NECESARIO: '0.00',
  NO_NECESARIO: '0.00',
  INVERSION: '0.00',
}

interface SummaryItem {
  label: string
  value: string
  negative?: boolean
}

interface BalanceColumnProps {
  id: string
  title: string
  items: BalanceMovement[]
  total: string
  summary: SummaryItem[]
}

function BalanceColumn({ id, title, items, total, summary }: BalanceColumnProps) {
  return (
    <section className="balance-column" aria-labelledby={id}>
      <header className="balance-column__header">
        <h3 id={id}>{title}</h3>
        <p className="balance-column__total">{formatMoney(total)}</p>
      </header>

      <div className="balance-column__table-wrap">
        <table className="balance-table">
          <thead>
            <tr>
              <th scope="col">Fecha</th>
              <th scope="col">Descripción</th>
              <th scope="col" className="amount">
                Valor
              </th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={3} className="balance-table__empty">
                  Sin movimientos
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id}>
                  <td>{formatDate(item.fecha)}</td>
                  <td>{item.descripcion}</td>
                  <td className="amount">{formatMoney(item.valor)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <dl className="balance-column__summary">
        {summary.map((item) => (
          <div key={item.label}>
            <dt>{item.label}</dt>
            <dd className={item.negative ? 'balance-negative' : undefined}>
              {item.value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

function AnnualBalanceTable({ balance }: { balance: AnnualBalance }) {
  return (
    <section className="balance-annual" aria-labelledby="annual-balance-title">
      <div className="balance-annual__summary">
        <div>
          <span>Ingresos del año</span>
          <strong>{formatMoney(balance.ingresos)}</strong>
        </div>
        <div>
          <span>Sin asignar</span>
          <strong>{formatMoney(balance.sin_asignar)}</strong>
        </div>
      </div>

      <div className="balance-table-wrap">
        <table className="balance-table balance-table--annual">
          <caption id="annual-balance-title">Balance anual</caption>
          <thead>
            <tr>
              <th scope="col">Rubro</th>
              <th scope="col">Porcentaje ponderado</th>
              <th scope="col" className="amount">
                Asignado
              </th>
              <th scope="col" className="amount">
                Gastado
              </th>
              <th scope="col" className="amount">
                Restante
              </th>
            </tr>
          </thead>
          <tbody>
            {EXPENSE_TYPES.map((type) => {
              const rubro = balance.rubros[type]
              const negative = rubro.restante.startsWith('-')
              return (
                <tr key={type}>
                  <th scope="row">{expenseTypeLabel(type)}</th>
                  <td>{rubro.porcentaje}%</td>
                  <td className="amount">{formatMoney(rubro.asignado)}</td>
                  <td className="amount">{formatMoney(rubro.gastado)}</td>
                  <td className={negative ? 'amount balance-negative' : 'amount'}>
                    {formatMoney(rubro.restante)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function toPercentages(balance: MonthlyBalance): AllocationPercentages {
  return {
    NECESARIO: balance.rubros.NECESARIO.porcentaje,
    NO_NECESARIO: balance.rubros.NO_NECESARIO.porcentaje,
    INVERSION: balance.rubros.INVERSION.porcentaje,
  }
}

function normalizePercentages(values: AllocationPercentages): AllocationPercentages {
  return {
    NECESARIO: values.NECESARIO.trim().replace(',', '.'),
    NO_NECESARIO: values.NO_NECESARIO.trim().replace(',', '.'),
    INVERSION: values.INVERSION.trim().replace(',', '.'),
  }
}

function validatePercentages(values: AllocationPercentages): string | null {
  const normalized = normalizePercentages(values)
  let total = 0

  for (const type of EXPENSE_TYPES) {
    const value = normalized[type]
    if (!/^\d{1,3}(?:\.\d{1,2})?$/.test(value)) {
      return 'Cada porcentaje debe tener como máximo dos decimales.'
    }

    const parsed = Number(value)
    if (parsed < 0 || parsed > 100) {
      return 'Cada porcentaje debe estar entre 0 y 100.'
    }
    total += parsed
  }

  if (total > 100) {
    return 'La suma de los porcentajes no puede superar 100.'
  }

  return null
}

export function MonthlyBalanceView() {
  const [periods, setPeriods] = useState<BalancePeriods | null>(null)
  const [selectedYear, setSelectedYear] = useState(CURRENT_YEAR)
  const [selectedMonth, setSelectedMonth] = useState<number | ''>('')
  const [balance, setBalance] = useState<MonthlyBalance | AnnualBalance | null>(null)
  const [percentages, setPercentages] = useState<AllocationPercentages>(EMPTY_PERCENTAGES)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [loadVersion, setLoadVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    async function load() {
      setLoading(true)
      setError(null)

      try {
        const [nextPeriods, nextBalance] = await Promise.all([
          getPeriods(controller.signal),
          selectedMonth === ''
            ? getAnnualBalance(selectedYear, controller.signal)
            : getMonthlyBalance(selectedYear, selectedMonth, controller.signal),
        ])

        if (!active) {
          return
        }

        setPeriods(nextPeriods)
        setBalance(nextBalance)
        if (nextBalance.mes !== null) {
          setPercentages(toPercentages(nextBalance))
        }
      } catch {
        if (active) {
          setError('No se pudo cargar el balance mensual.')
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
  }, [selectedYear, selectedMonth, loadVersion])

  const years = Array.from(
    new Set([selectedYear, ...(periods?.anios ?? [])]),
  ).sort((a, b) => b - a)

  function handleYearChange(value: string) {
    setSelectedYear(Number(value))
    setSaveError(null)
    setSaveMessage(null)
  }

  function handleMonthChange(value: string) {
    setSelectedMonth(value === '' ? '' : Number(value))
    setSaveError(null)
    setSaveMessage(null)
  }

  async function handleSave() {
    if (balance === null || balance.mes === null) {
      return
    }

    const validationError = validatePercentages(percentages)
    if (validationError !== null) {
      setSaveError(validationError)
      setSaveMessage(null)
      return
    }

    setSaving(true)
    setSaveError(null)
    setSaveMessage(null)

    try {
      const updated = await updateAllocations(
        selectedYear,
        balance.mes,
        normalizePercentages(percentages),
      )
      setBalance(updated)
      setPercentages(toPercentages(updated))
      setSaveMessage('Porcentajes guardados.')
    } catch {
      setSaveError('No se pudieron guardar los porcentajes. Inténtalo de nuevo.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="balance-view" aria-labelledby="balance-view-title">
      <div className="view-header">
        <div>
          <h2 id="balance-view-title">Balance mensual</h2>
          <p>
            Compara tus movimientos con los porcentajes asignados a cada rubro.
          </p>
        </div>
      </div>

      <div className="balance-filters">
        <div className="field">
          <label htmlFor="balance-year">Año</label>
          <select
            id="balance-year"
            value={selectedYear}
            onChange={(event) => handleYearChange(event.target.value)}
            disabled={loading || saving}
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="balance-month">Mes</label>
          <select
            id="balance-month"
            value={selectedMonth}
            onChange={(event) => handleMonthChange(event.target.value)}
            disabled={loading || saving}
          >
            <option value="">Todos</option>
            {MONTHS.map((month, index) => (
              <option key={month} value={index + 1}>
                {month}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <p className="status-message" role="status">
          Cargando balance...
        </p>
      )}

      {error && (
        <ErrorBanner
          message={error}
          onRetry={() => setLoadVersion((version) => version + 1)}
        />
      )}

      {!loading && !error && balance !== null && balance.mes === null && (
        <AnnualBalanceTable balance={balance} />
      )}

      {!loading && !error && balance !== null && balance.mes !== null && (
        <>
          <section
            className="balance-allocation"
            aria-labelledby="balance-allocation-title"
          >
            <h3 id="balance-allocation-title">Porcentajes del mes</h3>
            <div className="balance-allocation__fields">
              {EXPENSE_TYPES.map((type) => (
                <div className="field" key={type}>
                  <label htmlFor={`allocation-${type}`}>
                    {expenseTypeLabel(type)}
                  </label>
                  <input
                    id={`allocation-${type}`}
                    type="text"
                    inputMode="decimal"
                    value={percentages[type]}
                    onChange={(event) =>
                      setPercentages((current) => ({
                        ...current,
                        [type]: event.target.value,
                      }))
                    }
                    disabled={saving}
                  />
                </div>
              ))}
            </div>
            <div className="balance-allocation__actions">
              <button
                type="button"
                className="button button--primary"
                onClick={() => void handleSave()}
                disabled={saving}
              >
                {saving ? 'Guardando...' : 'Guardar porcentajes'}
              </button>
            </div>
            {saveError && (
              <p className="form-error" role="alert">
                {saveError}
              </p>
            )}
            {saveMessage && (
              <p className="balance-success" role="status">
                {saveMessage}
              </p>
            )}
          </section>

          <div className="balance-columns">
            <BalanceColumn
              id="balance-incomes-title"
              title="Ingresos"
              items={balance.movimientos.INGRESOS}
              total={balance.ingresos}
              summary={[
                {
                  label: 'Sin asignar',
                  value: formatMoney(balance.sin_asignar),
                },
              ]}
            />
            <BalanceColumn
              id="balance-necessary-title"
              title="Gastos necesarios"
              items={balance.movimientos.NECESARIO}
              total={balance.rubros.NECESARIO.gastado}
              summary={[
                {
                  label: 'Porcentaje',
                  value: `${balance.rubros.NECESARIO.porcentaje}%`,
                },
                {
                  label: 'Asignado',
                  value: formatMoney(balance.rubros.NECESARIO.asignado),
                },
                {
                  label: 'Restante',
                  value: formatMoney(balance.rubros.NECESARIO.restante),
                  negative: balance.rubros.NECESARIO.restante.startsWith('-'),
                },
              ]}
            />
            <BalanceColumn
              id="balance-non-necessary-title"
              title="Gastos no necesarios"
              items={balance.movimientos.NO_NECESARIO}
              total={balance.rubros.NO_NECESARIO.gastado}
              summary={[
                {
                  label: 'Porcentaje',
                  value: `${balance.rubros.NO_NECESARIO.porcentaje}%`,
                },
                {
                  label: 'Asignado',
                  value: formatMoney(balance.rubros.NO_NECESARIO.asignado),
                },
                {
                  label: 'Restante',
                  value: formatMoney(balance.rubros.NO_NECESARIO.restante),
                  negative: balance.rubros.NO_NECESARIO.restante.startsWith('-'),
                },
              ]}
            />
            <BalanceColumn
              id="balance-investment-title"
              title="Inversión"
              items={balance.movimientos.INVERSION}
              total={balance.rubros.INVERSION.gastado}
              summary={[
                {
                  label: 'Porcentaje',
                  value: `${balance.rubros.INVERSION.porcentaje}%`,
                },
                {
                  label: 'Asignado',
                  value: formatMoney(balance.rubros.INVERSION.asignado),
                },
                {
                  label: 'Restante',
                  value: formatMoney(balance.rubros.INVERSION.restante),
                  negative: balance.rubros.INVERSION.restante.startsWith('-'),
                },
              ]}
            />
          </div>
        </>
      )}
    </section>
  )
}
