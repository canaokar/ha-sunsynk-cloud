import pytest
from unittest.mock import MagicMock, patch

from custom_components.sunsynk_cloud.sensor import BatteryTimeRemainingSensor

from conftest import MOCK_INVERTER, MOCK_FLOW, MOCK_GRID, MOCK_BATTERY, MOCK_LOAD, MOCK_SETTINGS


def make_coordinators(flow=None, battery=None, settings=None):
    realtime = MagicMock()
    realtime.data = {
        "flow": flow or dict(MOCK_FLOW),
        "grid": dict(MOCK_GRID),
        "battery": battery or dict(MOCK_BATTERY),
        "load": dict(MOCK_LOAD),
    }
    realtime.async_add_listener = MagicMock(return_value=lambda: None)

    settings_coord = MagicMock()
    settings_coord.data = settings or dict(MOCK_SETTINGS)
    settings_coord.async_add_listener = MagicMock(return_value=lambda: None)

    return realtime, settings_coord


def make_entry(options=None):
    entry = MagicMock()
    entry.options = options or {}
    return entry


def make_sensor(flow=None, battery=None, settings=None, options=None):
    realtime, settings_coord = make_coordinators(flow, battery, settings)
    entry = make_entry(options)
    hass = MagicMock()
    return BatteryTimeRemainingSensor(
        hass=hass,
        realtime_coordinator=realtime,
        settings_coordinator=settings_coord,
        inverter=MOCK_INVERTER,
        entry=entry,
    )


def test_basic_discharge_calculation():
    flow = dict(MOCK_FLOW)
    flow["battPower"] = 1000
    flow["soc"] = 50.0
    battery = dict(MOCK_BATTERY)
    battery["capacity"] = "100.0"
    battery["bmsVolt"] = 51.2
    settings = dict(MOCK_SETTINGS)
    settings["batteryShutdownCap"] = "10"

    sensor = make_sensor(flow=flow, battery=battery, settings=settings)
    val = sensor.native_value

    # usable_soc = 50 - 10 = 40%
    # capacity = 100Ah * 51.2V = 5120Wh = 5.12kWh
    # usable_wh = 40% * 5120 = 2048Wh
    # hours = 2048 / 1000 = 2.048
    assert val == pytest.approx(2.05, abs=0.01)


def test_returns_none_when_not_discharging():
    flow = dict(MOCK_FLOW)
    flow["battPower"] = 0
    sensor = make_sensor(flow=flow)
    assert sensor.native_value is None


def test_returns_none_when_low_discharge():
    flow = dict(MOCK_FLOW)
    flow["battPower"] = 30
    sensor = make_sensor(flow=flow)
    assert sensor.native_value is None


def test_returns_zero_when_soc_at_shutdown():
    flow = dict(MOCK_FLOW)
    flow["battPower"] = 500
    flow["soc"] = 12.0
    settings = dict(MOCK_SETTINGS)
    settings["batteryShutdownCap"] = "12"

    sensor = make_sensor(flow=flow, settings=settings)
    assert sensor.native_value == 0.0


def test_returns_zero_when_soc_below_shutdown():
    flow = dict(MOCK_FLOW)
    flow["battPower"] = 500
    flow["soc"] = 10.0
    settings = dict(MOCK_SETTINGS)
    settings["batteryShutdownCap"] = "12"

    sensor = make_sensor(flow=flow, settings=settings)
    assert sensor.native_value == 0.0


def test_capacity_override_from_options():
    flow = dict(MOCK_FLOW)
    flow["battPower"] = 1000
    flow["soc"] = 50.0
    settings = dict(MOCK_SETTINGS)
    settings["batteryShutdownCap"] = "0"

    sensor = make_sensor(
        flow=flow,
        settings=settings,
        options={"battery_capacity_kwh": "10.0"},
    )
    val = sensor.native_value
    # usable = 50% * 10kWh * 1000 = 5000Wh, 5000/1000 = 5.0h
    assert val == pytest.approx(5.0, abs=0.01)


def test_external_entity_for_power():
    flow = dict(MOCK_FLOW)
    flow["battPower"] = 9999
    flow["soc"] = 50.0
    battery = dict(MOCK_BATTERY)
    battery["capacity"] = "100.0"
    battery["bmsVolt"] = 51.2
    settings = dict(MOCK_SETTINGS)
    settings["batteryShutdownCap"] = "0"

    sensor = make_sensor(
        flow=flow,
        battery=battery,
        settings=settings,
        options={"battery_power_entity": "sensor.kellerza_battery_power"},
    )

    mock_state = MagicMock()
    mock_state.state = "500"
    sensor._hass.states.get.return_value = mock_state

    val = sensor.native_value
    # Uses external entity (500W) not flow.battPower (9999W)
    # capacity = 100*51.2 = 5120Wh, usable = 50% = 2560Wh
    # 2560/500 = 5.12h
    assert val == pytest.approx(5.12, abs=0.01)


def test_extra_attributes():
    flow = dict(MOCK_FLOW)
    flow["battPower"] = 500
    battery = dict(MOCK_BATTERY)
    battery["capacity"] = "100.0"
    battery["bmsVolt"] = 51.2
    settings = dict(MOCK_SETTINGS)
    settings["batteryShutdownCap"] = "12"

    sensor = make_sensor(
        flow=flow,
        battery=battery,
        settings=settings,
        options={"battery_power_entity": "sensor.kellerza_batt"},
    )
    attrs = sensor.extra_state_attributes
    assert attrs["shutdown_soc"] == 12.0
    assert attrs["power_source"] == "sensor.kellerza_batt"
    assert "capacity_kwh" in attrs
