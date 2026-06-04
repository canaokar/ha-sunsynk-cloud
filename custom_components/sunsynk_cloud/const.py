from enum import StrEnum

DOMAIN = "sunsynk_cloud"

BASE_URL = "https://api.sunsynk.net"
SOURCE = "sunsynk"

CONF_INVERTER_SNS = "inverter_sns"

DEFAULT_SETTINGS_INTERVAL = 300
DEFAULT_REALTIME_INTERVAL = 60


class WorkMode(StrEnum):
    SELLING_FIRST = "0"
    ZERO_EXPORT = "1"
    LIMITED_TO_HOME = "2"


WORK_MODE_NAMES = {
    WorkMode.SELLING_FIRST: "Selling First",
    WorkMode.ZERO_EXPORT: "Zero Export",
    WorkMode.LIMITED_TO_HOME: "Limited to Home",
}


class EnergyMode(StrEnum):
    BATTERY_FIRST = "0"
    LOAD_FIRST = "1"


ENERGY_MODE_NAMES = {
    EnergyMode.BATTERY_FIRST: "Battery First",
    EnergyMode.LOAD_FIRST: "Load First",
}


BATTERY_SETTINGS = frozenset({
    "battMode", "batteryCap", "batteryMaxCurrentCharge",
    "batteryMaxCurrentDischarge", "batteryShutdownCap", "batteryRestartCap",
    "batteryLowCap", "batteryOn", "batteryEmptyV", "batteryImpedance",
    "batteryEfficiency", "lithiumMode", "bmsErrStop", "chargeVolt",
    "floatVolt", "absorptionVolt", "chargeCurrent", "dischargeCurrent",
})

CONF_BATTERY_POWER_ENTITY = "battery_power_entity"
CONF_BATTERY_SOC_ENTITY = "battery_soc_entity"
CONF_BATTERY_CAPACITY_OVERRIDE = "battery_capacity_kwh"

GRID_CHARGE_SETTINGS = frozenset({
    "sdChargeOn", "sdStartCap", "sdBatteryCurrent", "sdStartVolt",
    "gridSignal", "gridAlwaysOn",
})
