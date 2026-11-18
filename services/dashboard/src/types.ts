/** Types mirrored from the Axceta cloud API snapshot contract. */

export interface DeviceView {
  device_id: string
  device_name: string
  device_type: string
  powered: boolean
  online: boolean
  last_seen: number
  last_watts: number
  last_amps: number
  last_voltage: number
}

export interface CurrentMetrics {
  total_watts: number
  online_devices: number
  offline_devices: number
  by_device: Array<{
    device_id: string
    device_name: string
    watts: number
    online: boolean
    powered: boolean
  }>
  ts: number
}

export interface EnergyMetrics {
  window: 'daily' | 'peak_stress'
  date: string
  start_ts: number
  end_ts: number
  watt_hours: number
  kilowatt_hours: number
  sample_count: number
  stress_peak_start?: string | null
  stress_peak_end?: string | null
}

export interface Snapshot {
  type?: string
  devices: DeviceView[]
  current: CurrentMetrics
  daily: EnergyMetrics
  peak_stress: EnergyMetrics
}

export type ControlAction = 'power_on' | 'power_off' | 'set_watts' | 'set_outlets'
