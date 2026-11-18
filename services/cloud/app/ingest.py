"""
MQTT ingest worker.

Subscribes to devices/+/telemetry and devices/+/status, validates payloads,
writes SQLite, and signals the API loop that a fresh snapshot is available.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Callable

import paho.mqtt.client as mqtt

from .db import Database

logger = logging.getLogger("axceta.ingest")


class MqttIngest:
    """Background MQTT client bound to the process lifetime."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        db: Database,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.on_change = on_change
        self.connected = False
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="axceta-cloud-ingest",
        )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="mqtt-ingest", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass

    def publish_control(self, device_id: str, payload: dict[str, Any]) -> bool:
        """Publish a control message; returns True if the client believes it sent."""
        if not self.connected:
            return False
        topic = f"devices/{device_id}/control"
        info = self._client.publish(topic, json.dumps(payload), qos=1)
        return info.rc == mqtt.MQTT_ERR_SUCCESS

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._client.connect(self.host, self.port, keepalive=30)
                self._client.loop_start()
                while not self._stop.is_set():
                    time.sleep(0.5)
                break
            except OSError as exc:
                logger.warning("MQTT connect failed (%s); retrying…", exc)
                time.sleep(2)

    def _on_connect(
        self,
        client: mqtt.Client,
        _userdata: Any,
        _flags: Any,
        reason_code: mqtt.ReasonCode,
        _properties: Any = None,
    ) -> None:
        if reason_code.is_failure:
            self.connected = False
            logger.error("MQTT connect rejected: %s", reason_code)
            return
        self.connected = True
        client.subscribe("devices/+/telemetry")
        client.subscribe("devices/+/status")
        logger.info("MQTT ingest connected; subscribed to device topics")

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _flags: Any,
        reason_code: mqtt.ReasonCode,
        _properties: Any = None,
    ) -> None:
        self.connected = False
        logger.warning("MQTT disconnected: %s", reason_code)

    def _on_message(
        self, _client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Bad MQTT payload on %s", msg.topic)
            return

        parts = msg.topic.split("/")
        if len(parts) != 3 or parts[0] != "devices":
            return
        device_id = parts[1]
        kind = parts[2]

        if kind == "telemetry":
            self._handle_telemetry(device_id, payload)
        elif kind == "status":
            # Status is informational; telemetry already upserts registry.
            logger.debug("Status from %s: %s", device_id, payload.get("powered"))

    def _handle_telemetry(self, device_id: str, payload: dict[str, Any]) -> None:
        try:
            watts = float(payload["watts"])
            amps = float(payload.get("amps", 0.0))
            voltage = float(payload.get("voltage", 120.0))
            powered = bool(payload.get("powered", True))
            ts = float(payload.get("ts", time.time()))
            name = str(payload.get("device_name") or device_id)
            dtype = str(payload.get("device_type") or "unknown")
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Invalid telemetry from %s: %s", device_id, exc)
            return

        self.db.upsert_sample(
            device_id=device_id,
            device_name=name,
            device_type=dtype,
            watts=watts,
            amps=amps,
            voltage=voltage,
            powered=powered,
            ts=ts,
        )
        if self.on_change:
            try:
                self.on_change()
            except Exception:
                logger.exception("on_change callback failed")
