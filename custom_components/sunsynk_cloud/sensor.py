from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SunsynkRealtimeCoordinator

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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    if not entry.options.get("enable_realtime", True):
        return

    entities = []
    for sn, inv_data in data["coordinators"].items():
        for defn in SENSOR_DEFINITIONS:
            entities.append(
                SunsynkRealtimeSensor(
                    coordinator=inv_data["realtime"],
                    inverter=inv_data["inverter"],
                    **defn,
                )
            )
    async_add_entities(entities)


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
        version = self._inverter.get("version", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._sn)},
            name=self._inverter.get("alias", self._sn),
            manufacturer=self._inverter.get("brand", "Sunsynk"),
            model=f"{self._inverter.get('ratePower', 0) // 1000}kW Hybrid",
            sw_version=version.get("softVer"),
        )

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
