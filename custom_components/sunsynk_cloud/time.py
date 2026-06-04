from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SunsynkSettingsCoordinator
from .entity import SunsynkEntity

TIMER_SLOTS = range(1, 7)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for sn, inv_data in data["coordinators"].items():
        for n in TIMER_SLOTS:
            entities.append(
                SunsynkTimeEntity(
                    coordinator=inv_data["settings"],
                    inverter=inv_data["inverter"],
                    key=f"timer_{n}_end_time",
                    field=f"sellTime{n}",
                )
            )
    async_add_entities(entities)


class SunsynkTimeEntity(SunsynkEntity, TimeEntity):
    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        key: str,
        field: str,
    ) -> None:
        super().__init__(coordinator, inverter)
        self._field = field
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> time | None:
        val = self.coordinator.data.get(self._field)
        if not val:
            return None
        try:
            h, m = val.split(":")
            return time(int(h), int(m))
        except (ValueError, AttributeError):
            return None

    async def async_set_value(self, value: time) -> None:
        time_str = f"{value.hour:02d}:{value.minute:02d}"
        await self.coordinator.async_write_settings({self._field: time_str})
