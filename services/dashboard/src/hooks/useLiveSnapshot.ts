/**
 * Live snapshot hook: WebSocket primary, REST poll fallback.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { cloudWsUrl, fetchSnapshot } from '../api'
import type { Snapshot } from '../types'

export type ConnState = 'connecting' | 'live' | 'polling' | 'error'

export function useLiveSnapshot() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [conn, setConn] = useState<ConnState>('connecting')
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await fetchSnapshot()
      setSnapshot(data)
      setError(null)
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load snapshot')
      return false
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    let pollTimer: number | undefined
    let retryTimer: number | undefined

    const startPoll = () => {
      setConn('polling')
      void refresh()
      pollTimer = window.setInterval(() => {
        void refresh()
      }, 2000)
    }

    const connectWs = () => {
      setConn('connecting')
      const ws = new WebSocket(cloudWsUrl())
      wsRef.current = ws

      ws.onopen = () => {
        if (cancelled) return
        setConn('live')
        setError(null)
      }

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data as string) as Snapshot
          setSnapshot(data)
          setError(null)
        } catch {
          /* ignore malformed frames */
        }
      }

      ws.onerror = () => {
        /* onclose handles recovery */
      }

      ws.onclose = () => {
        if (cancelled) return
        wsRef.current = null
        startPoll()
        retryTimer = window.setTimeout(connectWs, 5000)
      }
    }

    void refresh().then((ok) => {
      if (!cancelled && ok) connectWs()
      else if (!cancelled) {
        setConn('error')
        startPoll()
        retryTimer = window.setTimeout(connectWs, 5000)
      }
    })

    return () => {
      cancelled = true
      if (pollTimer) window.clearInterval(pollTimer)
      if (retryTimer) window.clearTimeout(retryTimer)
      wsRef.current?.close()
    }
  }, [refresh])

  return { snapshot, conn, error, refresh }
}
