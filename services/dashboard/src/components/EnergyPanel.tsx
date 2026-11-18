import type { EnergyMetrics } from '../types'
import { formatWh } from '../format'

interface Props {
  daily: EnergyMetrics
  peak: EnergyMetrics
  peakActive: boolean
}

export function EnergyPanel({ daily, peak, peakActive }: Props) {
  const windowLabel = `${peak.stress_peak_start ?? '—'}–${peak.stress_peak_end ?? '—'}`

  return (
    <section className="energy-panel" aria-label="Energy totals">
      <div className="energy-panel__daily">
        <h2>Today</h2>
        <p className="energy-panel__figure tabular">{formatWh(daily.watt_hours)}</p>
        <p className="energy-panel__sub">
          {daily.date} · {daily.sample_count.toLocaleString()} readings
        </p>
      </div>
      <div className={`energy-panel__peak${peakActive ? ' is-active' : ''}`}>
        <div className="energy-panel__peak-head">
          <h2>Peak-stress window</h2>
          <span className={`energy-panel__state${peakActive ? ' is-on' : ''}`}>
            {peakActive ? 'Active now' : 'Outside window'}
          </span>
        </div>
        <p className="energy-panel__figure tabular">{formatWh(peak.watt_hours)}</p>
        <p className="energy-panel__sub">
          Energy used only during {windowLabel} local — the hours the grid is typically under highest
          demand. Totals stay at zero outside that window until the clock enters it.
        </p>
      </div>
    </section>
  )
}
