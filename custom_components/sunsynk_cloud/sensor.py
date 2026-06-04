import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback as ha_callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_BATTERY_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
    CONF_BATTERY_CAPACITY_OVERRIDE,
)
from .coordinator import SunsynkRealtimeCoordinator, SunsynkSettingsCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DEFINITIONS = [
    {"key": "pv_power", "data_path": "flow.pvPower", "unit": "W", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power"},
    {"key": "battery_power", "data_path": "flow.battPower", "unit": "W", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery"},
    {"key": "battery_soc", "data_path": "flow.soc", "unit": "%", "device_class": "battery", "state_class": "measurement", "icon": "mdi:battery-medium"},
    {"key": "grid_power", "data_path": "flow.gridOrMeterPower", "unit": "W", "device_class": "power", "state_class": "measurement", "icon": "mdi:transmission-tower"},
    {"key": "load_power", "data_path": "flow.loadOrEpsPower", "unit": "W", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt"},
    {"key": "daily_pv_generation", "data_path": "grid.etodayTo", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:solar-power"},
    {"key": "daily_grid_import", "data_path": "grid.etodayFrom", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:transmission-tower-import"},
    {"key": "daily_grid_export", "data_path": "grid.etodayTo", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:transmission-tower-export"},
    {"key": "daily_battery_charge", "data_path": "battery.etodayChg", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:battery-charging"},
    {"key": "daily_battery_discharge", "data_path": "battery.etodayDischg", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:battery-minus"},
    {"key": "daily_load_consumption", "data_path": "load.dailyUsed", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:home-lightning-bolt"},
]

DEVICE_CLASS_MAP = {
    "power": SensorDeviceClass.POWER,
    "battery": SensorDeviceClass.BATTERY,
    "energy": SensorDeviceClass.ENERGY,
}

STATE_CLASS_MAP = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}

MIN_DISCHARGE_W = 50


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for sn, inv_data in data["coordinators"].items():
        if entry.options.get("enable_realtime", True):
            for defn in SENSOR_DEFINITIONS:
                entities.append(
                    SunsynkRealtimeSensor(
                        coordinator=inv_data["realtime"],
                        inverter=inv_data["inverter"],
                        **defn,
                    )
                )

        entities.append(
            BatteryTimeRemainingSensor(
                hass=hass,
                realtime_coordinator=inv_data["realtime"],
                settings_coordinator=inv_data["settings"],
                inverter=inv_data["inverter"],
                entry=entry,
            )
        )

    async_add_entities(entities)


def _make_device_info(inverter: dict) -> DeviceInfo:
    version = inverter.get("version", {})
    return DeviceInfo(
        identifiers={(DOMAIN, inverter["sn"])},
        name=inverter.get("alias", inverter["sn"]),
        manufacturer=inverter.get("brand", "Sunsynk"),
        model=f"{inverter.get('ratePower', 0) // 1000}kW Hybrid",
        sw_version=version.get("softVer"),
    )


class SunsynkRealtimeSensor(CoordinatorEntity[SunsynkRealtimeCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SunsynkRealtimeCoordinator,
        inverter: dict,
        key: str,
        data_path: str,
        unit: str,
        device_class: str,
        state_class: str,
        icon: str = "mdi:gauge",
    ) -> None:
        super().__init__(coordinator)
        self._inverter = inverter
        self._sn = inverter["sn"]
        self._data_path = data_path
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = DEVICE_CLASS_MAP.get(device_class)
        self._attr_state_class = STATE_CLASS_MAP.get(state_class)
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        return _make_device_info(self._inverter)

    @property
    def native_value(self) -> float | None:
        parts = self._data_path.split(".")
        data = self.coordinator.data
        for part in parts:
            if data is None:
                return None
            data = data.get(part) if isinstance(data, dict) else None
        if data is None:
            return None
        try:
            return float(data)
        except (ValueError, TypeError):
            return None


class BatteryTimeRemainingSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "battery_time_remaining"
    _attr_native_unit_of_measurement = "h"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery-clock-outline"
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        hass: HomeAssistant,
        realtime_coordinator: SunsynkRealtimeCoordinator,
        settings_coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        entry: ConfigEntry,
    ) -> None:
        self._hass = hass
        self._realtime = realtime_coordinator
        self._settings = settings_coordinator
        self._inverter = inverter
        self._sn = inverter["sn"]
        self._entry = entry
        self._attr_unique_id = f"{self._sn}_battery_time_remaining"
        self._unsub_listeners: list = []

    @property
    def device_info(self) -> DeviceInfo:
        return _make_device_info(self._inverter)

    @property
    def _ext_power_entity(self) -> str | None:
        return self._entry.options.get(CONF_BATTERY_POWER_ENTITY)

    @property
    def _ext_soc_entity(self) -> str | None:
        return self._entry.options.get(CONF_BATTERY_SOC_ENTITY)

    @property
    def _capacity_override(self) -> float | None:
        val = self._entry.options.get(CONF_BATTERY_CAPACITY_OVERRIDE)
        if val:
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        return None

    def _get_ext_state(self, entity_id: str) -> float | None:
        state = self._hass.states.get(entity_id)
        if state is None or state.state in ("unavailable", "unknown", ""):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _get_discharge_power(self) -> float | None:
        ext = self._ext_power_entity
        if ext:
            return self._get_ext_state(ext)
        if self._realtime.data:
            flow = self._realtime.data.get("flow", {})
            val = flow.get("battPower")
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
        return None

    def _get_soc(self) -> float | None:
        ext = self._ext_soc_entity
        if ext:
            return self._get_ext_state(ext)
        if self._realtime.data:
            flow = self._realtime.data.get("flow", {})
            val = flow.get("soc")
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
        return None

    def _get_shutdown_soc(self) -> float:
        if self._settings.data:
            val = self._settings.data.get("batteryShutdownCap")
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
        return 0.0

    def _get_capacity_kwh(self) -> float | None:
        override = self._capacity_override
        if override:
            return override
        if self._realtime.data:
            batt = self._realtime.data.get("battery", {})
            cap_str = batt.get("capacity")
            if cap_str is not None:
                try:
                    cap_ah = float(cap_str)
                    bms_volt = batt.get("bmsVolt")
                    if bms_volt:
                        return cap_ah * float(bms_volt) / 1000.0
                    return cap_ah * 51.2 / 1000.0
                except (ValueError, TypeError):
                    pass
        return None

    @property
    def native_value(self) -> float | None:
        discharge_w = self._get_discharge_power()
        soc = self._get_soc()
        capacity_kwh = self._get_capacity_kwh()
        shutdown_soc = self._get_shutdown_soc()

        if discharge_w is None or soc is None or capacity_kwh is None:
            return None

        if discharge_w < MIN_DISCHARGE_W:
            return None

        usable_soc = soc - shutdown_soc
        if usable_soc <= 0:
            return 0.0

        usable_wh = (usable_soc / 100.0) * capacity_kwh * 1000.0
        hours = usable_wh / discharge_w
        return round(hours, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        ext_power = self._ext_power_entity
        ext_soc = self._ext_soc_entity
        if ext_power:
            attrs["power_source"] = ext_power
        if ext_soc:
            attrs["soc_source"] = ext_soc
        cap = self._get_capacity_kwh()
        if cap is not None:
            attrs["capacity_kwh"] = round(cap, 2)
        attrs["shutdown_soc"] = self._get_shutdown_soc()
        return attrs

    async def async_added_to_hass(self) -> None:
        track_entities = []
        ext_power = self._ext_power_entity
        ext_soc = self._ext_soc_entity
        if ext_power:
            track_entities.append(ext_power)
        if ext_soc:
            track_entities.append(ext_soc)

        if track_entities:
            self._unsub_listeners.append(
                async_track_state_change_event(
                    self._hass,
                    track_entities,
                    self._handle_ext_state_change,
                )
            )

        self._unsub_listeners.append(
            self._realtime.async_add_listener(self._handle_coordinator_update)
        )
        self._unsub_listeners.append(
            self._settings.async_add_listener(self._handle_coordinator_update)
        )

    async def async_will_remove_from_hass(self) -> None:
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    @ha_callback
    def _handle_ext_state_change(self, event) -> None:
        self.async_write_ha_state()

    @ha_callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
