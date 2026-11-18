/** Display helpers for electrical quantities. */

export function formatWatts(w: number): string {
  if (w >= 1000) return `${(w / 1000).toFixed(2)} kW`
  return `${w.toFixed(1)} W`
}

export function formatWh(wh: number): string {
  if (wh >= 1000) return `${(wh / 1000).toFixed(3)} kWh`
  return `${wh.toFixed(1)} Wh`
}

export function formatAmps(a: number): string {
  return `${a.toFixed(3)} A`
}

export function relativeAge(ts: number, now = Date.now() / 1000): string {
  const age = Math.max(0, now - ts)
  if (age < 2) return 'just now'
  if (age < 60) return `${Math.floor(age)}s ago`
  return `${Math.floor(age / 60)}m ago`
}
