import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.sunsynk_cloud.api import AuthError
from custom_components.sunsynk_cloud.const import DOMAIN

from conftest import MOCK_PLANT, MOCK_INVERTER


@pytest.fixture
def mock_setup_entry():
    with patch(
        "custom_components.sunsynk_cloud.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


async def test_flow_user_step_success(hass, enable_custom_integrations, mock_setup_entry):
    with patch(
        "custom_components.sunsynk_cloud.config_flow.SunsynkApi"
    ) as MockApi:
        api = MockApi.return_value
        api.authenticate = AsyncMock()
        api.get_plants = AsyncMock(return_value=[MOCK_PLANT])
        api.get_inverters = AsyncMock(return_value=[MOCK_INVERTER])

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test@test.com", "password": "pass123"},
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "test@test.com"
        assert result["data"]["username"] == "test@test.com"
        assert result["data"]["inverters"] == [MOCK_INVERTER]


async def test_flow_invalid_auth(hass, enable_custom_integrations):
    with patch(
        "custom_components.sunsynk_cloud.config_flow.SunsynkApi"
    ) as MockApi:
        api = MockApi.return_value
        api.authenticate = AsyncMock(
            side_effect=AuthError("Bad credentials")
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test@test.com", "password": "wrong"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "invalid_auth"
