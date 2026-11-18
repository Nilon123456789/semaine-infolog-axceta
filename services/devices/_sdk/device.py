"""
MQTT device simulator base.

Each container publishes telemetry at ~1 Hz and listens for control commands.
Topic contract (stable for the cloud ingest layer):

  devices/{device_id}/telemetry  JSON TelemetrySample
  devices/{device_id}/control    JSON { "action": "...", ... }
  devices/{device_id}/status     JSON { "online": true, "powered": bool, ... }
"""

from __future__ import annotations

import json
import logging
import os
import random
import signal
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger("axceta.device")


@dataclass
class TelemetrySample:
    """One instantaneous electrical reading from a simulated meter."""

    device_id: str
    device_name: str
    device_type: str
    watts: float
    amps: float
    voltage: float
    powered: bool
    ts: float

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class DeviceSimulator:
    """
    Long-running MQTT client that simulates a household appliance meter.

    Subclasses implement ``compute_watts()`` to define load behaviour.
    Control actions: ``power_on``, ``power_off``, ``set_watts``, ``set_outlets``.
    """

    VOLTAGE = 120.0  # North-American nominal line voltage for the demo.

    def __init__(
        self,
        device_id: str,
        device_name: str,
        device_type: str,
        mqtt_host: str = "mosquitto",
        mqtt_port: int = 1883,
        publish_interval_s: float = 1.0,
        noise_ratio: float = 0.02,
    ) -> None:
        self.device_id = device_id
        self.device_name = device_name
        self.device_type = device_type
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.publish_interval_s = publish_interval_s
        self.noise_ratio = noise_ratio

        self.powered = True
        self.target_watts: float | None = None
        self._stop = threading.Event()
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"axceta-{device_id}",
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._extra_handlers: dict[str, Callable[[dict[str, Any]], None]] = {}

    # --- hooks for device-specific behaviour ---------------------------------

    def compute_watts(self) -> float:
        """Return the instantaneous load in watts when powered on."""
        raise NotImplementedError

    def register_handler(
        self, action: str, handler: Callable[[dict[str, Any]], None]
    ) -> None:
        """Register an extra control action beyond the built-in set."""
        self._extra_handlers[action] = handler

    # --- MQTT lifecycle ------------------------------------------------------

    def _telemetry_topic(self) -> str:
        return f"devices/{self.device_id}/telemetry"

    def _control_topic(self) -> str:
        return f"devices/{self.device_id}/control"

    def _status_topic(self) -> str:
        return f"devices/{self.device_id}/status"

    def _on_connect(
        self,
        client: mqtt.Client,
        _userdata: Any,
        _flags: Any,
        reason_code: mqtt.ReasonCode,
        _properties: Any = None,
    ) -> None:
        if reason_code.is_failure:
            logger.error("MQTT connect failed: %s", reason_code)
            return
        client.subscribe(self._control_topic())
        self._publish_status()
        logger.info(
            "Connected as %s (%s); subscribed to %s",
            self.device_id,
            self.device_type,
            self._control_topic(),
        )

    def _on_message(
        self, _client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("Invalid control payload: %s", exc)
            return
        action = payload.get("action")
        if action == "power_on":
            self.powered = True
        elif action == "power_off":
            self.powered = False
        elif action == "set_watts":
            try:
                self.target_watts = float(payload["watts"])
            except (KeyError, TypeError, ValueError):
                logger.warning("set_watts missing valid watts: %s", payload)
                return
        elif action in self._extra_handlers:
            self._extra_handlers[action](payload)
        else:
            logger.warning("Unknown control action: %s", action)
            return
        self._publish_status()
        logger.info("Applied control %s → powered=%s target=%s", action, self.powered, self.target_watts)

    def _publish_status(self) -> None:
        body = {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "online": True,
            "powered": self.powered,
            "target_watts": self.target_watts,
            "ts": time.time(),
        }
        self._client.publish(self._status_topic(), json.dumps(body), qos=1)

    def _apply_noise(self, watts: float) -> float:
        if watts <= 0:
            return 0.0
        jitter = 1.0 + random.uniform(-self.noise_ratio, self.noise_ratio)
        return max(0.0, watts * jitter)

    def _sample(self) -> TelemetrySample:
        raw = self.compute_watts() if self.powered else 0.0
        if self.powered and self.target_watts is not None:
            raw = self.target_watts
        watts = self._apply_noise(raw)
        amps = watts / self.VOLTAGE if self.VOLTAGE else 0.0
        return TelemetrySample(
            device_id=self.device_id,
            device_name=self.device_name,
            device_type=self.device_type,
            watts=round(watts, 3),
            amps=round(amps, 4),
            voltage=self.VOLTAGE,
            powered=self.powered,
            ts=time.time(),
        )

    def run(self) -> None:
        """Block until SIGTERM/SIGINT, publishing telemetry on an interval."""

        def _handle_signal(_signum: int, _frame: Any) -> None:
            self._stop.set()

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        logger.info(
            "Connecting %s to mqtt://%s:%s",
            self.device_id,
            self.mqtt_host,
            self.mqtt_port,
        )
        while not self._stop.is_set():
            try:
                self._client.connect(self.mqtt_host, self.mqtt_port, keepalive=30)
                break
            except OSError as exc:
                logger.warning("MQTT not ready (%s); retrying…", exc)
                time.sleep(2)

        self._client.loop_start()
        try:
            while not self._stop.is_set():
                sample = self._sample()
                self._client.publish(self._telemetry_topic(), sample.to_json(), qos=0)
                self._stop.wait(self.publish_interval_s)
        finally:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("Device %s stopped", self.device_id)


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return float(raw)


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
