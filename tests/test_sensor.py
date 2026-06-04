import pytest
from unittest.mock import MagicMock

from custom_components.sunsynk_cloud.sensor import SunsynkRealtimeSensor

from conftest import MOCK_INVERTER, MOCK_FLOW, MOCK_GRID, MOCK_BATTERY, MOCK_LOAD


def make_realtime_coordinator():
    coord = MagicMock()
    coord.data = {
        "flow": MOCK_FLOW,
        "grid": MOCK_GRID,
        "battery": MOCK_BATTERY,
        "load": MOCK_LOAD,
    }
    coord.sn = "2601120338"
    return coord


def test_pv_power_sensor():
    coord = make_realtime_coordinator()
    entity = SunsynkRealtimeSensor(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="pv_power",
        data_path="flow.pvPower",
        unit="W",
        device_class="power",
        state_class="measurement",
    )
    assert entity.native_value == 5566


def test_battery_soc_sensor():
    coord = make_realtime_coordinator()
    entity = SunsynkRealtimeSensor(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="battery_soc",
        data_path="flow.soc",
        unit="%",
        device_class="battery",
        state_class="measurement",
    )
    assert entity.native_value == 41.0


def test_daily_grid_import():
    coord = make_realtime_coordinator()
    entity = SunsynkRealtimeSensor(
        coordinator=coord,
        inverter=MOCK_INVERTER,
        key="daily_grid_import",
        data_path="grid.etodayFrom",
        unit="kWh",
        device_class="energy",
        state_class="total_increasing",
    )
    assert entity.native_value == 36.6
