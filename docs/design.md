# ha-sunsynk-cloud — Design Specification

**Project:** HACS custom integration + custom Lovelace card for Sunsynk/Deye inverter control via the cloud API.

**Repository:** `ha-sunsynk-cloud`
**License:** MIT
**Date:** 2026-06-04

---

## 1. Problem Statement

The kellerza Home Assistant add-on reads inverter data via Modbus/RS485 locally. It's reliable for monitoring but cannot write settings. The Sunsynk cloud portal (sunsynk.net) exposes 300+ configurable fields — work modes, timer schedules, battery limits, grid protection — but has no API documentation and no HA integration for settings control.

Predbat (battery prediction/automation) needs to change inverter settings dynamically but cannot call the Sunsynk cloud API directly. If settings are exposed as standard HA entities, Predbat and any automation can control the inverter through HA services (`number.set_value`, `select.select_option`, `switch.turn_on`).

## 2. Goals

1. Expose all important inverter settings as writable HA entities.
2. Provide read-only sensors for cloud-sourced data (energy totals, flow data).
3. Ship a custom Lovelace card with visual timer editor for manual control.
4. Work alongside kellerza (supplement, not replace).
5. Support multiple inverters per account.
6. Publish as a HACS-installable integration.

## 3. Non-Goals

- Replacing kellerza for local Modbus reads.
- Supporting the official OpenAPI (HMAC-signed) endpoint — web portal API only.
- Supporting non-hybrid inverter types in Phase 1 (grid-tied, micro, string, Sunsynk Store). The architecture allows adding these later via the type-specific setting endpoints discovered in the API spec.

## 4. Architecture

### 4.1 Component Overview

```
Home Assistant
├── custom_components/sunsynk_cloud/     ← HACS integration (Python)
│   ├── __init__.py          Setup, platforms, coordinators
│   ├── config_flow.py       UI-based setup + options flow
│   ├── api.py               Async API client (auth, GET, POST)
│   ├── coordinator.py       DataUpdateCoordinator(s)
│   ├── const.py             Setting definitions, field maps, enums
│   ├── sensor.py            Read-only sensor entities
│   ├── number.py            Writable numeric entities
│   ├── select.py            Writable enum entities
│   ├── switch.py            Writable toggle entities
│   ├── time.py              Writable time entities
│   ├── manifest.json        Integration manifest
│   ├── strings.json         UI strings / translations
│   └── translations/
│       └── en.json
└── www/community/
    └── sunsynk-cloud-card.js            ← Custom Lovelace card (TypeScript → JS)
```

### 4.2 API Client (`api.py`)

Async client using `aiohttp`. Handles the full auth lifecycle:

1. **Login:** `GET /anonymous/publicKey` → RSA-encrypt password → `POST /oauth/token/new`
2. **Token storage:** Access token + refresh token held in memory, persisted via HA's config entry data for restart survival.
3. **Auto-refresh:** On 401 response, re-authenticate and retry the request once.
4. **Rate limiting:** Minimum 60s between identical GET requests (enforced by the coordinators, not the client).

Key methods:
- `authenticate(username, password) → token`
- `get_plants() → list[Plant]`
- `get_inverters(plant_id) → list[Inverter]`
- `get_flow(sn) → FlowData`
- `get_grid_realtime(sn) → GridData`
- `get_battery_realtime(sn) → BatteryData`
- `get_load_realtime(sn) → LoadData`
- `get_settings(sn) → dict` (GET `common/setting/{sn}/read`)
- `post_settings(sn, settings: dict) → bool` (POST `common/setting/{sn}/set`)

The RSA encryption uses the `cryptography` library (bundled with HA) to handle PKCS1v15 encryption of the password against the server's public key.

### 4.3 Coordinators

Two `DataUpdateCoordinator` instances per inverter:

| Coordinator | Endpoints polled | Default interval | Purpose |
|---|---|---|---|
| `SunsynkSettingsCoordinator` | `common/setting/{sn}/read` | 300s (5 min) | Settings entities |
| `SunsynkRealtimeCoordinator` | `inverter/{sn}/flow`, `inverter/grid/{sn}/realtime`, `inverter/battery/{sn}/realtime`, `inverter/load/{sn}/realtime` | 60s | Sensor entities |

Both intervals are configurable via the Options Flow after setup.

### 4.4 Config Flow

**Step 1 — Credentials:**
- Email (string)
- Password (string, masked)
- Click "Submit" → integration calls `api.authenticate()` → validates credentials

**Step 2 — Discovery:**
- Integration calls `get_plants()` → `get_inverters()` for each plant
- If single inverter: auto-select, proceed
- If multiple: show multi-select for which inverters to add

**Step 3 — Done:**
- Config entry created. Entities appear.

**Options Flow (post-setup):**
- Change realtime poll interval (30-300s)
- Change settings poll interval (60-900s)
- Enable/disable realtime sensors (if user only wants settings control)

**Re-auth Flow:**
- If credentials expire or password changes, HA shows "Re-authenticate" prompt
- User enters new password → integration re-authenticates

### 4.5 Device Model

Each inverter becomes an HA Device:
- **Identifiers:** `(DOMAIN, inverter_sn)`
- **Name:** Inverter alias or SN
- **Manufacturer:** Brand from API (e.g., "Deye")
- **Model:** From API (e.g., "10kW Hybrid")
- **SW Version:** `softVer` from API
- **Via Device:** Gateway (optional)

## 5. Entity Specification

### 5.1 Read-Only Sensors

Created by `sensor.py`, updated by `SunsynkRealtimeCoordinator`.

| Entity ID suffix | Source | Unit | Device class | State class |
|---|---|---|---|---|
| `pv_power` | `flow.pvPower` | W | power | measurement |
| `battery_power` | `flow.battPower` | W | power | measurement |
| `battery_soc` | `flow.soc` | % | battery | measurement |
| `grid_power` | `flow.gridOrMeterPower` | W | power | measurement |
| `load_power` | `flow.loadOrEpsPower` | W | power | measurement |
| `daily_pv_generation` | `input.etoday` | kWh | energy | total_increasing |
| `daily_grid_import` | `grid.etodayFrom` | kWh | energy | total_increasing |
| `daily_grid_export` | `grid.etodayTo` | kWh | energy | total_increasing |
| `daily_battery_charge` | `batt.etodayChg` | kWh | energy | total_increasing |
| `daily_battery_discharge` | `batt.etodayDischg` | kWh | energy | total_increasing |
| `daily_load_consumption` | `load.dailyUsed` | kWh | energy | total_increasing |
| `inverter_status` | `inverter.runStatus` | — | — | — |

Attributes on `grid_power`: `etotalFrom`, `etotalTo`, `acRealyStatus`, `frequency`.
Attributes on `battery_soc`: `bmsVolt`, `bmsCurrent`, `bmsTemp`, `capacity`.

### 5.2 Writable Entities — Main Settings

Created by `select.py`, `number.py`, `switch.py`. Updated by `SunsynkSettingsCoordinator`. Writes via `api.post_settings()`.

**Select entities:**

| Entity ID suffix | Field | Options |
|---|---|---|
| `work_mode` | `sysWorkMode` | `0`: Selling First, `1`: Zero Export, `2`: Limited to Home |
| `energy_mode` | `energyMode` | `0`: Battery First, `1`: Load First |

**Switch entities:**

| Entity ID suffix | Field | On value | Off value |
|---|---|---|---|
| `solar_sell` | `solarSell` | `"1"` | `"0"` |
| `grid_charge` | `sdChargeOn` | `"1"` | `"0"` |
| `peak_and_valley` | `peakAndVallery` | `"1"` | `"0"` |
| `grid_peak_shaving` | `gridPeakShaving` | `"1"` | `"0"` |

**Number entities:**

| Entity ID suffix | Field | Min | Max | Step | Unit |
|---|---|---|---|---|---|
| `max_sell_power` | `solarMaxSellPower` | 0 | 15000 | 100 | W |
| `zero_export_power` | `zeroExportPower` | 0 | 500 | 10 | W |
| `grid_charge_soc` | `sdStartCap` | 10 | 90 | 1 | % |
| `grid_charge_current` | `sdBatteryCurrent` | 0 | 275 | 5 | A |
| `battery_shutdown_soc` | `batteryShutdownCap` | 0 | 100 | 1 | % |
| `battery_restart_soc` | `batteryRestartCap` | 0 | 100 | 1 | % |
| `battery_low_soc` | `batteryLowCap` | 0 | 100 | 1 | % |
| `max_charge_current` | `batteryMaxCurrentCharge` | 0 | 280 | 5 | A |
| `max_discharge_current` | `batteryMaxCurrentDischarge` | 0 | 280 | 5 | A |
| `grid_peak_power` | `gridPeakPower` | 0 | 15000 | 100 | W |
| `import_power_limit` | `importPower` | 0 | 15000 | 100 | W |
| `ac_output_power_limit` | `acOutputPowerLimit` | 0 | 15000 | 100 | W |

### 5.3 Writable Entities — Timer Slots (x6)

Each slot `{n}` (1-6) creates:

| Entity ID suffix | Type | Field | Details |
|---|---|---|---|
| `timer_{n}_enable` | switch | `sellTime{n}En` | `"1"`/`"0"` |
| `timer_{n}_end_time` | time | `sellTime{n}` | `"HH:MM"` format |
| `timer_{n}_power` | number | `sellTime{n}Pac` | 0-10000 W, step 100 |
| `timer_{n}_soc` | number | `cap{n}` | 0-100 %, step 1 |
| `timer_{n}_grid_charge` | switch | `time{n}on` | `"true"`/`"false"` |

**Day-of-week switches (shared across all slots):**

| Entity ID suffix | Field |
|---|---|
| `schedule_monday` | `mondayOn` |
| `schedule_tuesday` | `tuesdayOn` |
| `schedule_wednesday` | `wednesdayOn` |
| `schedule_thursday` | `thursdayOn` |
| `schedule_friday` | `fridayOn` |
| `schedule_saturday` | `saturdayOn` |
| `schedule_sunday` | `sundayOn` |

### 5.4 Write Safety

- **Debounce:** If multiple writes happen within 2 seconds, batch them into a single POST.
- **Read-after-write:** Force a settings coordinator refresh 30 seconds after any write to confirm the inverter accepted the change.
- **Optimistic update:** Entity state updates immediately in HA (responsive UI), but reverts if the read-after-write shows the setting didn't take.
- **Error surfacing:** Failed writes raise `HomeAssistantError` which shows as a persistent notification in HA.
- **No mixing:** Battery settings and system mode settings are never combined in a single POST (API constraint from reverse-engineering).

Setting categories for POST separation:
- **System group:** `sysWorkMode`, `energyMode`, `peakAndVallery`, `solarSell`, `solarMaxSellPower`, `pvMaxLimit`, `zeroExportPower`, `loadMode`, all `sellTime*`, all `cap*`, all `time*on`, all `genTime*on`, all day-of-week fields, `gridPeakShaving`, `gridPeakPower`
- **Battery group:** `battMode`, `batteryCap`, `batteryMaxCurrentCharge`, `batteryMaxCurrentDischarge`, `batteryShutdownCap`, `batteryRestartCap`, `batteryLowCap`, `batteryOn`, `batteryEmptyV`, `batteryImpedance`, `batteryEfficiency`, `lithiumMode`, `bmsErrStop`, `chargeVolt`, `floatVolt`, `absorptionVolt`, `chargeCurrent`, `dischargeCurrent`
- **Grid charge group:** `sdChargeOn`, `sdStartCap`, `sdBatteryCurrent`, `sdStartVolt`, `gridSignal`, `gridAlwaysOn`

## 6. Custom Lovelace Card

### 6.1 Tech Stack

- **Language:** TypeScript
- **Framework:** LitElement (HA standard)
- **Build:** Rollup, outputting a single `sunsynk-cloud-card.js`
- **Styling:** CSS-in-JS via Lit's `css` tagged template
- **Distribution:** Bundled with the integration, auto-registered via `async_setup_entry`

### 6.2 Card Configuration

Minimal:
```yaml
type: custom:sunsynk-cloud-card
device: "2601120338"
```

Full options:
```yaml
type: custom:sunsynk-cloud-card
device: "2601120338"
show_realtime: true        # show live power flow header
show_timers: true          # show timer schedule section
show_battery: true         # show battery settings section
show_grid: true            # show grid settings section
compact: false             # compact mode for sidebar
```

### 6.3 Card Layout

**Header — Live Status**
- Inverter name, online/offline indicator
- Battery SOC gauge (circular)
- PV power, grid power, load power, battery power as value tiles
- Flow direction arrows with colour coding

**Section 1 — Work Mode & General**
- Work mode dropdown (Selling First / Zero Export / Limited to Home)
- Energy mode dropdown
- Solar sell toggle + max sell power slider
- Zero export power slider

**Section 2 — Timer Schedule**
- 24-hour timeline bar showing all 6 slots
- Colour coding: blue = grid charging, green = solar/discharge, grey = disabled
- Click slot → edit popup with:
  - End time picker
  - Power limit slider
  - Target SOC slider
  - Grid charge toggle
  - Generator charge toggle
- Drag slot edges to adjust times
- Day-of-week toggle row (Mo-Su)
- "Save Changes" / "Reset" buttons (batches all timer changes into one or two POSTs)

**Section 3 — Battery Settings**
- Shutdown SOC slider
- Low warning SOC slider
- Restart SOC slider
- Max charge current slider
- Max discharge current slider

**Section 4 — Grid Settings**
- Grid charge toggle
- Grid charge start SOC slider
- Grid charge current slider
- Peak shaving toggle + power slider

All sections are collapsible. The card reads entity states for display and calls HA services for writes.

### 6.4 Card Registration

The integration registers the card resource in `async_setup_entry`:
```python
# In __init__.py async_setup_entry
hass.http.register_static_path(
    "/sunsynk_cloud/sunsynk-cloud-card.js",
    hass.config.path("custom_components/sunsynk_cloud/card/sunsynk-cloud-card.js"),
    cache_headers=True,
)
# Register as Lovelace resource
await hass.components.lovelace.async_create_resource(
    {"url": "/sunsynk_cloud/sunsynk-cloud-card.js", "type": "module"},
)
```

## 7. Technology Decisions

| Decision | Choice | Reason |
|---|---|---|
| Integration framework | HA DataUpdateCoordinator | Standard pattern, handles polling, caching, error retry |
| HTTP client | aiohttp | Async, bundled with HA, no extra dependencies |
| RSA encryption | `cryptography` library | Bundled with HA, handles PKCS1v15 |
| Card framework | LitElement + TypeScript | HA standard for custom cards |
| Card bundler | Rollup | Produces single JS file, tree-shakes well |
| Credential storage | HA config entry `.storage/` | Encrypted, standard HA pattern |
| License | MIT | Standard for HA integrations |

## 8. Implementation Phases

### Phase 1 — Core Integration (MVP)
**Deliverable:** Working HACS integration that exposes writable settings entities.

- Project scaffolding: `manifest.json`, `const.py`, `__init__.py`, `strings.json`
- `api.py`: Full async API client with RSA auth, token refresh, settings read/write
- `config_flow.py`: Email + password UI, credential validation, inverter discovery
- `coordinator.py`: `SunsynkSettingsCoordinator` (5-min polling)
- `select.py`: Work mode, energy mode
- `number.py`: All numeric settings (SOC limits, power limits, currents)
- `switch.py`: Solar sell, grid charge, peak shaving, peak & valley
- Write safety: debounce, read-after-write, error surfacing, category separation
- Manual testing against live API

### Phase 2 — Realtime Sensors + Timer Entities
**Deliverable:** Full entity coverage including timers and live data.

- `SunsynkRealtimeCoordinator` (60s polling): flow, grid, battery, load
- `sensor.py`: All 12 read-only sensors with proper device classes
- `time.py`: Timer end-time entities (x6)
- Timer-related number and switch entities (x24)
- Day-of-week switch entities (x7)
- Options flow: poll interval configuration

### Phase 3 — Custom Lovelace Card
**Deliverable:** Visual control card with timer editor.

- TypeScript + Rollup build pipeline
- Card scaffolding: LitElement base, HA types, entity subscription
- Live status header with power flow display
- Work mode & general settings section
- Battery & grid settings section
- Timer visual timeline renderer
- Timer slot edit dialog
- Timer drag-to-resize interaction
- Batch save logic for timer changes
- Card auto-registration from integration
- Responsive layout (desktop, mobile, sidebar)

### Phase 4 — Polish & Release
**Deliverable:** HACS-ready public release.

- `hacs.json`, `info.md` for HACS
- Re-auth flow for expired credentials
- Connection retry with exponential backoff
- Translations framework (English complete)
- README with screenshots, installation guide, Predbat integration example
- GitHub Actions CI (linting, type checking)
- GitHub release workflow
- HACS default repository submission

## 9. Predbat Integration

Once settings entities exist, Predbat can control the inverter through HA automations:

```yaml
# Example: Predbat sets charge rate
service: number.set_value
target:
  entity_id: number.sunsynk_2601120338_max_charge_current
data:
  value: 110

# Example: Predbat enables grid charging during cheap rate
service: switch.turn_on
target:
  entity_id: switch.sunsynk_2601120338_grid_charge

# Example: Predbat sets work mode
service: select.select_option
target:
  entity_id: select.sunsynk_2601120338_work_mode
data:
  option: "Zero Export"
```

No Predbat code changes are needed — it works through standard HA service calls.

## 10. Risk & Mitigations

| Risk | Mitigation |
|---|---|
| Sunsynk changes API / breaks auth | Pin to known working endpoints. Auth flow extracted from live JS. Version-check on startup. |
| Rate limiting by Sunsynk | Conservative polling (60s realtime, 300s settings). Debounce writes. |
| Settings write breaks inverter | Category separation enforced. Read-after-write verification. User confirmation on card save. |
| Token expiry mid-session | Auto-refresh on 401. Persistent token in config entry for restart. |
| kellerza entity conflicts | Different domain (`sunsynk_cloud` vs `sunsynk`). Entities have distinct IDs. No overlap. |
