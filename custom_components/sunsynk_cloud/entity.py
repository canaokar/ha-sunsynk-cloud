from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SunsynkSettingsCoordinator


class SunsynkEntity(CoordinatorEntity[SunsynkSettingsCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
    ) -> None:
        super().__init__(coordinator)
        self._inverter = inverter
        self._sn = inverter["sn"]

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
