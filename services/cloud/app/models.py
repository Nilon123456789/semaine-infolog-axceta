"""Pydantic request/response models for the cloud HTTP API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    mqtt_connected: bool
    device_count: int


class DeviceView(BaseModel):
    device_id: str
    device_name: str
    device_type: str
    powered: bool
    online: bool
    last_seen: float
    last_watts: float
    last_amps: float
    last_voltage: float


class CurrentMetrics(BaseModel):
    """Instantaneous house load: sum of latest watts for online devices."""

    total_watts: float
    online_devices: int
    offline_devices: int
    by_device: list[dict[str, Any]]
    ts: float


class EnergyMetrics(BaseModel):
    """Integrated energy over a time window (Wh and kWh)."""

    window: Literal["daily", "peak_stress"]
    date: str
    start_ts: float
    end_ts: float
    watt_hours: float
    kilowatt_hours: float
    sample_count: int
    stress_peak_start: str | None = None
    stress_peak_end: str | None = None


class ControlRequest(BaseModel):
    action: Literal["power_on", "power_off", "set_watts", "set_outlets"]
    watts: float | list[float] | None = Field(
        default=None,
        description="Required for set_watts (float) or set_outlets (list).",
    )


class ControlResponse(BaseModel):
    device_id: str
    action: str
    published: bool
    detail: str = "ok"


class Snapshot(BaseModel):
    """WebSocket push payload with devices + headline metrics."""

    type: str = "snapshot"
    devices: list[DeviceView]
    current: CurrentMetrics
    daily: EnergyMetrics
    peak_stress: EnergyMetrics
