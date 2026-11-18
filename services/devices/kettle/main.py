"""Electric kettle — high boil load when powered (~1.8–2.2 kW)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, "/app")

from _sdk.device import DeviceSimulator, configure_logging, env_float  # noqa: E402


class KettleSimulator(DeviceSimulator):
    """Countertop kettle; starts powered off so operators must turn it on."""

    def __init__(self) -> None:
        super().__init__(
            device_id=os.environ["DEVICE_ID"],
            device_name=os.getenv("DEVICE_NAME", "Kettle"),
            device_type=os.getenv("DEVICE_TYPE", "kettle"),
            mqtt_host=os.getenv("MQTT_HOST", "mosquitto"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        )
        self.nominal_watts = env_float("NOMINAL_WATTS", 2000.0)
        # Demo default: kettle sits standby until the operator powers it.
        self.powered = os.getenv("START_POWERED", "false").lower() in ("1", "true", "yes")

    def compute_watts(self) -> float:
        return self.nominal_watts


def main() -> None:
    configure_logging()
    KettleSimulator().run()


if __name__ == "__main__":
    main()
