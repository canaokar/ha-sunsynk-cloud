import pytest
from unittest.mock import AsyncMock, patch
from datetime import timedelta

from custom_components.sunsynk_cloud.coordinator import (
    SunsynkSettingsCoordinator,
)


async def test_settings_coordinator_fetches_data(hass, mock_api):
    coordinator = SunsynkSettingsCoordinator(
        hass, mock_api, "2601120338", update_interval=timedelta(seconds=300)
    )
    data = await coordinator._async_update_data()
    mock_api.get_settings.assert_called_once_with("2601120338")
    assert data["sysWorkMode"] == "2"


async def test_settings_coordinator_write_posts_settings(hass, mock_api):
    coordinator = SunsynkSettingsCoordinator(
        hass, mock_api, "2601120338", update_interval=timedelta(seconds=300)
    )
    coordinator.data = {"sysWorkMode": "2", "solarSell": "1"}

    with patch.object(coordinator, "_flush_writes", new_callable=AsyncMock) as mock_flush:
        await coordinator.async_write_settings({"solarSell": "0"})
        assert coordinator._pending_writes == {"solarSell": "0"}


async def test_flush_writes_calls_api(hass, mock_api):
    coordinator = SunsynkSettingsCoordinator(
        hass, mock_api, "2601120338", update_interval=timedelta(seconds=300)
    )
    coordinator._pending_writes = {"solarSell": "0"}

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with patch.object(coordinator, "async_request_refresh", new_callable=AsyncMock):
            await coordinator._flush_writes()

    mock_api.post_settings.assert_called_once_with(
        "2601120338", {"solarSell": "0"}
    )
    assert coordinator._pending_writes == {}
