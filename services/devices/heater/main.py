"""Basement space heater — high continuous resistive load."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, "/app")

from _sdk.device import DeviceSimulator, configure_logging, env_float  # noqa: E402


class HeaterSimulator(DeviceSimulator):
    """Portable heater; default ~1.5 kW when powered."""

    def __init__(self) -> None:
        super().__init__(
            device_id=os.environ["DEVICE_ID"],
            device_name=os.getenv("DEVICE_NAME", "Heater"),
            device_type=os.getenv("DEVICE_TYPE", "heater"),
            mqtt_host=os.getenv("MQTT_HOST", "mosquitto"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        )
        self.nominal_watts = env_float("NOMINAL_WATTS", 1500.0)

    def compute_watts(self) -> float:
        return self.nominal_watts


def main() -> None:
    configure_logging()
    HeaterSimulator().run()


if __name__ == "__main__":
    main()
