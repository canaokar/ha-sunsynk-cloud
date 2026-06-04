import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import SunsynkApi, AuthError
from .const import (
    DOMAIN,
    CONF_INVERTER_SNS,
    DEFAULT_SETTINGS_INTERVAL,
    DEFAULT_REALTIME_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class SunsynkCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._username: str = ""
        self._password: str = ""
        self._plants: list[dict] = []
        self._inverters: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input["username"]
            self._password = user_input["password"]

            await self.async_set_unique_id(self._username.lower())
            self._abort_if_unique_id_configured()

            try:
                session = aiohttp.ClientSession()
                api = SunsynkApi(session)
                await api.authenticate(self._username, self._password)
                self._plants = await api.get_plants()
                for plant in self._plants:
                    invs = await api.get_inverters(plant["id"])
                    self._inverters.extend(invs)
                await session.close()
            except AuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"

            if not errors:
                if len(self._inverters) == 1:
                    return self._create_entry([self._inverters[0]["sn"]])
                if len(self._inverters) > 1:
                    return await self.async_step_select_inverters()
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("username"): str,
                vol.Required("password"): str,
            }),
            errors=errors,
        )

    async def async_step_select_inverters(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self._create_entry(user_input[CONF_INVERTER_SNS])

        options = {
            inv["sn"]: f"{inv.get('alias', inv['sn'])} ({inv.get('brand', 'Unknown')})"
            for inv in self._inverters
        }
        return self.async_show_form(
            step_id="select_inverters",
            data_schema=vol.Schema({
                vol.Required(CONF_INVERTER_SNS): vol.All(
                    vol.Coerce(list), [vol.In(options)]
                ),
            }),
        )

    def _create_entry(self, sns: list[str]) -> FlowResult:
        selected = [inv for inv in self._inverters if inv["sn"] in sns]
        return self.async_create_entry(
            title=self._username,
            data={
                "username": self._username,
                "password": self._password,
                "inverters": selected,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SunsynkCloudOptionsFlow(config_entry)

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        return await self.async_step_user()


class SunsynkCloudOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self._config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "settings_interval",
                    default=current.get(
                        "settings_interval", DEFAULT_SETTINGS_INTERVAL
                    ),
                ): vol.All(int, vol.Range(min=60, max=900)),
                vol.Optional(
                    "realtime_interval",
                    default=current.get(
                        "realtime_interval", DEFAULT_REALTIME_INTERVAL
                    ),
                ): vol.All(int, vol.Range(min=30, max=300)),
                vol.Optional(
                    "enable_realtime",
                    default=current.get("enable_realtime", True),
                ): bool,
            }),
        )
