import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import time

from custom_components.sunsynk_cloud.time import SunsynkTimeEntity

from conftest import MOCK_SETTINGS, MOCK_INVERTER


def make_coordinator(settings=None):
    coord = MagicMock()
    coord.data = settings or dict(MOCK_SETTINGS)
    coord.sn = "2601120338"
    coord.async_write_settings = AsyncMock()
    return coord


def test_time_value():
    coord = make_coordinator()
    entity = SunsynkTimeEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="timer_2_end_time",
        field="sellTime2",
    )
    assert entity.native_value == time(6, 0)


@pytest.mark.asyncio
async def test_set_time():
    coord = make_coordinator()
    entity = SunsynkTimeEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="timer_1_end_time",
        field="sellTime1",
    )
    await entity.async_set_value(time(5, 30))
    coord.async_write_settings.assert_called_once_with({"sellTime1": "05:30"})
