import { useMemo } from 'react'
import { DeviceTable } from './components/DeviceTable'
import { EnergyPanel } from './components/EnergyPanel'
import { PowerStrip } from './components/PowerStrip'
import { DashboardSkeleton } from './components/Skeleton'
import { useLiveSnapshot } from './hooks/useLiveSnapshot'
import './App.css'

function isPeakActive(start?: string | null, end?: string | null): boolean {
  if (!start || !end) return false
  const [sh, sm] = start.split(':').map(Number)
  const [eh, em] = end.split(':').map(Number)
  const now = new Date()
  const mins = now.getHours() * 60 + now.getMinutes()
  const a = sh * 60 + sm
  const b = eh * 60 + em
  if (b <= a) return mins >= a || mins < b
  return mins >= a && mins < b
}

export default function App() {
  const { snapshot, conn, error, refresh } = useLiveSnapshot()

  const peakActive = useMemo(
    () =>
      isPeakActive(
        snapshot?.peak_stress.stress_peak_start,
        snapshot?.peak_stress.stress_peak_end,
      ),
    [snapshot],
  )

  const connLabel =
    conn === 'live'
      ? 'Live'
      : conn === 'polling'
        ? 'Polling'
        : conn === 'connecting'
          ? 'Connecting'
          : 'Disconnected'

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar__brand">
          <p className="brand">Axceta</p>
          <p className="brand-sub">Local energy</p>
        </div>
        <p className={`conn conn--${conn}`} aria-live="polite">
          <span className="conn__dot" aria-hidden="true" />
          Local stack · {connLabel}
        </p>
      </header>

      <main className="main">
        {error && !snapshot ? (
          <div className="banner banner--error" role="alert">
            <p>
              Cannot reach the cloud API ({error}). Confirm Compose is up, then retry.
            </p>
            <button type="button" className="btn" onClick={() => void refresh()}>
              Retry connection
            </button>
          </div>
        ) : null}

        {snapshot ? (
          <>
            <PowerStrip
              totalWatts={snapshot.current.total_watts}
              online={snapshot.current.online_devices}
              offline={snapshot.current.offline_devices}
              peakActive={peakActive}
              shares={snapshot.current.by_device.map((d) => ({
                device_id: d.device_id,
                device_name: d.device_name,
                watts: d.watts,
                online: d.online,
              }))}
            />
            <EnergyPanel daily={snapshot.daily} peak={snapshot.peak_stress} peakActive={peakActive} />
            <DeviceTable devices={snapshot.devices} onChanged={() => void refresh()} />
          </>
        ) : error ? null : (
          <DashboardSkeleton />
        )}
      </main>
    </div>
  )
}
