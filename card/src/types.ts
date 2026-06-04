export interface SunsynkCardConfig {
  device: string;
  show_realtime?: boolean;
  show_timers?: boolean;
  show_battery?: boolean;
  show_grid?: boolean;
  compact?: boolean;
}

export interface TimerSlot {
  index: number;
  enabled: boolean;
  endTime: string;
  power: number;
  soc: number;
  gridCharge: boolean;
}

export interface HassEntity {
  state: string;
  attributes: Record<string, unknown>;
  entity_id: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: { entity_id: string }
  ): Promise<void>;
}
