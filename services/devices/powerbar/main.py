"""
Office powerbar simulator — sums N virtual outlet loads.

Control extras:
  set_outlets  { "action": "set_outlets", "watts": [25, 60, 5, 0] }
"""

from __future__ import annotations

import os
import sys
from typing import Any

sys.path.insert(0, "/app")

from _sdk.device import DeviceSimulator, configure_logging  # noqa: E402


def _parse_outlets(raw: str | None) -> list[float]:
    if not raw:
        return [25.0, 60.0, 5.0, 0.0]
    return [float(part.strip()) for part in raw.split(",") if part.strip() != ""]


class PowerbarSimulator(DeviceSimulator):
    """Multi-outlet strip; total draw is the sum of outlet wattages when powered."""

    def __init__(self) -> None:
        super().__init__(
            device_id=os.environ["DEVICE_ID"],
            device_name=os.getenv("DEVICE_NAME", "Powerbar"),
            device_type=os.getenv("DEVICE_TYPE", "powerbar"),
            mqtt_host=os.getenv("MQTT_HOST", "mosquitto"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        )
        self.outlets = _parse_outlets(os.getenv("OUTLET_WATTS"))
        self.register_handler("set_outlets", self._set_outlets)

    def _set_outlets(self, payload: dict[str, Any]) -> None:
        watts = payload.get("watts")
        if not isinstance(watts, list) or not watts:
            return
        self.outlets = [float(w) for w in watts]
        # Clear a prior set_watts override so outlet math applies again.
        self.target_watts = None

    def compute_watts(self) -> float:
        return float(sum(self.outlets))


def main() -> None:
    configure_logging()
    PowerbarSimulator().run()


if __name__ == "__main__":
    main()
