# AI usage

This document describes how AI assisted the Axceta Local Energy Dashboard submission.

## Tools and models

| Tool | Role |
|---|---|
| **Cursor** (agent / Composer) | Primary coding agent: planning, implementation, debugging, docs, git |
| **Impeccable** (Cursor skill) | Operate-mode UI/UX: PRODUCT/DESIGN context, critique, polish |
| **Browser tools** (Cursor) | Live dashboard inspection during UI critique and polish |

Human decisions drove stack choice (local-first Docker Compose), English UI, and acceptance of the implementation plan. AI executed design and engineering within those constraints.

## What AI did

### 1. Requirements intake

- Extracted and decoded the challenge text from `Défi_Axceta.pdf` (compressed PDF CID encoding).
- Mapped requirements to a concrete architecture (MQTT simulators → FastAPI “cloud” → React dashboard).
- Asked clarifying questions (local-first vs real cloud; English vs French); plan locked to **local-first + English + Impeccable UI**.

### 2. Architecture and planning

- Produced an implementation plan (Compose layout, metrics formulas, device plugin contract, CI/CD, Operate-mode dashboard intent).
- Documented assumptions (e.g. peak-stress window as configurable local hours, default 16:00–20:00).

### 3. Implementation

AI authored essentially all application code and config, including:

- `docker-compose.yml`, Mosquitto config, Makefiles
- Device SDK + simulators (`lamp`, `powerbar`, later `heater`, `fridge`, `kettle`)
- FastAPI cloud (MQTT ingest, SQLite, metrics, control, WebSocket)
- React dashboard (live snapshot hook, power strip, energy panel, device controls)
- Unit tests for energy integration math; CI workflow; README / ARCHITECTURE / DEVICE_PLUGIN docs

### 4. UI / UX (Impeccable)

- Wrote `PRODUCT.md` and `DESIGN.md` (Operate mode; code-led path when the Impeccable launcher was unavailable in the agent sandbox).
- Ran a dual-agent **critique** (~27/40 heuristics); then implemented feedback: powerbar outlets, per-device confirmation, peak-stress copy, card layout, quieter motion, brand/watts hierarchy.
- Verified builds and iterated from live/browser evidence where the stack was reachable.

### 5. Hardening and submission hygiene

- Fixed submission gaps (e.g. `tzdata` in the cloud image, safer timezone resolution, lockfile sync for Docker `npm ci`, CORS for local origins).
- Added more devices and raised the power-strip scale for multi-kW loads.
- Initialized a git repository and created the initial commit after analysis.

## What AI did *not* do alone

- Did not invent commercial claims or external utility APIs beyond the challenge scope.
- Did not replace human product choices (local-first stack, English UI).
- Impeccable CLI (`concept-seed` / live overlay) was often blocked in the agent sandbox; design proceeded from PRODUCT/DESIGN + craft guidance and source/browser review instead of a full dice-driven world roll in-session.
- Docker rebuilds and final demo runs on the developer machine were (and remain) a human step when the agent lacked Docker socket access.

## Human oversight

- Confirmed plan options and “implement the plan / critique feedback / commit” requests.
- Ran `docker compose up --build` locally to validate the running stack.
- Owns final review of metrics correctness, demo narrative, and marketplace/academic integrity requirements for the submission.

## Integrity note

All AI-generated code and docs in this repository were produced for this challenge under human direction. This file is the disclosure of that assistance.
