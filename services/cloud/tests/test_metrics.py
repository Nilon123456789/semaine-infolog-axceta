"""Unit tests for energy integration math (no MQTT required)."""

from __future__ import annotations

from datetime import date

from app.metrics import (
    house_series,
    parse_hhmm,
    stress_bounds,
    trapezoidal_watt_hours,
)


def test_trapezoidal_constant_100w_one_hour() -> None:
    # 100 W sampled every 60s for 1 hour (within the 5-minute gap limit) → 100 Wh
    points = [(float(t), 100.0) for t in range(0, 3601, 60)]
    assert abs(trapezoidal_watt_hours(points) - 100.0) < 1e-6


def test_trapezoidal_skips_large_gaps() -> None:
    points = [(0.0, 100.0), (10.0, 100.0), (400.0, 100.0)]
    # Only the 10s segment counts (100 W * 10/3600 h ≈ 0.2778 Wh)
    wh = trapezoidal_watt_hours(points)
    assert abs(wh - (100.0 * 10 / 3600)) < 1e-6


def test_house_series_sums_same_second() -> None:
    samples = [
        {"ts": 100.2, "watts": 40.0},
        {"ts": 100.8, "watts": 60.0},
        {"ts": 101.0, "watts": 10.0},
    ]
    series = house_series(samples)
    assert series == [(100.0, 100.0), (101.0, 10.0)]


def test_parse_hhmm() -> None:
    t = parse_hhmm("16:00")
    assert t.hour == 16 and t.minute == 0


def test_stress_bounds_same_day() -> None:
    start, end = stress_bounds(date(2026, 11, 18), "16:00", "20:00", "UTC")
    assert end - start == 4 * 3600
