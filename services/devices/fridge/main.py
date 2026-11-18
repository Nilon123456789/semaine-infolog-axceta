"""
Kitchen fridge — compressor cycles between idle and run loads.

CYCLE_SECONDS controls the full period; roughly half is compressor-on.
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, "/app")

from _sdk.device import DeviceSimulator, configure_logging, env_float  # noqa: E402


class FridgeSimulator(DeviceSimulator):
    """Refrigerator with a simple duty-cycle compressor model."""

    def __init__(self) -> None:
        super().__init__(
            device_id=os.environ["DEVICE_ID"],
            device_name=os.getenv("DEVICE_NAME", "Fridge"),
            device_type=os.getenv("DEVICE_TYPE", "fridge"),
            mqtt_host=os.getenv("MQTT_HOST", "mosquitto"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        )
        self.run_watts = env_float("RUN_WATTS", 120.0)
        self.idle_watts = env_float("IDLE_WATTS", 8.0)
        self.cycle_seconds = env_float("CYCLE_SECONDS", 40.0)
        self._started = time.time()

    def compute_watts(self) -> float:
        elapsed = (time.time() - self._started) % self.cycle_seconds
        # Compressor on for the first 45% of each cycle.
        if elapsed < self.cycle_seconds * 0.45:
            return self.run_watts
        return self.idle_watts


def main() -> None:
    configure_logging()
    FridgeSimulator().run()


if __name__ == "__main__":
    main()
