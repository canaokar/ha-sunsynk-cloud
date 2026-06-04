import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.sunsynk_cloud.select import SunsynkSelectEntity
from custom_components.sunsynk_cloud.const import WORK_MODE_NAMES, ENERGY_MODE_NAMES

from conftest import MOCK_SETTINGS, MOCK_INVERTER


def make_coordinator(settings=None):
    coord = MagicMock()
    coord.data = settings or dict(MOCK_SETTINGS)
    coord.sn = "2601120338"
    coord.async_write_settings = AsyncMock()
    return coord


def test_work_mode_current_option():
    coord = make_coordinator()
    entity = SunsynkSelectEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="work_mode",
        field="sysWorkMode",
        options_map=WORK_MODE_NAMES,
    )
    assert entity.current_option == "Limited to Home"


def test_energy_mode_current_option():
    coord = make_coordinator()
    entity = SunsynkSelectEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="energy_mode",
        field="energyMode",
        options_map=ENERGY_MODE_NAMES,
    )
    assert entity.current_option == "Load First"


@pytest.mark.asyncio
async def test_select_option_posts_setting():
    coord = make_coordinator()
    entity = SunsynkSelectEntity(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="work_mode",
        field="sysWorkMode",
        options_map=WORK_MODE_NAMES,
    )
    await entity.async_select_option("Zero Export")
    coord.async_write_settings.assert_called_once_with({"sysWorkMode": "1"})
