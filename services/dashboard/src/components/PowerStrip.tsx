/**
 * Signature reading: a continuous load rail with per-device segments
 * so operators see both house total and who is drawing.
 */

import { formatWatts } from '../format'

/** Display scale for the rail; house totals with heater/kettle can exceed 2 kW. */
const DISPLAY_CAP_W = 2500

export interface StripShare {
  device_id: string
  device_name: string
  watts: number
  online: boolean
}

interface Props {
  totalWatts: number
  online: number
  offline: number
  peakActive: boolean
  shares: StripShare[]
}

const SEGMENT_TONES = ['var(--live-deep)', 'var(--live)', '#2a9d8f', '#1b6b63']

export function PowerStrip({ totalWatts, online, offline, peakActive, shares }: Props) {
  const active = shares.filter((s) => s.online && s.watts > 0)

  return (
    <section className="power-strip" aria-labelledby="power-heading">
      <div className="power-strip__meta">
        <h2 id="power-heading">House load</h2>
        <p className="power-strip__hint">
          <span className="power-strip__hint-stat">
            {online} online{offline > 0 ? ` · ${offline} offline` : ''}
          </span>
          {peakActive ? <span className="power-strip__peak-tag">Stress window</span> : null}
        </p>
      </div>

      <div className="power-strip__readout">
        <p className="power-strip__value" aria-live="polite">
          <span className="power-strip__number tabular">{formatWatts(totalWatts)}</span>
          <span className="power-strip__unit">drawing now</span>
        </p>
        {active.length > 0 ? (
          <ul className="power-strip__legend">
            {active.map((s, i) => (
              <li key={s.device_id}>
                <span
                  className="power-strip__swatch"
                  style={{ background: SEGMENT_TONES[i % SEGMENT_TONES.length] }}
                  aria-hidden="true"
                />
                <span className="power-strip__legend-name">{s.device_name}</span>
                <span className="tabular">{formatWatts(s.watts)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="power-strip__idle">No draw from online devices</p>
        )}
      </div>

      <div
        className="power-strip__rail"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={DISPLAY_CAP_W}
        aria-valuenow={Math.round(totalWatts)}
        aria-label="Current house power"
      >
        <div className="power-strip__segments">
          {active.map((s, i) => {
            const width = Math.min(100, (s.watts / DISPLAY_CAP_W) * 100)
            return (
              <div
                key={s.device_id}
                className="power-strip__segment"
                style={{
                  width: `${width}%`,
                  background: SEGMENT_TONES[i % SEGMENT_TONES.length],
                }}
                title={`${s.device_name}: ${formatWatts(s.watts)}`}
              />
            )
          })}
        </div>
        <div className="power-strip__ticks" aria-hidden="true">
          <span>0</span>
          <span>1.25 kW</span>
          <span>2.5 kW</span>
        </div>
      </div>
    </section>
  )
}
