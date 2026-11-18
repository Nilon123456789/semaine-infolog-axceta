# Architecture

## Overview

Local-first stack for the Axceta electrical-consumption challenge:

1. **Device simulators** (Docker) measure synthetic current and publish MQTT telemetry.
2. **Mosquitto** brokers telemetry and control messages.
3. **Cloud API** (FastAPI) ingests samples into SQLite, computes metrics, exposes REST + WebSocket.
4. **Dashboard** (React) is the local application that reads cloud data and sends device controls.

```
lamp / powerbar  --telemetry-->  Mosquitto  -->  Cloud (ingest)
dashboard  --REST/WS-->  Cloud
dashboard  --control-->  Cloud  --MQTT-->  devices
```

## Topics

| Topic | Direction | Payload |
|---|---|---|
| `devices/{id}/telemetry` | device → cloud | watts, amps, voltage, powered, ts, names |
| `devices/{id}/control` | cloud → device | `{ "action": "power_on" \| "power_off" \| "set_watts" \| "set_outlets", ... }` |
| `devices/{id}/status` | device → cloud | online/powered snapshot |

## Metrics

Formulas live in `services/cloud/app/metrics.py` and are covered by unit tests.

- **Current:** sum of `last_watts` for devices seen within `ONLINE_THRESHOLD_SECONDS`.
- **Daily / peak-stress:** trapezoidal integration of house-total watts over time → Wh (and kWh). Peak-stress uses `STRESS_PEAK_START`–`STRESS_PEAK_END` on the cloud local calendar day (`TZ`).

## Persistence

SQLite file at `DATABASE_PATH` (Compose volume `cloud-data`). Tables: `devices`, `samples`.

## Extending devices

See [DEVICE_PLUGIN.md](DEVICE_PLUGIN.md).
