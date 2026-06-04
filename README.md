# Sunsynk Cloud for Home Assistant

A HACS custom integration that connects Home Assistant to the [Sunsynk cloud API](https://www.sunsynk.net) for reading and writing inverter settings. Includes a custom Lovelace card with a visual timer editor.

This integration supplements the [kellerza add-on](https://github.com/kellerza/sunsynk) (which provides local Modbus reads) by adding cloud-based settings control. It does not replace kellerza — both can run side by side.

## Features

- **Writable settings** — work mode, energy mode, battery limits, power limits, timer schedules, and more, exposed as standard HA entities (`select`, `number`, `switch`, `time`)
- **Realtime sensors** — PV power, battery SOC, grid power, load, daily energy totals
- **Timer schedule** — 6-slot timer with per-slot power, SOC target, grid charge toggle, and day-of-week control
- **Custom Lovelace card** — power flow display, collapsible settings panels, 24-hour visual timeline for timer slots
- **Multi-inverter support** — one config entry per account, entities per inverter
- **Write safety** — battery and system settings are never mixed in a single API call; writes are debounced and verified with a read-after-write check
- **Predbat compatible** — all settings are standard HA entities, so Predbat and any automation can control the inverter directly

## Supported Inverters

Tested with Deye hybrid inverters using the `common/setting` endpoint. Other Sunsynk-branded inverters using the same cloud portal should work. Grid-tied, micro, and Sunsynk Store inverters use different API endpoints and are not yet supported.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/canaokar/ha-sunsynk-cloud` as an **Integration**
4. Search for "Sunsynk Cloud" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/sunsynk_cloud/` folder into your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Sunsynk Cloud**
3. Enter your sunsynk.net email and password
4. The integration discovers your inverters and creates entities

### Options

After setup, click **Configure** on the integration to adjust:

- **Settings poll interval** — how often to read settings from the cloud (default: 300s, range: 60–900s)
- **Realtime poll interval** — how often to read power flow data (default: 60s, range: 30–300s)
- **Enable realtime sensors** — toggle realtime polling on/off

## Entities

Each inverter creates approximately 61 entities:

### Read-Only Sensors (10)

| Entity | Unit | Description |
|--------|------|-------------|
| `sensor.*_pv_power` | W | Solar panel output |
| `sensor.*_battery_power` | W | Battery charge/discharge power |
| `sensor.*_battery_soc` | % | Battery state of charge |
| `sensor.*_grid_power` | W | Grid import (positive) or export (negative) |
| `sensor.*_load_power` | W | Home consumption |
| `sensor.*_daily_grid_import` | kWh | Today's grid import |
| `sensor.*_daily_grid_export` | kWh | Today's grid export |
| `sensor.*_daily_battery_charge` | kWh | Today's battery charge |
| `sensor.*_daily_battery_discharge` | kWh | Today's battery discharge |
| `sensor.*_daily_load_consumption` | kWh | Today's home consumption |

### Writable Settings

**Select (2):** Work mode, energy mode

**Switch (4):** Solar sell, grid charge, peak & valley, grid peak shaving

**Number (12):** Max sell power, zero export power, grid charge SOC, grid charge current, battery shutdown/restart/low SOC, max charge/discharge current, grid peak power, import power limit, AC output power limit

### Timer Slots (per slot × 6)

**Time (6):** End time for each slot

**Number (12):** Power limit and SOC target per slot

**Switch (12):** Enable and grid charge toggle per slot

### Day-of-Week (7)

**Switch (7):** Monday through Sunday toggles for the timer schedule

## Custom Card

The integration includes a custom Lovelace card. Add it to a dashboard:

```yaml
type: custom:sunsynk-cloud-card
device: "YOUR_INVERTER_SN"
```

### Card Options

```yaml
type: custom:sunsynk-cloud-card
device: "2601120338"
show_realtime: true    # show live power flow tiles
show_timers: true      # show timer schedule section
show_battery: true     # show battery settings section
show_grid: true        # show grid settings section
compact: false         # compact mode for sidebar panels
```

### Card Sections

- **Header** — battery SOC badge and live power flow tiles (PV, battery, grid, load)
- **Work Mode & General** — dropdowns and toggles for system settings
- **Timer Schedule** — 24-hour visual timeline with colour-coded slots (blue = grid charge, green = solar, grey = disabled) and day-of-week row
- **Battery** — shutdown/low/restart SOC sliders, charge/discharge current limits
- **Grid** — grid charge toggle and SOC target, peak shaving toggle and power limit

All sections are collapsible.

## Predbat Integration

Predbat can control the inverter through standard HA service calls — no custom code needed:

```yaml
# Set charge rate
service: number.set_value
target:
  entity_id: number.sunsynk_2601120338_max_charge_current
data:
  value: 110

# Enable grid charging
service: switch.turn_on
target:
  entity_id: switch.sunsynk_2601120338_grid_charge

# Change work mode
service: select.select_option
target:
  entity_id: select.sunsynk_2601120338_work_mode
data:
  option: "Zero Export"
```

## Write Safety

The integration enforces several safety measures for settings writes:

- **Category separation** — battery settings and system/grid settings are never mixed in a single API POST (the Sunsynk API rejects or corrupts mixed writes)
- **Debounce** — multiple changes within 2 seconds are batched into a single request
- **Read-after-write** — the integration re-reads settings 30 seconds after any write to confirm the inverter accepted the change
- **Retry with backoff** — failed writes are retried up to 3 times with exponential delays (4s, 8s, 16s)
- **Re-authentication** — on 401 responses, the client automatically re-authenticates and retries

## Known Limitations

| Issue | Detail |
|-------|--------|
| Cloud-only | Requires internet. For local control, use kellerza's Modbus integration |
| API stability | Sunsynk may change their cloud API without notice |
| Rate limits | Conservative polling intervals to avoid rate limiting |
| Inverter types | Only hybrid inverters using the `common/setting` endpoint are tested |

## Contributing

Contributions are welcome. Please open an issue first to discuss the change you'd like to make.

## License

MIT
