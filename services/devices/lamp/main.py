"""Living-room lamp simulator — single resistive load (~5–60 W)."""

from __future__ import annotations

import os
import sys

# Allow importing the shared SDK when running from /app in the container.
sys.path.insert(0, "/app")

from _sdk.device import DeviceSimulator, configure_logging, env_float  # noqa: E402


class LampSimulator(DeviceSimulator):
    """Incandescent/LED lamp with a configurable nominal wattage."""

    def __init__(self) -> None:
        super().__init__(
            device_id=os.environ["DEVICE_ID"],
            device_name=os.getenv("DEVICE_NAME", "Lamp"),
            device_type=os.getenv("DEVICE_TYPE", "lamp"),
            mqtt_host=os.getenv("MQTT_HOST", "mosquitto"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        )
        self.nominal_watts = env_float("NOMINAL_WATTS", 40.0)

    def compute_watts(self) -> float:
        return self.nominal_watts


def main() -> None:
    configure_logging()
    LampSimulator().run()


if __name__ == "__main__":
    main()
