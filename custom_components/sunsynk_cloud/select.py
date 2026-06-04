from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WORK_MODE_NAMES, ENERGY_MODE_NAMES
from .coordinator import SunsynkSettingsCoordinator
from .entity import SunsynkEntity

SELECT_DEFINITIONS = [
    {
        "key": "work_mode",
        "field": "sysWorkMode",
        "options_map": WORK_MODE_NAMES,
        "icon": "mdi:solar-power",
    },
    {
        "key": "energy_mode",
        "field": "energyMode",
        "options_map": ENERGY_MODE_NAMES,
        "icon": "mdi:battery-charging",
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for sn, inv_data in data["coordinators"].items():
        for defn in SELECT_DEFINITIONS:
            entities.append(
                SunsynkSelectEntity(
                    coordinator=inv_data["settings"],
                    inverter=inv_data["inverter"],
                    **defn,
                )
            )
    async_add_entities(entities)


class SunsynkSelectEntity(SunsynkEntity, SelectEntity):
    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        key: str,
        field: str,
        options_map: dict[str, str],
        icon: str = "mdi:cog",
    ) -> None:
        super().__init__(coordinator, inverter)
        self._field = field
        self._options_map = options_map
        self._reverse_map = {v: k for k, v in options_map.items()}
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_icon = icon
        self._attr_options = list(options_map.values())

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.data.get(self._field)
        return self._options_map.get(val)

    async def async_select_option(self, option: str) -> None:
        api_val = self._reverse_map[option]
        await self.coordinator.async_write_settings({self._field: api_val})
