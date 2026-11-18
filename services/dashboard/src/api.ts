/**
 * Cloud API client for the local dashboard.
 *
 * In Docker the browser talks to the host-mapped cloud URL (VITE_CLOUD_URL).
 * In Vite dev, relative /api and /ws are proxied to localhost:8000.
 */

import type { ControlAction, Snapshot } from './types'

const CLOUD_URL = (import.meta.env.VITE_CLOUD_URL as string | undefined)?.replace(/\/$/, '') ?? ''

export function cloudHttpBase(): string {
  return CLOUD_URL || ''
}

export function cloudWsUrl(): string {
  if (CLOUD_URL) {
    const u = new URL(CLOUD_URL)
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    u.pathname = '/ws'
    return u.toString()
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws`
}

function httpPath(path: string): string {
  if (CLOUD_URL) return `${CLOUD_URL}${path}`
  return `/api${path}`
}

export async function fetchSnapshot(): Promise<Snapshot> {
  const res = await fetch(httpPath('/snapshot'))
  if (!res.ok) throw new Error(`Snapshot failed (${res.status})`)
  return res.json() as Promise<Snapshot>
}

export async function sendControl(
  deviceId: string,
  action: ControlAction,
  watts?: number | number[],
): Promise<void> {
  const body: Record<string, unknown> = { action }
  if (watts !== undefined) body.watts = watts
  const res = await fetch(httpPath(`/devices/${encodeURIComponent(deviceId)}/control`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `Control failed (${res.status})`)
  }
}
