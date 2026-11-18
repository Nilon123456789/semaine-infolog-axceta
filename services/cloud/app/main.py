"""
Axceta cloud HTTP + WebSocket API.

Exposes device registry, control, and the three required consumption metrics
for the local dashboard.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .db import Database
from .hub import SnapshotHub
from .ingest import MqttIngest
from .metrics import current_metrics, device_views, energy_for_window, resolve_tz
from .models import (
    ControlRequest,
    ControlResponse,
    CurrentMetrics,
    DeviceView,
    EnergyMetrics,
    HealthResponse,
    Snapshot,
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("axceta.cloud")


def _local_tz(settings: Settings) -> str:
    return os.getenv("TZ", "UTC")


def _parse_day(raw: str | None, tz_name: str) -> date:
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(resolve_tz(tz_name)).date()


class AppState:
    def __init__(self) -> None:
        self.settings: Settings = get_settings()
        self.db = Database(self.settings.database_path)
        self.hub = SnapshotHub()
        self.ingest: MqttIngest | None = None
        self._dirty = asyncio.Event()
        self._loop: asyncio.AbstractEventLoop | None = None

    def mark_dirty(self) -> None:
        """Called from the MQTT thread when new telemetry arrives."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._dirty.set)


state = AppState()


def build_snapshot() -> Snapshot:
    settings = state.settings
    tz = _local_tz(settings)
    today = _parse_day(None, tz)
    return Snapshot(
        devices=device_views(state.db, settings),
        current=current_metrics(state.db, settings),
        daily=energy_for_window(
            state.db, settings, day=today, window="daily", tz_name=tz
        ),
        peak_stress=energy_for_window(
            state.db, settings, day=today, window="peak_stress", tz_name=tz
        ),
    )


async def _broadcast_loop() -> None:
    """Debounced broadcaster: wake on dirty flag, push at most ~2 Hz."""
    while True:
        await state._dirty.wait()
        state._dirty.clear()
        try:
            snap = build_snapshot()
            await state.hub.broadcast(snap.model_dump())
        except Exception:
            logger.exception("Failed to broadcast snapshot")
        await asyncio.sleep(0.5)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    state._loop = asyncio.get_running_loop()
    ingest = MqttIngest(
        host=state.settings.mqtt_host,
        port=state.settings.mqtt_port,
        db=state.db,
        on_change=state.mark_dirty,
    )
    state.ingest = ingest
    ingest.start()
    task = asyncio.create_task(_broadcast_loop())
    logger.info(
        "Cloud up — stress window %s–%s, online threshold %.1fs",
        state.settings.stress_peak_start,
        state.settings.stress_peak_end,
        state.settings.online_threshold_seconds,
    )
    yield
    task.cancel()
    ingest.stop()


app = FastAPI(
    title="Axceta Cloud",
    description="Local-first electrical consumption cloud for the Axceta challenge.",
    version="1.0.0",
    lifespan=lifespan,
)

# Local-first demo: browsers reject Access-Control-Allow-Origin: * when
# credentials are enabled, so keep credentials off and allow any localhost origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    mqtt_ok = bool(state.ingest and state.ingest.connected)
    return HealthResponse(
        status="ok",
        mqtt_connected=mqtt_ok,
        device_count=len(state.db.list_devices()),
    )


@app.get("/devices", response_model=list[DeviceView])
def list_devices() -> list[DeviceView]:
    return device_views(state.db, state.settings)


@app.get("/devices/{device_id}", response_model=DeviceView)
def get_device(device_id: str) -> DeviceView:
    for d in device_views(state.db, state.settings):
        if d.device_id == device_id:
            return d
    raise HTTPException(status_code=404, detail="Device not found")


@app.post("/devices/{device_id}/control", response_model=ControlResponse)
def control_device(device_id: str, body: ControlRequest) -> ControlResponse:
    if state.ingest is None:
        raise HTTPException(status_code=503, detail="MQTT ingest not ready")

    payload: dict = {"action": body.action}
    if body.action == "set_watts":
        if body.watts is None or isinstance(body.watts, list):
            raise HTTPException(status_code=400, detail="set_watts requires a numeric watts")
        payload["watts"] = float(body.watts)
    elif body.action == "set_outlets":
        if not isinstance(body.watts, list):
            raise HTTPException(status_code=400, detail="set_outlets requires watts as a list")
        payload["watts"] = [float(w) for w in body.watts]

    published = state.ingest.publish_control(device_id, payload)
    if not published:
        raise HTTPException(status_code=503, detail="MQTT not connected")
    state.mark_dirty()
    return ControlResponse(device_id=device_id, action=body.action, published=True)


@app.get("/metrics/current", response_model=CurrentMetrics)
def metrics_current() -> CurrentMetrics:
    return current_metrics(state.db, state.settings)


@app.get("/metrics/daily", response_model=EnergyMetrics)
def metrics_daily(date: str | None = None) -> EnergyMetrics:
    tz = _local_tz(state.settings)
    day = _parse_day(date, tz)
    return energy_for_window(
        state.db, state.settings, day=day, window="daily", tz_name=tz
    )


@app.get("/metrics/peak-stress", response_model=EnergyMetrics)
def metrics_peak_stress(date: str | None = None) -> EnergyMetrics:
    tz = _local_tz(state.settings)
    day = _parse_day(date, tz)
    return energy_for_window(
        state.db, state.settings, day=day, window="peak_stress", tz_name=tz
    )


@app.get("/snapshot", response_model=Snapshot)
def snapshot() -> Snapshot:
    return build_snapshot()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await state.hub.connect(ws)
    try:
        # Send an immediate snapshot so the UI is not blank until next sample.
        await ws.send_json(build_snapshot().model_dump())
        while True:
            # Keep the socket open; clients may send pings as plain text.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await state.hub.disconnect(ws)
