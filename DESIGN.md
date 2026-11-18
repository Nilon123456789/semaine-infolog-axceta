# Design system — Axceta Local Energy Dashboard

<!-- Documented from the built Operate surface (code-led; Impeccable launcher unavailable in this environment). -->

## World

Cool load-board: mist green-gray paper, slate ink, teal live-power signal. Brand name leads the chrome; the signature interaction is the continuous horizontal power strip that fills with house load.

## Tokens

| Token | Value | Role |
|---|---|---|
| `--ink` | `#14201c` | Primary text |
| `--ink-muted` | `#44554e` | Secondary text |
| `--paper` | `#eef2f0` | Page ground |
| `--paper-deep` | `#dde5e1` | Recessed surfaces |
| `--line` | `#b7c4be` | Rules / borders |
| `--live` / `--live-deep` | `#0d7a6f` / `#06554d` | Live power / primary actions |
| `--ok` | `#1f6b4a` | Online |
| `--off` | `#5c6b65` | Offline |
| `--danger` | `#9b1c1c` | Errors |
| `--font` | Public Sans (self-hosted variable) | UI face |
| `--radius` | `2px` | Controls |

## Layout

1. Top bar: quieter **Axceta** + “Local stack” connection state  
2. Power strip: house total (primary) + per-device legend + segmented load rail  
3. Asymmetric energy pair: Today | Peak-stress with inline definition  
4. Device cards: combined status, power toggle, load override, powerbar outlets  

## Motion

Short strip entrance (opacity/translate only); segment widths ease on live updates; connecting pulse on the status dot.

## States

Skeleton loading, empty devices, offline cards, per-device aria-live success/error, cloud Retry, peak Active/Outside, disabled controls when offline or busy.
