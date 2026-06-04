from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SunsynkSettingsCoordinator
from .entity import SunsynkEntity

SWITCH_DEFINITIONS = [
    {"key": "solar_sell", "field": "solarSell", "on_value": "1", "off_value": "0", "icon": "mdi:solar-power-variant"},
    {"key": "grid_charge", "field": "sdChargeOn", "on_value": "1", "off_value": "0", "icon": "mdi:transmission-tower"},
    {"key": "peak_and_valley", "field": "peakAndVallery", "on_value": "1", "off_value": "0", "icon": "mdi:clock-outline"},
    {"key": "grid_peak_shaving", "field": "gridPeakShaving", "on_value": "1", "off_value": "0", "icon": "mdi:chart-bell-curve-cumulative"},
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for sn, inv_data in data["coordinators"].items():
        for defn in SWITCH_DEFINITIONS:
            entities.append(
                SunsynkSwitchEntity(
                    coordinator=inv_data["settings"],
                    inverter=inv_data["inverter"],
                    **defn,
                )
            )
    async_add_entities(entities)


class SunsynkSwitchEntity(SunsynkEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        key: str,
        field: str,
        on_value: str,
        off_value: str,
        icon: str = "mdi:toggle-switch",
    ) -> None:
        super().__init__(coordinator, inverter)
        self._field = field
        self._on_value = on_value
        self._off_value = off_value
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.data.get(self._field)
        if val is None:
            return None
        return str(val).lower() == self._on_value.lower()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_settings(
            {self._field: self._on_value}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_settings(
            {self._field: self._off_value}
        )
