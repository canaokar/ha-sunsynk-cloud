from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SunsynkSettingsCoordinator
from .entity import SunsynkEntity

NUMBER_DEFINITIONS = [
    {"key": "max_sell_power", "field": "solarMaxSellPower", "min_value": 0, "max_value": 15000, "step": 100, "unit": "W", "icon": "mdi:transmission-tower-export"},
    {"key": "zero_export_power", "field": "zeroExportPower", "min_value": 0, "max_value": 500, "step": 10, "unit": "W", "icon": "mdi:transmission-tower-off"},
    {"key": "grid_charge_soc", "field": "sdStartCap", "min_value": 10, "max_value": 90, "step": 1, "unit": "%", "icon": "mdi:battery-charging-40"},
    {"key": "grid_charge_current", "field": "sdBatteryCurrent", "min_value": 0, "max_value": 275, "step": 5, "unit": "A", "icon": "mdi:current-ac"},
    {"key": "battery_shutdown_soc", "field": "batteryShutdownCap", "min_value": 0, "max_value": 100, "step": 1, "unit": "%", "icon": "mdi:battery-alert"},
    {"key": "battery_restart_soc", "field": "batteryRestartCap", "min_value": 0, "max_value": 100, "step": 1, "unit": "%", "icon": "mdi:battery-plus"},
    {"key": "battery_low_soc", "field": "batteryLowCap", "min_value": 0, "max_value": 100, "step": 1, "unit": "%", "icon": "mdi:battery-low"},
    {"key": "max_charge_current", "field": "batteryMaxCurrentCharge", "min_value": 0, "max_value": 280, "step": 5, "unit": "A", "icon": "mdi:battery-charging"},
    {"key": "max_discharge_current", "field": "batteryMaxCurrentDischarge", "min_value": 0, "max_value": 280, "step": 5, "unit": "A", "icon": "mdi:battery-minus"},
    {"key": "grid_peak_power", "field": "gridPeakPower", "min_value": 0, "max_value": 15000, "step": 100, "unit": "W", "icon": "mdi:flash-alert"},
    {"key": "import_power_limit", "field": "importPower", "min_value": 0, "max_value": 15000, "step": 100, "unit": "W", "icon": "mdi:transmission-tower-import"},
    {"key": "ac_output_power_limit", "field": "acOutputPowerLimit", "min_value": 0, "max_value": 15000, "step": 100, "unit": "W", "icon": "mdi:power-plug"},
]

for _n in range(1, 7):
    NUMBER_DEFINITIONS.append(
        {"key": f"timer_{_n}_power", "field": f"sellTime{_n}Pac", "min_value": 0, "max_value": 10000, "step": 100, "unit": "W", "icon": "mdi:flash"}
    )
    NUMBER_DEFINITIONS.append(
        {"key": f"timer_{_n}_soc", "field": f"cap{_n}", "min_value": 0, "max_value": 100, "step": 1, "unit": "%", "icon": "mdi:battery-charging-outline"}
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for sn, inv_data in data["coordinators"].items():
        for defn in NUMBER_DEFINITIONS:
            entities.append(
                SunsynkNumberEntity(
                    coordinator=inv_data["settings"],
                    inverter=inv_data["inverter"],
                    **defn,
                )
            )
    async_add_entities(entities)


class SunsynkNumberEntity(SunsynkEntity, NumberEntity):
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        key: str,
        field: str,
        min_value: float,
        max_value: float,
        step: float,
        unit: str,
        icon: str = "mdi:cog",
    ) -> None:
        super().__init__(coordinator, inverter)
        self._field = field
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data.get(self._field)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_settings(
            {self._field: str(int(value))}
        )
