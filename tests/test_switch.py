import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.sunsynk_cloud.switch import SunsynkSwitchEntity

from conftest import MOCK_SETTINGS, MOCK_INVERTER


def make_coordinator(settings=None):
    coord = MagicMock()
    coord.data = settings or dict(MOCK_SETTINGS)
    coord.sn = "2601120338"
    coord.async_write_settings = AsyncMock()
    return coord


def test_switch_is_on_numeric():
    coord = make_coordinator()
    entity = SunsynkSwitchEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="solar_sell",
        field="solarSell",
        on_value="1",
        off_value="0",
    )
    assert entity.is_on is True


def test_switch_is_off_numeric():
    coord = make_coordinator({"gridPeakShaving": "0"})
    entity = SunsynkSwitchEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="grid_peak_shaving",
        field="gridPeakShaving",
        on_value="1",
        off_value="0",
    )
    assert entity.is_on is False


@pytest.mark.asyncio
async def test_turn_on():
    coord = make_coordinator()
    entity = SunsynkSwitchEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="grid_peak_shaving",
        field="gridPeakShaving",
        on_value="1",
        off_value="0",
    )
    await entity.async_turn_on()
    coord.async_write_settings.assert_called_once_with({"gridPeakShaving": "1"})


@pytest.mark.asyncio
async def test_turn_off():
    coord = make_coordinator()
    entity = SunsynkSwitchEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="solar_sell",
        field="solarSell",
        on_value="1",
        off_value="0",
    )
    await entity.async_turn_off()
    coord.async_write_settings.assert_called_once_with({"solarSell": "0"})


def test_switch_handles_true_false_strings():
    coord = make_coordinator({"time1on": "true"})
    entity = SunsynkSwitchEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="timer_1_grid_charge",
        field="time1on",
        on_value="true",
        off_value="false",
    )
    assert entity.is_on is True
