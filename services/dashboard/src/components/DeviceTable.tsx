import { useEffect, useState } from 'react'
import { sendControl } from '../api'
import { formatAmps, formatWatts, relativeAge } from '../format'
import type { ControlAction, DeviceView } from '../types'

interface Props {
  devices: DeviceView[]
  onChanged: () => void
}

type Feedback = { kind: 'ok' | 'err'; text: string }

const DEFAULT_OUTLETS = [25, 60, 5, 0]
const MAX_WATTS = 5000

function statusLabel(d: DeviceView): string {
  if (!d.online) return 'Offline'
  return d.powered ? 'Online · powered' : 'Online · standby'
}

export function DeviceTable({ devices, onChanged }: Props) {
  const [busy, setBusy] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<Record<string, Feedback>>({})
  const [draftWatts, setDraftWatts] = useState<Record<string, string>>({})
  const [outlets, setOutlets] = useState<Record<string, number[]>>({})

  useEffect(() => {
    setOutlets((prev) => {
      const next = { ...prev }
      for (const d of devices) {
        if (d.device_type === 'powerbar' && !next[d.device_id]) {
          next[d.device_id] = [...DEFAULT_OUTLETS]
        }
      }
      return next
    })
  }, [devices])

  async function run(
    device: DeviceView,
    action: ControlAction,
    watts?: number | number[],
    successText?: string,
  ) {
    const deviceId = device.device_id
    setBusy(deviceId)
    setFeedback((f) => {
      const copy = { ...f }
      delete copy[deviceId]
      return copy
    })
    try {
      await sendControl(deviceId, action, watts)
      const text =
        successText ??
        (action === 'power_on'
          ? `${device.device_name} → powered on`
          : action === 'power_off'
            ? `${device.device_name} → standby`
            : `${device.device_name} updated`)
      setFeedback((f) => ({ ...f, [deviceId]: { kind: 'ok', text } }))
      onChanged()
      window.setTimeout(() => {
        setFeedback((f) => {
          if (f[deviceId]?.kind !== 'ok') return f
          const copy = { ...f }
          delete copy[deviceId]
          return copy
        })
      }, 3200)
    } catch (e) {
      setFeedback((f) => ({
        ...f,
        [deviceId]: {
          kind: 'err',
          text:
            e instanceof Error
              ? e.message
              : 'Control failed — check MQTT and try again',
        },
      }))
    } finally {
      setBusy(null)
    }
  }

  if (devices.length === 0) {
    return (
      <section className="device-table" aria-labelledby="devices-heading">
        <h2 id="devices-heading">Devices</h2>
        <p className="device-table__empty">
          No meters have checked in yet. With Compose running, devices should appear within a couple of
          seconds. If this stays empty, confirm the broker and device containers are up.
        </p>
      </section>
    )
  }

  return (
    <section className="device-table" aria-labelledby="devices-heading">
      <div className="device-table__head">
        <h2 id="devices-heading">Devices</h2>
        <p className="device-table__help">
          Switch power, set a load override, or edit powerbar outlet watts.
        </p>
      </div>

      <ul className="device-list">
        {devices.map((d) => {
          const isBusy = busy === d.device_id
          const fb = feedback[d.device_id]
          const outletVals = outlets[d.device_id] ?? DEFAULT_OUTLETS
          const isPowerbar = d.device_type === 'powerbar'

          return (
            <li
              key={d.device_id}
              className={[
                'device-card',
                !d.online ? 'is-offline' : '',
                fb?.kind === 'ok' ? 'is-ok' : '',
                fb?.kind === 'err' ? 'is-err' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <div className="device-card__top">
                <div>
                  <p className="device-card__name">{d.device_name}</p>
                  <p className="device-card__id">
                    {d.device_type} · {d.device_id}
                  </p>
                </div>
                <div className="device-card__meta">
                  <span
                    className={`pill ${d.online ? (d.powered ? 'pill--powered' : 'pill--ok') : 'pill--off'}`}
                  >
                    {statusLabel(d)}
                  </span>
                  <p className="device-card__draw tabular">
                    <span className="device-card__watts">{formatWatts(d.last_watts)}</span>
                    <span className="device-card__amps">{formatAmps(d.last_amps)}</span>
                  </p>
                  <p className="device-card__seen">Seen {relativeAge(d.last_seen)}</p>
                </div>
              </div>

              <div className="device-card__controls">
                <div className="power-toggle" role="group" aria-label={`Power for ${d.device_name}`}>
                  <button
                    type="button"
                    className={`power-toggle__btn${d.powered ? ' is-selected' : ''}`}
                    disabled={isBusy || !d.online || d.powered}
                    aria-pressed={d.powered}
                    onClick={() => void run(d, 'power_on')}
                  >
                    On
                  </button>
                  <button
                    type="button"
                    className={`power-toggle__btn${!d.powered ? ' is-selected is-off' : ''}`}
                    disabled={isBusy || !d.online || !d.powered}
                    aria-pressed={!d.powered}
                    onClick={() => void run(d, 'power_off')}
                  >
                    Off
                  </button>
                </div>

                <form
                  className="load-form"
                  onSubmit={(e) => {
                    e.preventDefault()
                    const w = Number(draftWatts[d.device_id])
                    if (!Number.isFinite(w) || w < 0 || w > MAX_WATTS) {
                      setFeedback((f) => ({
                        ...f,
                        [d.device_id]: {
                          kind: 'err',
                          text: `Enter a load between 0 and ${MAX_WATTS} W`,
                        },
                      }))
                      return
                    }
                    void run(d, 'set_watts', w, `${d.device_name} → ${formatWatts(w)} override`)
                  }}
                >
                  <label className="load-form__label" htmlFor={`watts-${d.device_id}`}>
                    Load override (W)
                  </label>
                  <input
                    id={`watts-${d.device_id}`}
                    type="number"
                    min={0}
                    max={MAX_WATTS}
                    step={1}
                    inputMode="decimal"
                    placeholder={String(Math.round(d.last_watts))}
                    value={draftWatts[d.device_id] ?? ''}
                    onChange={(e) =>
                      setDraftWatts((prev) => ({ ...prev, [d.device_id]: e.target.value }))
                    }
                    disabled={isBusy || !d.online}
                  />
                  <button
                    type="submit"
                    className="btn"
                    disabled={isBusy || !d.online || !draftWatts[d.device_id]}
                  >
                    {isBusy ? 'Sending…' : 'Apply'}
                  </button>
                </form>
              </div>

              {isPowerbar ? (
                <form
                  className="outlet-form"
                  onSubmit={(e) => {
                    e.preventDefault()
                    const clean = outletVals.map((n) => Math.max(0, Math.min(MAX_WATTS, Number(n) || 0)))
                    void run(
                      d,
                      'set_outlets',
                      clean,
                      `${d.device_name} outlets → ${clean.join(' + ')} W`,
                    )
                  }}
                >
                  <p className="outlet-form__title">Outlets (W each)</p>
                  <div className="outlet-form__row">
                    {outletVals.map((val, i) => (
                      <label key={i} className="outlet-form__cell">
                        <span>#{i + 1}</span>
                        <input
                          type="number"
                          min={0}
                          max={MAX_WATTS}
                          step={1}
                          value={val}
                          disabled={isBusy || !d.online}
                          onChange={(e) => {
                            const n = Number(e.target.value)
                            setOutlets((prev) => {
                              const list = [...(prev[d.device_id] ?? DEFAULT_OUTLETS)]
                              list[i] = Number.isFinite(n) ? n : 0
                              return { ...prev, [d.device_id]: list }
                            })
                          }}
                        />
                      </label>
                    ))}
                    <button type="submit" className="btn" disabled={isBusy || !d.online}>
                      {isBusy ? 'Sending…' : 'Apply outlets'}
                    </button>
                  </div>
                </form>
              ) : null}

              <p
                className={`device-card__feedback${fb ? ` is-${fb.kind}` : ''}`}
                aria-live="polite"
                role={fb?.kind === 'err' ? 'alert' : undefined}
              >
                {fb ? fb.text : '\u00a0'}
              </p>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
