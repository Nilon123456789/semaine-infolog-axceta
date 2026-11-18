/**
 * Lightweight formatter checks (no test runner required).
 * Keep in sync with src/format.ts.
 */

function formatWatts(w) {
  if (w >= 1000) return `${(w / 1000).toFixed(2)} kW`
  return `${w.toFixed(1)} W`
}

function formatWh(wh) {
  if (wh >= 1000) return `${(wh / 1000).toFixed(3)} kWh`
  return `${wh.toFixed(1)} Wh`
}

function formatAmps(a) {
  return `${a.toFixed(3)} A`
}

function relativeAge(ts, now = Date.now() / 1000) {
  const age = Math.max(0, now - ts)
  if (age < 2) return 'just now'
  if (age < 60) return `${Math.floor(age)}s ago`
  return `${Math.floor(age / 60)}m ago`
}

function assertEqual(actual, expected) {
  if (actual !== expected) {
    throw new Error(`Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`)
  }
}

assertEqual(formatWatts(40), '40.0 W')
assertEqual(formatWatts(1500), '1.50 kW')
assertEqual(formatWh(250), '250.0 Wh')
assertEqual(formatWh(2500), '2.500 kWh')
assertEqual(formatAmps(0.3333), '0.333 A')
assertEqual(relativeAge(100, 100.5), 'just now')
assertEqual(relativeAge(100, 130), '30s ago')

console.log('format.test.mjs OK')
