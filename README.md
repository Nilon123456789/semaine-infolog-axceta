# Axceta Local Energy Dashboard

Local-first home electrical consumption demo for the Axceta challenge: Docker-simulated IoT meters, a local MQTT + FastAPI “cloud,” and an English React dashboard with live controls.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open **http://localhost:5173** (dashboard) and **http://localhost:8000/docs** (cloud API).

Default devices:

| Service | ID | Nominal load |
|---|---|---|
| `lamp` | `lamp-living-room` | ~40 W |
| `powerbar` | `powerbar-office` | sum of outlets (25+60+5+0 W) |
| `heater` | `heater-basement` | ~1500 W |
| `fridge` | `fridge-kitchen` | cycles ~8–120 W |
| `kettle` | `kettle-kitchen` | ~2000 W (starts standby) |

## What you get

- **Current consumption** — sum of online device watts (power strip on the dashboard)
- **Daily total** — Wh / kWh integrated over today
- **Peak-stress window** — same integral for `STRESS_PEAK_START`–`STRESS_PEAK_END` (default 16:00–20:00, `TZ`)
- Device connectivity, live readings, On / Off / load override / powerbar outlets
- Documented path to add new device containers

## Development

### Cloud (Python)

```bash
cd services/cloud
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
ruff check app tests
uvicorn app.main:app --reload --port 8000
```

### Dashboard (React)

```bash
cd services/dashboard
npm install
npm run dev          # http://localhost:5173 — proxies /api and /ws to :8000
npm run build
```

Requires the cloud + Mosquitto running (Compose or local).

## Challenge criteria checklist

| Criterion | Where |
|---|---|
| Measured metrics present | Dashboard + `/metrics/*` |
| Simple dashboard UI | Operate-mode React UI |
| Easy simulator use | On / Off / load override / outlets on each device card |
| Adding devices | [docs/DEVICE_PLUGIN.md](docs/DEVICE_PLUGIN.md) |
| CI/CD | [.github/workflows/ci.yml](.github/workflows/ci.yml) |

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Device plugin guide](docs/DEVICE_PLUGIN.md)
- [Product context](PRODUCT.md)
- [Design system](DESIGN.md)

## Configuration

See [.env.example](.env.example). Important knobs: `STRESS_PEAK_START` / `STRESS_PEAK_END`, `ONLINE_THRESHOLD_SECONDS`, `TZ`.
