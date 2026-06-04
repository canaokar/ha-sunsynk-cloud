import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SunsynkApi

_LOGGER = logging.getLogger(__name__)


class SunsynkSettingsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: SunsynkApi,
        sn: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"sunsynk_settings_{sn}",
            update_interval=update_interval,
        )
        self.api = api
        self.sn = sn
        self._write_lock = asyncio.Lock()
        self._pending_writes: dict[str, str] = {}
        self._debounce_task: asyncio.Task | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        return await self.api.get_settings(self.sn)

    async def async_write_settings(self, settings: dict[str, str]) -> None:
        async with self._write_lock:
            self._pending_writes.update(settings)
            if self._debounce_task and not self._debounce_task.done():
                self._debounce_task.cancel()
            self._debounce_task = asyncio.ensure_future(
                self._flush_writes()
            )

    async def _flush_writes(self) -> None:
        await asyncio.sleep(2)
        async with self._write_lock:
            if not self._pending_writes:
                return
            writes = dict(self._pending_writes)
            self._pending_writes.clear()

        await self.api.post_settings(self.sn, writes)
        await asyncio.sleep(30)
        await self.async_request_refresh()


class SunsynkRealtimeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: SunsynkApi,
        sn: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"sunsynk_realtime_{sn}",
            update_interval=update_interval,
        )
        self.api = api
        self.sn = sn

    async def _async_update_data(self) -> dict[str, Any]:
        flow, grid, battery, load = await asyncio.gather(
            self.api.get_flow(self.sn),
            self.api.get_grid_realtime(self.sn),
            self.api.get_battery_realtime(self.sn),
            self.api.get_load_realtime(self.sn),
        )
        return {
            "flow": flow,
            "grid": grid,
            "battery": battery,
            "load": load,
        }
