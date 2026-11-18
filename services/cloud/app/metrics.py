"""
Energy metric formulas for the Axceta cloud dashboard.

Current consumption
    Sum of each online device's last_watts.

Daily / peak-stress consumption
    Trapezoidal integration of power over time, in watt-hours:

        Wh ≈ Σ  0.5 * (P_i + P_{i+1}) * Δt_hours

    Samples are first collapsed to a house-total series (sum watts per
    distinct timestamp bucket), then integrated. Peak-stress uses the same
    integral restricted to [STRESS_PEAK_START, STRESS_PEAK_END) on the
    requested calendar day (cloud local timezone).
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from datetime import time as dtime
from typing import Any
from zoneinfo import ZoneInfo

from .config import Settings
from .db import Database
from .models import CurrentMetrics, DeviceView, EnergyMetrics


def resolve_tz(tz_name: str):
    """Resolve a timezone name; UTC never requires the system zoneinfo database."""
    if tz_name.upper() in ("UTC", "GMT"):
        return timezone.utc
    return ZoneInfo(tz_name)


def parse_hhmm(value: str) -> dtime:
    hour, minute = value.split(":")
    return dtime(hour=int(hour), minute=int(minute))


def day_bounds(day: date, tz_name: str) -> tuple[float, float]:
    """Return [start, end) unix timestamps for a local calendar day."""
    tz = resolve_tz(tz_name)
    start = datetime.combine(day, dtime(0, 0), tzinfo=tz)
    end = start + timedelta(days=1)
    return start.timestamp(), end.timestamp()


def stress_bounds(
    day: date, start_hhmm: str, end_hhmm: str, tz_name: str
) -> tuple[float, float]:
    """Return [start, end) unix timestamps for the stress window on ``day``."""
    tz = resolve_tz(tz_name)
    start = datetime.combine(day, parse_hhmm(start_hhmm), tzinfo=tz)
    end = datetime.combine(day, parse_hhmm(end_hhmm), tzinfo=tz)
    if end <= start:
        # Window crosses midnight — treat end as next day.
        end = end + timedelta(days=1)
    return start.timestamp(), end.timestamp()


def trapezoidal_watt_hours(points: list[tuple[float, float]]) -> float:
    """
    Integrate a (timestamp, watts) series into watt-hours.

    Points must be sorted by timestamp ascending. Gaps larger than 5 minutes
    are not interpolated across (treat as a break to avoid inventing energy).
    """
    if len(points) < 2:
        return 0.0
    max_gap_s = 300.0
    total_wh = 0.0
    for i in range(len(points) - 1):
        t0, p0 = points[i]
        t1, p1 = points[i + 1]
        dt = t1 - t0
        if dt <= 0 or dt > max_gap_s:
            continue
        total_wh += 0.5 * (p0 + p1) * (dt / 3600.0)
    return total_wh


def house_series(samples: list[dict[str, Any]]) -> list[tuple[float, float]]:
    """
    Collapse per-device samples into a house-total power series.

    Samples that share the same second are summed (devices publish ~1 Hz).
    """
    buckets: dict[int, float] = defaultdict(float)
    for row in samples:
        bucket = int(row["ts"])
        buckets[bucket] += float(row["watts"])
    return sorted((float(ts), watts) for ts, watts in buckets.items())


def device_views(
    db: Database, settings: Settings, now: float | None = None
) -> list[DeviceView]:
    now = now if now is not None else time.time()
    views: list[DeviceView] = []
    for row in db.list_devices():
        online = (now - float(row["last_seen"])) <= settings.online_threshold_seconds
        views.append(
            DeviceView(
                device_id=row["device_id"],
                device_name=row["device_name"],
                device_type=row["device_type"],
                powered=bool(row["powered"]),
                online=online,
                last_seen=float(row["last_seen"]),
                last_watts=float(row["last_watts"]),
                last_amps=float(row["last_amps"]),
                last_voltage=float(row["last_voltage"]),
            )
        )
    return views


def current_metrics(db: Database, settings: Settings) -> CurrentMetrics:
    now = time.time()
    devices = device_views(db, settings, now=now)
    online = [d for d in devices if d.online]
    total = sum(d.last_watts for d in online)
    return CurrentMetrics(
        total_watts=round(total, 3),
        online_devices=len(online),
        offline_devices=len(devices) - len(online),
        by_device=[
            {
                "device_id": d.device_id,
                "device_name": d.device_name,
                "watts": d.last_watts,
                "online": d.online,
                "powered": d.powered,
            }
            for d in devices
        ],
        ts=now,
    )


def energy_for_window(
    db: Database,
    settings: Settings,
    *,
    day: date,
    window: str,
    tz_name: str = "UTC",
) -> EnergyMetrics:
    if window == "daily":
        start_ts, end_ts = day_bounds(day, tz_name)
        stress_start = stress_end = None
    elif window == "peak_stress":
        start_ts, end_ts = stress_bounds(
            day,
            settings.stress_peak_start,
            settings.stress_peak_end,
            tz_name,
        )
        stress_start = settings.stress_peak_start
        stress_end = settings.stress_peak_end
    else:
        raise ValueError(f"Unknown window: {window}")

    samples = db.samples_between(start_ts, end_ts)
    series = house_series(samples)
    wh = trapezoidal_watt_hours(series)
    return EnergyMetrics(
        window=window,  # type: ignore[arg-type]
        date=day.isoformat(),
        start_ts=start_ts,
        end_ts=end_ts,
        watt_hours=round(wh, 4),
        kilowatt_hours=round(wh / 1000.0, 6),
        sample_count=len(samples),
        stress_peak_start=stress_start,
        stress_peak_end=stress_end,
    )
