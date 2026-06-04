import logging
from datetime import timedelta

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SunsynkApi, AuthError
from .const import (
    DOMAIN,
    DEFAULT_SETTINGS_INTERVAL,
    DEFAULT_REALTIME_INTERVAL,
)
from .coordinator import SunsynkSettingsCoordinator, SunsynkRealtimeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["select", "number", "switch", "sensor", "time"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    api = SunsynkApi(session)

    try:
        await api.authenticate(entry.data["username"], entry.data["password"])
    except AuthError as err:
        raise ConfigEntryAuthFailed(
            "Login failed — check credentials"
        ) from err

    settings_interval = timedelta(
        seconds=entry.options.get("settings_interval", DEFAULT_SETTINGS_INTERVAL)
    )
    realtime_interval = timedelta(
        seconds=entry.options.get("realtime_interval", DEFAULT_REALTIME_INTERVAL)
    )

    coordinators: dict[str, dict] = {}
    inverters = entry.data["inverters"]

    for inv in inverters:
        sn = inv["sn"]
        settings_coord = SunsynkSettingsCoordinator(
            hass, api, sn, settings_interval
        )
        await settings_coord.async_config_entry_first_refresh()

        realtime_coord = SunsynkRealtimeCoordinator(
            hass, api, sn, realtime_interval
        )
        if entry.options.get("enable_realtime", True):
            await realtime_coord.async_config_entry_first_refresh()

        coordinators[sn] = {
            "settings": settings_coord,
            "realtime": realtime_coord,
            "inverter": inv,
        }

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
    }

    card_path = hass.config.path(
        "custom_components/sunsynk_cloud/card/sunsynk-cloud-card.js"
    )
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/sunsynk_cloud/sunsynk-cloud-card.js",
            card_path,
            True,
        )
    ])

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
