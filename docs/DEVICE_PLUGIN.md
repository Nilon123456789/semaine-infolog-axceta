# Adding a new simulated device

Goal: a new appliance meter should take minutes, not a refactor.

## Contract

1. Container publishes JSON to `devices/{DEVICE_ID}/telemetry` about once per second.
2. Container listens on `devices/{DEVICE_ID}/control` for `power_on`, `power_off`, `set_watts` (and optional custom actions).
3. Required telemetry fields: `device_id`, `device_name`, `device_type`, `watts`, `amps`, `voltage`, `powered`, `ts`.

## Steps

1. Copy an existing device folder under `services/devices/` (e.g. `lamp/`) to a new name, e.g. `heater/`.
2. Implement `compute_watts()` (subclass `DeviceSimulator` from `_sdk`).
3. Add a Dockerfile that copies `_sdk` + your `main.py` (same pattern as lamp/powerbar).
4. Register the service in `docker-compose.yml`:

```yaml
  heater:
    build:
      context: ./services/devices
      dockerfile: heater/Dockerfile
    environment:
      MQTT_HOST: mosquitto
      MQTT_PORT: 1883
      DEVICE_ID: heater-basement
      DEVICE_NAME: Basement Heater
      DEVICE_TYPE: heater
      NOMINAL_WATTS: "800"
    depends_on:
      mosquitto:
        condition: service_healthy
    networks:
      - axceta
    restart: unless-stopped
```

5. Rebuild: `docker compose up -d --build heater`
6. Confirm the device appears on the dashboard within a few seconds.

## Tips

- Keep `DEVICE_ID` unique across the stack.
- Prefer the shared SDK so control + noise + MQTT reconnect stay consistent.
- Document any custom control actions next to the device `main.py`.
