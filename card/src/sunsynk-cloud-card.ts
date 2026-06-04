import { LitElement, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { cardStyles } from "./styles";
import type { SunsynkCardConfig, HomeAssistant, TimerSlot } from "./types";

@customElement("sunsynk-cloud-card")
export class SunsynkCloudCard extends LitElement {
  static styles = cardStyles;

  @property({ attribute: false }) hass!: HomeAssistant;
  @state() private _config!: SunsynkCardConfig;
  @state() private _expandedSections: Set<string> = new Set(["timers"]);

  setConfig(config: SunsynkCardConfig): void {
    if (!config.device) {
      throw new Error("Please define a device (inverter SN)");
    }
    this._config = {
      show_realtime: true,
      show_timers: true,
      show_battery: true,
      show_grid: true,
      compact: false,
      ...config,
    };
  }

  private _prefix(): string {
    return `sunsynk_${this._config.device}`;
  }

  private _getState(domain: string, key: string): string | undefined {
    const entityId = `${domain}.${this._prefix()}_${key}`;
    return this.hass?.states[entityId]?.state;
  }

  private _getNumericState(domain: string, key: string): number | undefined {
    const val = this._getState(domain, key);
    if (val === undefined || val === "unavailable" || val === "unknown")
      return undefined;
    return parseFloat(val);
  }

  private async _callService(
    domain: string,
    service: string,
    entityId: string,
    data?: Record<string, unknown>
  ): Promise<void> {
    await this.hass.callService(domain, service, data, {
      entity_id: entityId,
    });
  }

  private _toggleSection(section: string): void {
    const next = new Set(this._expandedSections);
    if (next.has(section)) {
      next.delete(section);
    } else {
      next.add(section);
    }
    this._expandedSections = next;
  }

  protected render() {
    if (!this._config || !this.hass) return nothing;

    return html`
      <ha-card>
        ${this._renderHeader()}
        ${this._config.show_realtime ? this._renderPowerTiles() : nothing}
        ${this._renderSettingsSection()}
        ${this._config.show_timers ? this._renderTimerSection() : nothing}
        ${this._config.show_battery ? this._renderBatterySection() : nothing}
        ${this._config.show_grid ? this._renderGridSection() : nothing}
      </ha-card>
    `;
  }

  private _renderHeader() {
    const soc = this._getNumericState("sensor", "battery_soc");
    return html`
      <div class="header">
        <span class="title">Sunsynk Inverter</span>
        <div class="status">
          <span class="soc-badge"
            >${soc != null ? `${Math.round(soc)}%` : "--"}</span
          >
        </div>
      </div>
    `;
  }

  private _renderPowerTiles() {
    const pv = this._getNumericState("sensor", "pv_power");
    const batt = this._getNumericState("sensor", "battery_power");
    const grid = this._getNumericState("sensor", "grid_power");
    const load = this._getNumericState("sensor", "load_power");

    return html`
      <div class="power-grid">
        <div class="power-tile">
          <div class="value" style="color: #f9a825">${pv ?? "--"}W</div>
          <div class="label">PV</div>
        </div>
        <div class="power-tile">
          <div
            class="value"
            style="color: ${(batt ?? 0) > 0 ? "#ef5350" : "#66bb6a"}"
          >
            ${batt ?? "--"}W
          </div>
          <div class="label">Battery</div>
        </div>
        <div class="power-tile">
          <div
            class="value"
            style="color: ${(grid ?? 0) < 0 ? "#66bb6a" : "#ef5350"}"
          >
            ${grid ?? "--"}W
          </div>
          <div class="label">Grid</div>
        </div>
        <div class="power-tile">
          <div class="value">${load ?? "--"}W</div>
          <div class="label">Load</div>
        </div>
      </div>
    `;
  }

  private _renderSettingsSection() {
    const workMode = this._getState("select", "work_mode");
    const energyMode = this._getState("select", "energy_mode");
    const solarSell = this._getState("switch", "solar_sell");

    return html`
      <div class="section">
        <div
          class="section-header"
          @click=${() => this._toggleSection("settings")}
        >
          <h3>Work Mode & General</h3>
          <span>${this._expandedSections.has("settings") ? "▾" : "▸"}</span>
        </div>
        ${this._expandedSections.has("settings")
          ? html`
              <div class="section-content">
                <div class="setting-row">
                  <span class="label">Work Mode</span>
                  <ha-select
                    .value=${workMode}
                    @selected=${(e: CustomEvent) => {
                      const entityId = `select.${this._prefix()}_work_mode`;
                      this._callService("select", "select_option", entityId, {
                        option: (e.target as HTMLSelectElement).value,
                      });
                    }}
                  >
                    <mwc-list-item value="Selling First"
                      >Selling First</mwc-list-item
                    >
                    <mwc-list-item value="Zero Export"
                      >Zero Export</mwc-list-item
                    >
                    <mwc-list-item value="Limited to Home"
                      >Limited to Home</mwc-list-item
                    >
                  </ha-select>
                </div>
                <div class="setting-row">
                  <span class="label">Energy Mode</span>
                  <ha-select
                    .value=${energyMode}
                    @selected=${(e: CustomEvent) => {
                      const entityId = `select.${this._prefix()}_energy_mode`;
                      this._callService("select", "select_option", entityId, {
                        option: (e.target as HTMLSelectElement).value,
                      });
                    }}
                  >
                    <mwc-list-item value="Battery First"
                      >Battery First</mwc-list-item
                    >
                    <mwc-list-item value="Load First"
                      >Load First</mwc-list-item
                    >
                  </ha-select>
                </div>
                <div class="setting-row">
                  <span class="label">Solar Sell</span>
                  <ha-switch
                    .checked=${solarSell === "on"}
                    @change=${(e: Event) => {
                      const entityId = `switch.${this._prefix()}_solar_sell`;
                      const service = (e.target as HTMLInputElement).checked
                        ? "turn_on"
                        : "turn_off";
                      this._callService("switch", service, entityId);
                    }}
                  ></ha-switch>
                </div>
              </div>
            `
          : nothing}
      </div>
    `;
  }

  private _renderTimerSection() {
    const slots: TimerSlot[] = [];
    for (let i = 1; i <= 6; i++) {
      slots.push({
        index: i,
        enabled: this._getState("switch", `timer_${i}_enable`) === "on",
        endTime: this._getState("time", `timer_${i}_end_time`) ?? "00:00",
        power: this._getNumericState("number", `timer_${i}_power`) ?? 0,
        soc: this._getNumericState("number", `timer_${i}_soc`) ?? 0,
        gridCharge:
          this._getState("switch", `timer_${i}_grid_charge`) === "on",
      });
    }

    const startTimes = ["00:00", ...slots.slice(0, 5).map((s) => s.endTime)];

    return html`
      <div class="section">
        <div
          class="section-header"
          @click=${() => this._toggleSection("timers")}
        >
          <h3>Timer Schedule</h3>
          <span>${this._expandedSections.has("timers") ? "▾" : "▸"}</span>
        </div>
        ${this._expandedSections.has("timers")
          ? html`
              <div class="section-content">
                <div class="timeline-bar">
                  ${slots.map((slot, i) => {
                    const start = this._timeToPercent(startTimes[i]);
                    const end = this._timeToPercent(slot.endTime);
                    const width = end - start;
                    const cls = !slot.enabled
                      ? "disabled"
                      : slot.gridCharge
                        ? "grid-charge"
                        : "solar";
                    return html`
                      <div
                        class="timeline-slot ${cls}"
                        style="left: ${start}%; width: ${width}%"
                        title="Slot ${slot.index}: ${startTimes[i]}-${slot.endTime} | ${slot.power}W | SOC ${slot.soc}%"
                      >
                        <span>${slot.soc}%</span>
                        <span>${slot.power}W</span>
                      </div>
                    `;
                  })}
                </div>
                <div class="timeline-labels">
                  <span>00:00</span><span>06:00</span><span>12:00</span
                  ><span>18:00</span><span>24:00</span>
                </div>
                ${this._renderDayRow()}
              </div>
            `
          : nothing}
      </div>
    `;
  }

  private _renderDayRow() {
    const days = [
      { key: "monday", label: "Mo" },
      { key: "tuesday", label: "Tu" },
      { key: "wednesday", label: "We" },
      { key: "thursday", label: "Th" },
      { key: "friday", label: "Fr" },
      { key: "saturday", label: "Sa" },
      { key: "sunday", label: "Su" },
    ];

    return html`
      <div class="day-row">
        ${days.map((d) => {
          const active =
            this._getState("switch", `schedule_${d.key}`) === "on";
          return html`
            <div
              class="day-toggle ${active ? "active" : ""}"
              @click=${() => {
                const entityId = `switch.${this._prefix()}_schedule_${d.key}`;
                this._callService(
                  "switch",
                  active ? "turn_off" : "turn_on",
                  entityId
                );
              }}
            >
              ${d.label}
            </div>
          `;
        })}
      </div>
    `;
  }

  private _renderBatterySection() {
    return html`
      <div class="section">
        <div
          class="section-header"
          @click=${() => this._toggleSection("battery")}
        >
          <h3>Battery</h3>
          <span>${this._expandedSections.has("battery") ? "▾" : "▸"}</span>
        </div>
        ${this._expandedSections.has("battery")
          ? html`
              <div class="section-content">
                ${this._renderSlider(
                  "Shutdown SOC",
                  "number",
                  "battery_shutdown_soc",
                  "%",
                  0,
                  100
                )}
                ${this._renderSlider(
                  "Low Warning SOC",
                  "number",
                  "battery_low_soc",
                  "%",
                  0,
                  100
                )}
                ${this._renderSlider(
                  "Restart SOC",
                  "number",
                  "battery_restart_soc",
                  "%",
                  0,
                  100
                )}
                ${this._renderSlider(
                  "Max Charge Current",
                  "number",
                  "max_charge_current",
                  "A",
                  0,
                  280
                )}
                ${this._renderSlider(
                  "Max Discharge Current",
                  "number",
                  "max_discharge_current",
                  "A",
                  0,
                  280
                )}
              </div>
            `
          : nothing}
      </div>
    `;
  }

  private _renderGridSection() {
    const gridCharge = this._getState("switch", "grid_charge");
    const peakShaving = this._getState("switch", "grid_peak_shaving");

    return html`
      <div class="section">
        <div
          class="section-header"
          @click=${() => this._toggleSection("grid")}
        >
          <h3>Grid</h3>
          <span>${this._expandedSections.has("grid") ? "▾" : "▸"}</span>
        </div>
        ${this._expandedSections.has("grid")
          ? html`
              <div class="section-content">
                <div class="setting-row">
                  <span class="label">Grid Charge</span>
                  <ha-switch
                    .checked=${gridCharge === "on"}
                    @change=${(e: Event) => {
                      const entityId = `switch.${this._prefix()}_grid_charge`;
                      this._callService(
                        "switch",
                        (e.target as HTMLInputElement).checked
                          ? "turn_on"
                          : "turn_off",
                        entityId
                      );
                    }}
                  ></ha-switch>
                </div>
                ${this._renderSlider(
                  "Grid Charge SOC",
                  "number",
                  "grid_charge_soc",
                  "%",
                  10,
                  90
                )}
                ${this._renderSlider(
                  "Grid Charge Current",
                  "number",
                  "grid_charge_current",
                  "A",
                  0,
                  275
                )}
                <div class="setting-row">
                  <span class="label">Peak Shaving</span>
                  <ha-switch
                    .checked=${peakShaving === "on"}
                    @change=${(e: Event) => {
                      const entityId = `switch.${this._prefix()}_grid_peak_shaving`;
                      this._callService(
                        "switch",
                        (e.target as HTMLInputElement).checked
                          ? "turn_on"
                          : "turn_off",
                        entityId
                      );
                    }}
                  ></ha-switch>
                </div>
                ${this._renderSlider(
                  "Peak Shaving Power",
                  "number",
                  "grid_peak_power",
                  "W",
                  0,
                  15000
                )}
              </div>
            `
          : nothing}
      </div>
    `;
  }

  private _renderSlider(
    label: string,
    domain: string,
    key: string,
    unit: string,
    min: number,
    max: number
  ) {
    const val = this._getNumericState(domain, key);
    const entityId = `${domain}.${this._prefix()}_${key}`;

    return html`
      <div class="setting-row">
        <span class="label">${label}</span>
        <span>${val != null ? `${val}${unit}` : "--"}</span>
      </div>
      <ha-slider
        .min=${min}
        .max=${max}
        .value=${val ?? min}
        @change=${(e: Event) => {
          const newVal = (e.target as HTMLInputElement).value;
          this._callService("number", "set_value", entityId, {
            value: newVal,
          });
        }}
      ></ha-slider>
    `;
  }

  private _timeToPercent(time: string): number {
    const [h, m] = time.split(":").map(Number);
    return ((h * 60 + m) / 1440) * 100;
  }

  getCardSize(): number {
    return this._config?.compact ? 4 : 8;
  }

  static getStubConfig() {
    return { device: "" };
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const w = window as any;
w.customCards = w.customCards || [];
w.customCards.push({
  type: "sunsynk-cloud-card",
  name: "Sunsynk Cloud Card",
  description: "Control panel for Sunsynk/Deye inverters via cloud API",
});
