from unittest.mock import AsyncMock, patch
import pytest

MOCK_SETTINGS = {
    "sn": "2601120338",
    "sysWorkMode": "2",
    "energyMode": "1",
    "peakAndVallery": "1",
    "solarSell": "1",
    "solarMaxSellPower": "15000",
    "zeroExportPower": "20",
    "sdChargeOn": "1",
    "sdStartCap": "30",
    "sdBatteryCurrent": "220",
    "batteryShutdownCap": "12",
    "batteryRestartCap": "25",
    "batteryLowCap": "20",
    "batteryMaxCurrentCharge": "220",
    "batteryMaxCurrentDischarge": "220",
    "gridPeakShaving": "0",
    "gridPeakPower": "8000",
    "importPower": "14950",
    "acOutputPowerLimit": "10000",
    "sellTime1": "00:00",
    "sellTime2": "06:00",
    "sellTime3": "11:00",
    "sellTime4": "16:00",
    "sellTime5": "21:00",
    "sellTime6": "23:00",
    "sellTime1Pac": "10000",
    "sellTime2Pac": "500",
    "sellTime3Pac": "500",
    "sellTime4Pac": "500",
    "sellTime5Pac": "500",
    "sellTime6Pac": "10000",
    "sellTime1En": "0",
    "sellTime2En": "0",
    "sellTime3En": "1",
    "sellTime4En": "1",
    "sellTime5En": "1",
    "sellTime6En": "0",
    "cap1": "100",
    "cap2": "70",
    "cap3": "20",
    "cap4": "20",
    "cap5": "20",
    "cap6": "100",
    "time1on": "true",
    "time2on": "false",
    "time3on": "false",
    "time4on": "false",
    "time5on": "false",
    "time6on": "true",
    "mondayOn": "true",
    "tuesdayOn": "true",
    "wednesdayOn": "true",
    "thursdayOn": "true",
    "fridayOn": "true",
    "saturdayOn": "true",
    "sundayOn": "true",
}

MOCK_FLOW = {
    "pvPower": 5566,
    "battPower": 476,
    "gridOrMeterPower": -5160,
    "loadOrEpsPower": 700,
    "soc": 41.0,
    "pvTo": True,
    "toGrid": True,
    "toBat": False,
    "batTo": True,
    "gridTo": False,
    "existsGrid": True,
}

MOCK_GRID = {
    "pac": -5160,
    "fac": 50.03,
    "pf": 1.0,
    "acRealyStatus": 1,
    "etodayFrom": "36.6",
    "etodayTo": "41.5",
    "etotalFrom": "215.2",
    "etotalTo": "655.7",
}

MOCK_BATTERY = {
    "power": 476,
    "soc": "41.0",
    "bmsSoc": 40.0,
    "bmsVolt": 52.61,
    "bmsCurrent": -11.0,
    "bmsTemp": 26.7,
    "capacity": "628.0",
    "etodayChg": "33.2",
    "etodayDischg": "31.3",
}

MOCK_LOAD = {
    "totalPower": 700,
    "dailyUsed": 20.9,
    "totalUsed": 441.5,
}

MOCK_INVERTER = {
    "id": 284284,
    "sn": "2601120338",
    "alias": "2601120338",
    "gsn": "E47W25A05539",
    "status": 1,
    "type": 2,
    "pac": 5566,
    "etoday": 32.4,
    "etotal": 968.7,
    "ratePower": 10000,
    "brand": "Deye",
    "version": {
        "masterVer": "B.0.2.9",
        "softVer": "1.7.2.7",
        "hmiVer": "E.4.3.E",
    },
    "plant": {"id": 537602, "name": "66 Hartscroft"},
    "sunsynkEquip": True,
    "protocolIdentifier": "2",
    "equipType": 2,
    "pvNum": 3,
}

MOCK_PLANT = {
    "id": 537602,
    "name": "66 Hartscroft",
    "status": 1,
    "type": 2,
    "pac": 5566,
}


@pytest.fixture
def mock_api():
    with patch("custom_components.sunsynk_cloud.api.SunsynkApi") as mock_cls:
        api = mock_cls.return_value
        api.authenticate = AsyncMock(return_value="fake_token")
        api.get_plants = AsyncMock(return_value=[MOCK_PLANT])
        api.get_inverters = AsyncMock(return_value=[MOCK_INVERTER])
        api.get_settings = AsyncMock(return_value=MOCK_SETTINGS)
        api.post_settings = AsyncMock(return_value=True)
        api.get_flow = AsyncMock(return_value=MOCK_FLOW)
        api.get_grid_realtime = AsyncMock(return_value=MOCK_GRID)
        api.get_battery_realtime = AsyncMock(return_value=MOCK_BATTERY)
        api.get_load_realtime = AsyncMock(return_value=MOCK_LOAD)
        yield api
