# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: React + Vite + TypeScript for the local dashboard; FastAPI + MQTT + Docker Compose for the local cloud and device simulators (chosen in the approved implementation plan).

## Users

Home energy operators and IoT demo reviewers who need to see household electrical load in real time and exercise simulated appliances without cloud accounts.

## Product Purpose

Axceta Local Energy Dashboard shows live electrical consumption from Docker-simulated IoT meters, aggregates it in a local “cloud,” and lets operators power devices on/off and adjust load. Success means the three required metrics (current, daily total, peak-stress window) are always visible, device connectivity is obvious, and state changes appear immediately.

## Positioning

Devices are first-class Docker containers with a documented plugin contract; the cloud is a local MQTT + FastAPI service rather than a hosted IoT platform, so the whole demo runs with one Compose command.

## Operating Context

Operators start the stack with Docker Compose, open the local dashboard, watch wattage update about once per second, and use on-page controls that publish MQTT commands to simulators (lamp, powerbar, heater, fridge, kettle). Grid stress peaks are a configurable daily time window (default 16:00–20:00).

## Capabilities and Constraints

- Metrics: current watts (sum of online devices), daily Wh/kWh, peak-stress Wh/kWh.
- Device list with connectivity (online/offline), powered state, and live watts.
- Control: power on/off, set watts, set powerbar outlets.
- English UI only.
- No multi-user auth; local-first only.
- Synthetic demo data from simulators — not utility-grade metering.

## Brand Commitments

Product name: **Axceta**. Voice: clear, technical, calm. English copy.

## Evidence on Hand

Challenge brief: `Défi_Axceta.pdf`. Synthetic telemetry from lamp and powerbar containers. No customer logos or third-party testimonials.

## Product Principles

1. Live truth over decoration — readings and connectivity lead every screen.
2. One action per control — power and load changes must be obvious and reversible.
3. Adding a device is a documented Compose + plugin step, not a code hunt.
4. Metrics formulas stay documented and tested in one cloud module.
5. Local-first: the demo never depends on an external cloud account.

## Accessibility & Inclusion

Target WCAG 2.2 AA contrast for body text; keyboard-focusable controls; status not conveyed by color alone.
