import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.sunsynk_cloud.number import SunsynkNumberEntity

from conftest import MOCK_SETTINGS, MOCK_INVERTER


def make_coordinator(settings=None):
    coord = MagicMock()
    coord.data = settings or dict(MOCK_SETTINGS)
    coord.sn = "2601120338"
    coord.async_write_settings = AsyncMock()
    return coord


def test_number_value():
    coord = make_coordinator()
    entity = SunsynkNumberEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="battery_shutdown_soc",
        field="batteryShutdownCap",
        min_value=0,
        max_value=100,
        step=1,
        unit="%",
    )
    assert entity.native_value == 12.0


@pytest.mark.asyncio
async def test_set_value_posts_setting():
    coord = make_coordinator()
    entity = SunsynkNumberEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="battery_shutdown_soc",
        field="batteryShutdownCap",
        min_value=0,
        max_value=100,
        step=1,
        unit="%",
    )
    await entity.async_set_native_value(20)
    coord.async_write_settings.assert_called_once_with(
        {"batteryShutdownCap": "20"}
    )


def test_number_handles_string_values():
    coord = make_coordinator()
    entity = SunsynkNumberEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="max_sell_power",
        field="solarMaxSellPower",
        min_value=0,
        max_value=15000,
        step=100,
        unit="W",
    )
    assert entity.native_value == 15000.0
