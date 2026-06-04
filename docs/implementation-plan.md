# ha-sunsynk-cloud Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a HACS integration that exposes Sunsynk/Deye inverter settings as writable HA entities, plus a custom Lovelace card with visual timer editor.

**Architecture:** Python async integration using HA's DataUpdateCoordinator pattern, aiohttp for cloud API calls, RSA-encrypted auth. Two coordinators (settings @ 5min, realtime @ 60s). TypeScript + LitElement Lovelace card bundled with Rollup.

**Tech Stack:** Python 3.12+, aiohttp, cryptography (RSA), Home Assistant 2024.1+, TypeScript, Lit 3, Rollup

**Reference files:**
- `docs/design.md` — full design spec with entity tables, write safety rules, card layout
- `sunsynk-api.yaml` — OpenAPI 3.0 spec with all 251 endpoints, validated response schemas
- `auth_example.py` — working sync auth flow (reference for porting to async)

---

## Project Context

This plan is self-contained. Each phase can be executed in a fresh session with no prior conversation context — just read this file and the reference files listed above.

### What this project is

A HACS custom integration for Home Assistant that talks to the Sunsynk cloud API (`api.sunsynk.net`) to read and write inverter settings. The user already has kellerza's add-on for local Modbus reads — this integration supplements it by adding cloud-based settings control and a custom Lovelace card.

### Key API details

- **Base URL:** `https://api.sunsynk.net`
- **Auth flow:** `GET /anonymous/publicKey` → RSA PKCS1v15 encrypt password → `POST /oauth/token/new` → Bearer token (expires in ~7 days)
- **Read settings:** `GET /api/v1/common/setting/{sn}/read` → returns 300+ fields as string values
- **Write settings:** `POST /api/v1/common/setting/{sn}/set` → send only changed fields as JSON body
- **Write safety constraint:** Battery fields and system mode fields must NEVER be mixed in a single POST — the API rejects or corrupts them. See `BATTERY_SETTINGS` and `GRID_CHARGE_SETTINGS` sets in `const.py`.
- **All setting values are strings** in both directions (e.g. `"1"` not `1`, `"true"` not `true`).

### Test inverter (for integration testing)

- **Inverter SN:** `2601120338` (Deye 10kW hybrid, 3 PV strings)
- **Gateway SN:** `E47W25A05539` (Wi-Fi)
- **Plant ID:** `537602`
- **Brand:** Deye
- **Settings endpoint:** `common/setting` (the gy/mt/sunsynk-store endpoints return "No Permissions" for this inverter type)

### Repository

- **Repo:** `https://github.com/canaokar/ha-sunsynk-cloud.git` (origin already configured)
- **Branch:** `main`
- **License:** MIT
- **No AI attribution** in commits, code, or docs.

---

## File Structure

```
ha-sunsynk-cloud/
├── custom_components/sunsynk_cloud/
│   ├── __init__.py              Integration setup, platform forwarding
│   ├── api.py                   Async API client (auth, GET, POST, token refresh)
│   ├── config_flow.py           Config flow UI + options flow + re-auth
│   ├── coordinator.py           Settings + realtime coordinators
│   ├── const.py                 Domain, field definitions, enums, category groups
│   ├── entity.py                Base entity class with shared device_info
│   ├── sensor.py                Read-only sensor entities
│   ├── number.py                Writable number entities
│   ├── select.py                Writable select entities
│   ├── switch.py                Writable switch entities
│   ├── time.py                  Writable time entities (timer slots)
│   ├── manifest.json            Integration manifest for HA/HACS
│   ├── strings.json             Config flow UI strings
│   └── translations/
│       └── en.json              English translations
├── card/
│   ├── package.json             Node dependencies (lit, rollup, typescript)
│   ├── tsconfig.json            TypeScript config
│   ├── rollup.config.mjs        Rollup bundler config
│   └── src/
│       ├── sunsynk-cloud-card.ts    Main card entry point
│       ├── components/
│       │   ├── status-header.ts     Live power flow header
│       │   ├── settings-section.ts  Work mode / general settings
│       │   ├── battery-section.ts   Battery settings panel
│       │   ├── grid-section.ts      Grid settings panel
│       │   ├── timer-timeline.ts    Visual 24h timeline bar
│       │   └── timer-dialog.ts      Slot edit popup
│       ├── styles.ts                Shared CSS
│       └── types.ts                 TypeScript interfaces
├── tests/
│   ├── conftest.py              Shared fixtures (mock API, mock coordinator)
│   ├── test_api.py              API client tests
│   ├── test_config_flow.py      Config flow tests
│   ├── test_coordinator.py      Coordinator tests
│   ├── test_sensor.py           Sensor entity tests
│   ├── test_number.py           Number entity tests
│   ├── test_select.py           Select entity tests
│   ├── test_switch.py           Switch entity tests
│   └── test_time.py             Time entity tests
├── hacs.json                    HACS metadata
├── LICENSE                      MIT license
└── README.md                    Docs, screenshots, install guide
```

---

## Phase 1 — Core Integration (MVP)

> **Starting state:** Empty project with only `docs/design.md`, `sunsynk-api.yaml`, `auth_example.py`, and `docs/implementation-plan.md`. Git repo initialized, remote `origin` points to `https://github.com/canaokar/ha-sunsynk-cloud.git`.
>
> **End state:** Working HACS integration with 18 writable entities (2 select, 12 number, 4 switch). Config flow authenticates against live API. Settings coordinator polls every 5 min. Writes debounced with category separation. Tagged `v0.1.0`.
>
> **Files created this phase:** `custom_components/sunsynk_cloud/` (`__init__.py`, `api.py`, `config_flow.py`, `coordinator.py`, `const.py`, `entity.py`, `select.py`, `number.py`, `switch.py`, `manifest.json`, `strings.json`, `translations/en.json`), `tests/` (`conftest.py`, `test_api.py`, `test_config_flow.py`, `test_coordinator.py`, `test_select.py`, `test_number.py`, `test_switch.py`), `hacs.json`, `LICENSE`.

### Task 1: Project Scaffolding

**Files:**
- Create: `custom_components/sunsynk_cloud/manifest.json`
- Create: `custom_components/sunsynk_cloud/const.py`
- Create: `custom_components/sunsynk_cloud/strings.json`
- Create: `custom_components/sunsynk_cloud/translations/en.json`
- Create: `tests/conftest.py`
- Create: `hacs.json`
- Create: `LICENSE`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p custom_components/sunsynk_cloud/translations
mkdir -p card/src/components
mkdir -p tests
```

- [ ] **Step 2: Create manifest.json**

```json
{
  "domain": "sunsynk_cloud",
  "name": "Sunsynk Cloud",
  "codeowners": ["@canaokar"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/canaokar/ha-sunsynk-cloud",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/canaokar/ha-sunsynk-cloud/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

No `requirements` needed — `aiohttp` and `cryptography` are bundled with HA.

- [ ] **Step 3: Create const.py**

```python
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

GRID_CHARGE_SETTINGS = frozenset({
    "sdChargeOn", "sdStartCap", "sdBatteryCurrent", "sdStartVolt",
    "gridSignal", "gridAlwaysOn",
})
```

- [ ] **Step 4: Create strings.json and translations/en.json**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Sunsynk Cloud Login",
        "description": "Enter your sunsynk.net credentials.",
        "data": {
          "username": "Email",
          "password": "Password"
        }
      },
      "select_inverters": {
        "title": "Select Inverters",
        "description": "Choose which inverters to add.",
        "data": {
          "inverter_sns": "Inverters"
        }
      }
    },
    "error": {
      "cannot_connect": "Cannot connect to Sunsynk API",
      "invalid_auth": "Invalid email or password",
      "unknown": "Unexpected error"
    },
    "abort": {
      "already_configured": "This account is already configured"
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Sunsynk Cloud Options",
        "data": {
          "settings_interval": "Settings poll interval (seconds)",
          "realtime_interval": "Realtime poll interval (seconds)",
          "enable_realtime": "Enable realtime sensors"
        }
      }
    }
  }
}
```

Copy the same content to `translations/en.json`.

- [ ] **Step 5: Create hacs.json**

```json
{
  "name": "Sunsynk Cloud",
  "render_readme": true
}
```

- [ ] **Step 6: Create LICENSE**

Standard MIT license file with `Copyright (c) 2026 canaokar`.

- [ ] **Step 7: Create tests/conftest.py with shared fixtures**

```python
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
```

- [ ] **Step 8: Commit scaffolding**

```bash
git add custom_components/ tests/ hacs.json LICENSE
git commit -m "project scaffolding: manifest, constants, strings, test fixtures"
```

---

### Task 2: API Client

**Files:**
- Create: `custom_components/sunsynk_cloud/api.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write API client tests**

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import ClientSession

from custom_components.sunsynk_cloud.api import SunsynkApi, AuthError, ApiError


@pytest.fixture
def api():
    session = MagicMock(spec=ClientSession)
    return SunsynkApi(session)


@pytest.mark.asyncio
async def test_get_public_key(api):
    mock_resp = AsyncMock()
    mock_resp.json = AsyncMock(return_value={
        "code": 0, "success": True, "data": "MOCK_PUBKEY_BASE64"
    })
    api._session.get = AsyncMock(return_value=mock_resp)

    key = await api._get_public_key()
    assert key == "MOCK_PUBKEY_BASE64"
    api._session.get.assert_called_once()
    call_url = api._session.get.call_args[0][0]
    assert "/anonymous/publicKey" in call_url


@pytest.mark.asyncio
async def test_authenticate_success(api):
    with patch.object(api, "_get_public_key", return_value="MIICIjAN...fake"):
        with patch.object(api, "_encrypt_password", return_value="encrypted_pw"):
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value={
                "code": 0,
                "success": True,
                "data": {
                    "access_token": "tok_123",
                    "refresh_token": "ref_456",
                    "expires_in": 604799,
                },
            })
            api._session.post = AsyncMock(return_value=mock_resp)

            await api.authenticate("user@test.com", "pass123")
            assert api._access_token == "tok_123"
            assert api._refresh_token == "ref_456"


@pytest.mark.asyncio
async def test_authenticate_bad_credentials(api):
    with patch.object(api, "_get_public_key", return_value="MIICIjAN...fake"):
        with patch.object(api, "_encrypt_password", return_value="encrypted_pw"):
            mock_resp = AsyncMock()
            mock_resp.json = AsyncMock(return_value={
                "code": 401, "success": False, "msg": "Bad credentials"
            })
            api._session.post = AsyncMock(return_value=mock_resp)

            with pytest.raises(AuthError):
                await api.authenticate("user@test.com", "wrong")


@pytest.mark.asyncio
async def test_get_plants(api):
    api._access_token = "tok_123"
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={
        "code": 0, "success": True,
        "data": {"infos": [{"id": 1, "name": "My Plant"}]},
    })
    api._session.get = AsyncMock(return_value=mock_resp)

    plants = await api.get_plants()
    assert len(plants) == 1
    assert plants[0]["id"] == 1


@pytest.mark.asyncio
async def test_get_settings(api):
    api._access_token = "tok_123"
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={
        "code": 0, "success": True,
        "data": {"sysWorkMode": "2", "solarSell": "1"},
    })
    api._session.get = AsyncMock(return_value=mock_resp)

    settings = await api.get_settings("2601120338")
    assert settings["sysWorkMode"] == "2"


@pytest.mark.asyncio
async def test_post_settings(api):
    api._access_token = "tok_123"
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={
        "code": 0, "success": True, "data": None,
    })
    api._session.post = AsyncMock(return_value=mock_resp)

    result = await api.post_settings("2601120338", {"solarSell": "0"})
    assert result is True

    posted = api._session.post.call_args
    assert "common/setting/2601120338/set" in posted[0][0]


@pytest.mark.asyncio
async def test_auto_reauth_on_401(api):
    api._access_token = "expired_token"
    api._username = "user@test.com"
    api._password = "pass123"

    call_count = 0

    async def mock_get(url, **kwargs):
        nonlocal call_count
        resp = AsyncMock()
        call_count += 1
        if call_count == 1:
            resp.status = 401
            resp.json = AsyncMock(return_value={"code": 401})
        else:
            resp.status = 200
            resp.json = AsyncMock(return_value={
                "code": 0, "success": True,
                "data": {"sysWorkMode": "2"},
            })
        return resp

    api._session.get = mock_get

    with patch.object(api, "authenticate", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = None
        api._access_token = "new_token"
        settings = await api.get_settings("2601120338")
        mock_auth.assert_called_once()
        assert settings["sysWorkMode"] == "2"


@pytest.mark.asyncio
async def test_post_settings_categorises_battery_fields(api):
    api._access_token = "tok_123"
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={
        "code": 0, "success": True, "data": None,
    })
    api._session.post = AsyncMock(return_value=mock_resp)

    await api.post_settings("2601120338", {
        "sysWorkMode": "1",
        "batteryShutdownCap": "15",
    })

    assert api._session.post.call_count == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/chinmay/code/sunsyn-net
python -m pytest tests/test_api.py -v
```

Expected: `ModuleNotFoundError: No module named 'custom_components.sunsynk_cloud.api'`

- [ ] **Step 3: Implement api.py**

```python
import base64
import hashlib
import logging
import time as time_mod
from typing import Any

import aiohttp
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_der_public_key

from .const import BASE_URL, SOURCE, BATTERY_SETTINGS, GRID_CHARGE_SETTINGS

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://www.sunsynk.net",
    "Referer": "https://www.sunsynk.net/",
}


class AuthError(Exception):
    pass


class ApiError(Exception):
    pass


class SunsynkApi:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._username: str | None = None
        self._password: str | None = None

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @access_token.setter
    def access_token(self, value: str) -> None:
        self._access_token = value

    async def _get_public_key(self) -> str:
        nonce = str(int(time_mod.time() * 1000))
        sign = hashlib.md5(
            f"nonce={nonce}&source={SOURCE}POWER_VIEW".encode()
        ).hexdigest()
        url = (
            f"{BASE_URL}/anonymous/publicKey"
            f"?nonce={nonce}&source={SOURCE}&sign={sign}"
        )
        resp = await self._session.get(url, headers=HEADERS)
        data = await resp.json()
        if not data.get("success"):
            raise ApiError(f"Failed to get public key: {data.get('msg')}")
        return data["data"]

    def _encrypt_password(self, password: str, pubkey_b64: str) -> str:
        pubkey_der = base64.b64decode(pubkey_b64)
        key = load_der_public_key(pubkey_der)
        encrypted = key.encrypt(password.encode(), padding.PKCS1v15())
        return base64.b64encode(encrypted).decode()

    async def authenticate(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

        pubkey_b64 = await self._get_public_key()
        encrypted_pw = self._encrypt_password(password, pubkey_b64)

        nonce = str(int(time_mod.time() * 1000))
        sign = hashlib.md5(
            f"nonce={nonce}&source={SOURCE}{pubkey_b64[:10]}".encode()
        ).hexdigest()

        resp = await self._session.post(
            f"{BASE_URL}/oauth/token/new",
            json={
                "sign": sign,
                "nonce": nonce,
                "username": username,
                "password": encrypted_pw,
                "grant_type": "password",
                "client_id": "csp-web",
                "source": SOURCE,
            },
            headers={**HEADERS, "Content-Type": "application/json;charset=UTF-8"},
        )
        data = await resp.json()
        if not data.get("success"):
            raise AuthError(data.get("msg", "Authentication failed"))

        self._access_token = data["data"]["access_token"]
        self._refresh_token = data["data"].get("refresh_token")

    async def _request(
        self, method: str, path: str, retry_auth: bool = True, **kwargs
    ) -> dict[str, Any]:
        url = f"{BASE_URL}{path}" if path.startswith("/") else f"{BASE_URL}/{path}"
        headers = {
            **HEADERS,
            "Authorization": f"Bearer {self._access_token}",
        }

        if method == "post":
            resp = await self._session.post(url, headers=headers, **kwargs)
        else:
            resp = await self._session.get(url, headers=headers, **kwargs)

        if resp.status == 401 and retry_auth and self._username and self._password:
            _LOGGER.debug("Token expired, re-authenticating")
            await self.authenticate(self._username, self._password)
            return await self._request(method, path, retry_auth=False, **kwargs)

        data = await resp.json()
        if data.get("code") != 0:
            raise ApiError(f"API error {data.get('code')}: {data.get('msg')}")
        return data.get("data", {})

    async def get_plants(self) -> list[dict]:
        data = await self._request("get", "/api/v1/plants?page=1&limit=100")
        return data.get("infos", [])

    async def get_inverters(self, plant_id: int) -> list[dict]:
        data = await self._request(
            "get",
            f"/api/v1/plant/{plant_id}/inverters?page=1&limit=100"
            f"&status=-1&type=-2",
        )
        return data.get("infos", [])

    async def get_inverter(self, sn: str) -> dict:
        return await self._request("get", f"/api/v1/inverter/{sn}")

    async def get_flow(self, sn: str) -> dict:
        return await self._request("get", f"/api/v1/inverter/{sn}/flow")

    async def get_grid_realtime(self, sn: str) -> dict:
        return await self._request(
            "get", f"/api/v1/inverter/grid/{sn}/realtime?sn={sn}&lan=en"
        )

    async def get_battery_realtime(self, sn: str) -> dict:
        return await self._request(
            "get", f"/api/v1/inverter/battery/{sn}/realtime?sn={sn}&lan=en"
        )

    async def get_load_realtime(self, sn: str) -> dict:
        return await self._request(
            "get", f"/api/v1/inverter/load/{sn}/realtime?sn={sn}&lan=en"
        )

    async def get_settings(self, sn: str) -> dict:
        return await self._request(
            "get", f"/api/v1/common/setting/{sn}/read"
        )

    async def post_settings(self, sn: str, settings: dict) -> bool:
        battery_fields = {}
        grid_charge_fields = {}
        system_fields = {}

        for key, val in settings.items():
            if key in BATTERY_SETTINGS:
                battery_fields[key] = val
            elif key in GRID_CHARGE_SETTINGS:
                grid_charge_fields[key] = val
            else:
                system_fields[key] = val

        url = f"/api/v1/common/setting/{sn}/set"
        for group in [system_fields, battery_fields, grid_charge_fields]:
            if group:
                group["sn"] = sn
                await self._request("post", url, json=group)
        return True
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_api.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add custom_components/sunsynk_cloud/api.py tests/test_api.py
git commit -m "add async API client with RSA auth and settings read/write"
```

---

### Task 3: Config Flow

**Files:**
- Create: `custom_components/sunsynk_cloud/config_flow.py`
- Create: `tests/test_config_flow.py`

- [ ] **Step 1: Write config flow tests**

```python
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.sunsynk_cloud.const import DOMAIN

from conftest import MOCK_PLANT, MOCK_INVERTER


@pytest.fixture
def mock_setup_entry():
    with patch(
        "custom_components.sunsynk_cloud.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


async def test_flow_user_step_success(hass, mock_setup_entry):
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


async def test_flow_invalid_auth(hass):
    with patch(
        "custom_components.sunsynk_cloud.config_flow.SunsynkApi"
    ) as MockApi:
        api = MockApi.return_value
        api.authenticate = AsyncMock(
            side_effect=Exception("Bad credentials")
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_config_flow.py -v
```

Expected: fail (module not found).

- [ ] **Step 3: Implement config_flow.py**

```python
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import SunsynkApi, AuthError
from .const import (
    DOMAIN,
    CONF_INVERTER_SNS,
    DEFAULT_SETTINGS_INTERVAL,
    DEFAULT_REALTIME_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class SunsynkCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._username: str = ""
        self._password: str = ""
        self._plants: list[dict] = []
        self._inverters: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input["username"]
            self._password = user_input["password"]

            await self.async_set_unique_id(self._username.lower())
            self._abort_if_unique_id_configured()

            try:
                session = aiohttp.ClientSession()
                api = SunsynkApi(session)
                await api.authenticate(self._username, self._password)
                self._plants = await api.get_plants()
                for plant in self._plants:
                    invs = await api.get_inverters(plant["id"])
                    self._inverters.extend(invs)
                await session.close()
            except AuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"

            if not errors:
                if len(self._inverters) == 1:
                    return self._create_entry([self._inverters[0]["sn"]])
                if len(self._inverters) > 1:
                    return await self.async_step_select_inverters()
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("username"): str,
                vol.Required("password"): str,
            }),
            errors=errors,
        )

    async def async_step_select_inverters(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self._create_entry(user_input[CONF_INVERTER_SNS])

        options = {
            inv["sn"]: f"{inv.get('alias', inv['sn'])} ({inv.get('brand', 'Unknown')})"
            for inv in self._inverters
        }
        return self.async_show_form(
            step_id="select_inverters",
            data_schema=vol.Schema({
                vol.Required(CONF_INVERTER_SNS): vol.All(
                    vol.Coerce(list), [vol.In(options)]
                ),
            }),
        )

    def _create_entry(self, sns: list[str]) -> FlowResult:
        selected = [inv for inv in self._inverters if inv["sn"] in sns]
        return self.async_create_entry(
            title=self._username,
            data={
                "username": self._username,
                "password": self._password,
                "inverters": selected,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SunsynkCloudOptionsFlow(config_entry)

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        return await self.async_step_user()


class SunsynkCloudOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self._config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "settings_interval",
                    default=current.get(
                        "settings_interval", DEFAULT_SETTINGS_INTERVAL
                    ),
                ): vol.All(int, vol.Range(min=60, max=900)),
                vol.Optional(
                    "realtime_interval",
                    default=current.get(
                        "realtime_interval", DEFAULT_REALTIME_INTERVAL
                    ),
                ): vol.All(int, vol.Range(min=30, max=300)),
                vol.Optional(
                    "enable_realtime",
                    default=current.get("enable_realtime", True),
                ): bool,
            }),
        )
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_config_flow.py -v
```

Note: config flow tests require a running HA test harness. If not available locally, verify structure manually and test on a real HA instance in Task 8.

- [ ] **Step 5: Commit**

```bash
git add custom_components/sunsynk_cloud/config_flow.py tests/test_config_flow.py
git commit -m "add config flow with credential validation and inverter discovery"
```

---

### Task 4: Coordinator + Integration Setup

**Files:**
- Create: `custom_components/sunsynk_cloud/coordinator.py`
- Create: `custom_components/sunsynk_cloud/entity.py`
- Create: `custom_components/sunsynk_cloud/__init__.py`
- Create: `tests/test_coordinator.py`

- [ ] **Step 1: Write coordinator tests**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from custom_components.sunsynk_cloud.coordinator import (
    SunsynkSettingsCoordinator,
)


@pytest.mark.asyncio
async def test_settings_coordinator_fetches_data(mock_api):
    hass = MagicMock()
    hass.loop = MagicMock()
    coordinator = SunsynkSettingsCoordinator(
        hass, mock_api, "2601120338", update_interval=timedelta(seconds=300)
    )
    data = await coordinator._async_update_data()
    mock_api.get_settings.assert_called_once_with("2601120338")
    assert data["sysWorkMode"] == "2"


@pytest.mark.asyncio
async def test_settings_coordinator_write_and_refresh(mock_api):
    hass = MagicMock()
    hass.loop = MagicMock()
    coordinator = SunsynkSettingsCoordinator(
        hass, mock_api, "2601120338", update_interval=timedelta(seconds=300)
    )
    coordinator.data = {"sysWorkMode": "2", "solarSell": "1"}

    await coordinator.async_write_settings({"solarSell": "0"})
    mock_api.post_settings.assert_called_once_with(
        "2601120338", {"solarSell": "0"}
    )
```

- [ ] **Step 2: Implement coordinator.py**

```python
import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SunsynkApi

_LOGGER = logging.getLogger(__name__)


class SunsynkSettingsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: SunsynkApi,
        sn: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"sunsynk_settings_{sn}",
            update_interval=update_interval,
        )
        self.api = api
        self.sn = sn
        self._write_lock = asyncio.Lock()
        self._pending_writes: dict[str, str] = {}
        self._debounce_task: asyncio.Task | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        return await self.api.get_settings(self.sn)

    async def async_write_settings(self, settings: dict[str, str]) -> None:
        async with self._write_lock:
            self._pending_writes.update(settings)
            if self._debounce_task and not self._debounce_task.done():
                self._debounce_task.cancel()
            self._debounce_task = asyncio.ensure_future(
                self._flush_writes()
            )

    async def _flush_writes(self) -> None:
        await asyncio.sleep(2)
        async with self._write_lock:
            if not self._pending_writes:
                return
            writes = dict(self._pending_writes)
            self._pending_writes.clear()

        await self.api.post_settings(self.sn, writes)
        await asyncio.sleep(30)
        await self.async_request_refresh()


class SunsynkRealtimeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: SunsynkApi,
        sn: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"sunsynk_realtime_{sn}",
            update_interval=update_interval,
        )
        self.api = api
        self.sn = sn

    async def _async_update_data(self) -> dict[str, Any]:
        flow, grid, battery, load = await asyncio.gather(
            self.api.get_flow(self.sn),
            self.api.get_grid_realtime(self.sn),
            self.api.get_battery_realtime(self.sn),
            self.api.get_load_realtime(self.sn),
        )
        return {
            "flow": flow,
            "grid": grid,
            "battery": battery,
            "load": load,
        }
```

- [ ] **Step 3: Implement entity.py (base entity class)**

```python
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SunsynkSettingsCoordinator


class SunsynkEntity(CoordinatorEntity[SunsynkSettingsCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
    ) -> None:
        super().__init__(coordinator)
        self._inverter = inverter
        self._sn = inverter["sn"]

    @property
    def device_info(self) -> DeviceInfo:
        version = self._inverter.get("version", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._sn)},
            name=self._inverter.get("alias", self._sn),
            manufacturer=self._inverter.get("brand", "Sunsynk"),
            model=f"{self._inverter.get('ratePower', 0) // 1000}kW Hybrid",
            sw_version=version.get("softVer"),
        )
```

- [ ] **Step 4: Implement __init__.py**

```python
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import SunsynkApi, AuthError
from .const import (
    DOMAIN,
    DEFAULT_SETTINGS_INTERVAL,
    DEFAULT_REALTIME_INTERVAL,
)
from .coordinator import SunsynkSettingsCoordinator, SunsynkRealtimeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["select", "number", "switch"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = aiohttp.ClientSession()
    api = SunsynkApi(session)

    try:
        await api.authenticate(entry.data["username"], entry.data["password"])
    except AuthError as err:
        await session.close()
        raise ConfigEntryAuthFailed from err

    settings_interval = timedelta(
        seconds=entry.options.get("settings_interval", DEFAULT_SETTINGS_INTERVAL)
    )
    realtime_interval = timedelta(
        seconds=entry.options.get("realtime_interval", DEFAULT_REALTIME_INTERVAL)
    )

    coordinators: dict[str, dict] = {}
    inverters = entry.data["inverters"]

    for inv in inverters:
        sn = inv["sn"]
        settings_coord = SunsynkSettingsCoordinator(
            hass, api, sn, settings_interval
        )
        await settings_coord.async_config_entry_first_refresh()

        realtime_coord = SunsynkRealtimeCoordinator(
            hass, api, sn, realtime_interval
        )
        if entry.options.get("enable_realtime", True):
            await realtime_coord.async_config_entry_first_refresh()

        coordinators[sn] = {
            "settings": settings_coord,
            "realtime": realtime_coord,
            "inverter": inv,
        }

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "session": session,
        "coordinators": coordinators,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["session"].close()
    return unload_ok
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_coordinator.py -v
```

- [ ] **Step 6: Commit**

```bash
git add custom_components/sunsynk_cloud/__init__.py custom_components/sunsynk_cloud/coordinator.py custom_components/sunsynk_cloud/entity.py tests/test_coordinator.py
git commit -m "add coordinators, base entity, and integration setup"
```

---

### Task 5: Select Entities (Work Mode, Energy Mode)

**Files:**
- Create: `custom_components/sunsynk_cloud/select.py`
- Create: `tests/test_select.py`

- [ ] **Step 1: Write select entity tests**

```python
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
```

- [ ] **Step 2: Implement select.py**

```python
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, WORK_MODE_NAMES, ENERGY_MODE_NAMES
from .coordinator import SunsynkSettingsCoordinator
from .entity import SunsynkEntity

SELECT_DEFINITIONS = [
    {
        "key": "work_mode",
        "field": "sysWorkMode",
        "options_map": WORK_MODE_NAMES,
        "icon": "mdi:solar-power",
    },
    {
        "key": "energy_mode",
        "field": "energyMode",
        "options_map": ENERGY_MODE_NAMES,
        "icon": "mdi:battery-charging",
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for sn, inv_data in data["coordinators"].items():
        for defn in SELECT_DEFINITIONS:
            entities.append(
                SunsynkSelectEntity(
                    coordinator=inv_data["settings"],
                    inverter=inv_data["inverter"],
                    **defn,
                )
            )
    async_add_entities(entities)


class SunsynkSelectEntity(SunsynkEntity, SelectEntity):
    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        key: str,
        field: str,
        options_map: dict[str, str],
        icon: str = "mdi:cog",
    ) -> None:
        super().__init__(coordinator, inverter)
        self._field = field
        self._options_map = options_map
        self._reverse_map = {v: k for k, v in options_map.items()}
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_icon = icon
        self._attr_options = list(options_map.values())

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.data.get(self._field)
        return self._options_map.get(val)

    async def async_select_option(self, option: str) -> None:
        api_val = self._reverse_map[option]
        await self.coordinator.async_write_settings({self._field: api_val})
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_select.py -v
```

- [ ] **Step 4: Commit**

```bash
git add custom_components/sunsynk_cloud/select.py tests/test_select.py
git commit -m "add select entities for work mode and energy mode"
```

---

### Task 6: Number Entities (SOC Limits, Power, Currents)

**Files:**
- Create: `custom_components/sunsynk_cloud/number.py`
- Create: `tests/test_number.py`

- [ ] **Step 1: Write number entity tests**

```python
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
```

- [ ] **Step 2: Implement number.py**

```python
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SunsynkSettingsCoordinator
from .entity import SunsynkEntity

NUMBER_DEFINITIONS = [
    {"key": "max_sell_power", "field": "solarMaxSellPower", "min_value": 0, "max_value": 15000, "step": 100, "unit": "W", "icon": "mdi:transmission-tower-export"},
    {"key": "zero_export_power", "field": "zeroExportPower", "min_value": 0, "max_value": 500, "step": 10, "unit": "W", "icon": "mdi:transmission-tower-off"},
    {"key": "grid_charge_soc", "field": "sdStartCap", "min_value": 10, "max_value": 90, "step": 1, "unit": "%", "icon": "mdi:battery-charging-40"},
    {"key": "grid_charge_current", "field": "sdBatteryCurrent", "min_value": 0, "max_value": 275, "step": 5, "unit": "A", "icon": "mdi:current-ac"},
    {"key": "battery_shutdown_soc", "field": "batteryShutdownCap", "min_value": 0, "max_value": 100, "step": 1, "unit": "%", "icon": "mdi:battery-alert"},
    {"key": "battery_restart_soc", "field": "batteryRestartCap", "min_value": 0, "max_value": 100, "step": 1, "unit": "%", "icon": "mdi:battery-plus"},
    {"key": "battery_low_soc", "field": "batteryLowCap", "min_value": 0, "max_value": 100, "step": 1, "unit": "%", "icon": "mdi:battery-low"},
    {"key": "max_charge_current", "field": "batteryMaxCurrentCharge", "min_value": 0, "max_value": 280, "step": 5, "unit": "A", "icon": "mdi:battery-charging"},
    {"key": "max_discharge_current", "field": "batteryMaxCurrentDischarge", "min_value": 0, "max_value": 280, "step": 5, "unit": "A", "icon": "mdi:battery-minus"},
    {"key": "grid_peak_power", "field": "gridPeakPower", "min_value": 0, "max_value": 15000, "step": 100, "unit": "W", "icon": "mdi:flash-alert"},
    {"key": "import_power_limit", "field": "importPower", "min_value": 0, "max_value": 15000, "step": 100, "unit": "W", "icon": "mdi:transmission-tower-import"},
    {"key": "ac_output_power_limit", "field": "acOutputPowerLimit", "min_value": 0, "max_value": 15000, "step": 100, "unit": "W", "icon": "mdi:power-plug"},
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for sn, inv_data in data["coordinators"].items():
        for defn in NUMBER_DEFINITIONS:
            entities.append(
                SunsynkNumberEntity(
                    coordinator=inv_data["settings"],
                    inverter=inv_data["inverter"],
                    **defn,
                )
            )
    async_add_entities(entities)


class SunsynkNumberEntity(SunsynkEntity, NumberEntity):
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        key: str,
        field: str,
        min_value: float,
        max_value: float,
        step: float,
        unit: str,
        icon: str = "mdi:cog",
    ) -> None:
        super().__init__(coordinator, inverter)
        self._field = field
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def native_value(self) -> float | None:
        val = self.coordinator.data.get(self._field)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_settings(
            {self._field: str(int(value))}
        )
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_number.py -v
```

- [ ] **Step 4: Commit**

```bash
git add custom_components/sunsynk_cloud/number.py tests/test_number.py
git commit -m "add number entities for SOC limits, power limits, and currents"
```

---

### Task 7: Switch Entities (Toggles)

**Files:**
- Create: `custom_components/sunsynk_cloud/switch.py`
- Create: `tests/test_switch.py`

- [ ] **Step 1: Write switch entity tests**

```python
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
```

- [ ] **Step 2: Implement switch.py**

```python
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SunsynkSettingsCoordinator
from .entity import SunsynkEntity

SWITCH_DEFINITIONS = [
    {"key": "solar_sell", "field": "solarSell", "on_value": "1", "off_value": "0", "icon": "mdi:solar-power-variant"},
    {"key": "grid_charge", "field": "sdChargeOn", "on_value": "1", "off_value": "0", "icon": "mdi:transmission-tower"},
    {"key": "peak_and_valley", "field": "peakAndVallery", "on_value": "1", "off_value": "0", "icon": "mdi:clock-outline"},
    {"key": "grid_peak_shaving", "field": "gridPeakShaving", "on_value": "1", "off_value": "0", "icon": "mdi:chart-bell-curve-cumulative"},
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for sn, inv_data in data["coordinators"].items():
        for defn in SWITCH_DEFINITIONS:
            entities.append(
                SunsynkSwitchEntity(
                    coordinator=inv_data["settings"],
                    inverter=inv_data["inverter"],
                    **defn,
                )
            )
    async_add_entities(entities)


class SunsynkSwitchEntity(SunsynkEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        key: str,
        field: str,
        on_value: str,
        off_value: str,
        icon: str = "mdi:toggle-switch",
    ) -> None:
        super().__init__(coordinator, inverter)
        self._field = field
        self._on_value = on_value
        self._off_value = off_value
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.data.get(self._field)
        if val is None:
            return None
        return str(val).lower() == self._on_value.lower()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_settings(
            {self._field: self._on_value}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write_settings(
            {self._field: self._off_value}
        )
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_switch.py -v
```

- [ ] **Step 4: Commit**

```bash
git add custom_components/sunsynk_cloud/switch.py tests/test_switch.py
git commit -m "add switch entities for solar sell, grid charge, and peak shaving"
```

---

### Task 8: Phase 1 Integration Test

- [ ] **Step 1: Run full test suite**

```bash
python -m pytest tests/ -v
```

All tests should pass.

- [ ] **Step 2: Validate manifest loads in HA**

Copy `custom_components/sunsynk_cloud/` to your HA instance's `custom_components/` directory. Restart HA. Check the integration appears in Settings → Integrations → Add Integration → search "Sunsynk Cloud".

- [ ] **Step 3: Test config flow against live API**

Add the integration using real credentials. Verify:
- Login succeeds
- Inverter is discovered
- Entities appear under the device

- [ ] **Step 4: Test entity reads**

Check Developer Tools → States. Verify:
- `select.sunsynk_2601120338_work_mode` shows "Limited to Home"
- `number.sunsynk_2601120338_battery_shutdown_soc` shows 12
- `switch.sunsynk_2601120338_solar_sell` shows "on"

- [ ] **Step 5: Commit and tag Phase 1**

```bash
git add -A
git commit -m "phase 1 complete: core integration with writable settings entities"
git tag v0.1.0
```

---

## Phase 2 — Realtime Sensors + Timer Entities

> **Starting state:** Phase 1 complete. The following files exist and must be read before starting:
> - `custom_components/sunsynk_cloud/__init__.py` — has `PLATFORMS = ["select", "number", "switch"]` (you will add `"sensor"` and `"time"`)
> - `custom_components/sunsynk_cloud/number.py` — has `NUMBER_DEFINITIONS` list with 12 entries (you will append timer numbers)
> - `custom_components/sunsynk_cloud/switch.py` — has `SWITCH_DEFINITIONS` list with 4 entries (you will append timer + day-of-week switches)
> - `custom_components/sunsynk_cloud/coordinator.py` — has `SunsynkSettingsCoordinator` and `SunsynkRealtimeCoordinator` (realtime coordinator exists but isn't started yet unless `enable_realtime` option is true)
> - `custom_components/sunsynk_cloud/entity.py` — base entity class, used by settings entities
> - `tests/conftest.py` — has `MOCK_SETTINGS`, `MOCK_FLOW`, `MOCK_GRID`, `MOCK_BATTERY`, `MOCK_LOAD` fixtures
>
> **End state:** Full entity coverage — 61 entities per inverter. Realtime coordinator active, polling flow/grid/battery/load every 60s. Options flow lets user change poll intervals. Tagged `v0.2.0`.
>
> **Files created this phase:** `custom_components/sunsynk_cloud/sensor.py`, `custom_components/sunsynk_cloud/time.py`, `tests/test_sensor.py`, `tests/test_time.py`.
> **Files modified this phase:** `__init__.py` (PLATFORMS), `number.py` (timer numbers appended), `switch.py` (timer + day-of-week switches appended).

### Task 9: Read-Only Sensor Entities

**Files:**
- Create: `custom_components/sunsynk_cloud/sensor.py`
- Create: `tests/test_sensor.py`
- Modify: `custom_components/sunsynk_cloud/__init__.py` — add `"sensor"` to `PLATFORMS`

- [ ] **Step 1: Write sensor tests**

```python
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
```

- [ ] **Step 2: Implement sensor.py**

```python
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SunsynkRealtimeCoordinator

SENSOR_DEFINITIONS = [
    {"key": "pv_power", "data_path": "flow.pvPower", "unit": "W", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power"},
    {"key": "battery_power", "data_path": "flow.battPower", "unit": "W", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery"},
    {"key": "battery_soc", "data_path": "flow.soc", "unit": "%", "device_class": "battery", "state_class": "measurement", "icon": "mdi:battery-medium"},
    {"key": "grid_power", "data_path": "flow.gridOrMeterPower", "unit": "W", "device_class": "power", "state_class": "measurement", "icon": "mdi:transmission-tower"},
    {"key": "load_power", "data_path": "flow.loadOrEpsPower", "unit": "W", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt"},
    {"key": "daily_pv_generation", "data_path": "grid.etodayTo", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:solar-power"},
    {"key": "daily_grid_import", "data_path": "grid.etodayFrom", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:transmission-tower-import"},
    {"key": "daily_grid_export", "data_path": "grid.etodayTo", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:transmission-tower-export"},
    {"key": "daily_battery_charge", "data_path": "battery.etodayChg", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:battery-charging"},
    {"key": "daily_battery_discharge", "data_path": "battery.etodayDischg", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:battery-minus"},
    {"key": "daily_load_consumption", "data_path": "load.dailyUsed", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:home-lightning-bolt"},
]

DEVICE_CLASS_MAP = {
    "power": SensorDeviceClass.POWER,
    "battery": SensorDeviceClass.BATTERY,
    "energy": SensorDeviceClass.ENERGY,
}

STATE_CLASS_MAP = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    if not entry.options.get("enable_realtime", True):
        return

    entities = []
    for sn, inv_data in data["coordinators"].items():
        for defn in SENSOR_DEFINITIONS:
            entities.append(
                SunsynkRealtimeSensor(
                    coordinator=inv_data["realtime"],
                    inverter=inv_data["inverter"],
                    **defn,
                )
            )
    async_add_entities(entities)


class SunsynkRealtimeSensor(CoordinatorEntity[SunsynkRealtimeCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SunsynkRealtimeCoordinator,
        inverter: dict,
        key: str,
        data_path: str,
        unit: str,
        device_class: str,
        state_class: str,
        icon: str = "mdi:gauge",
    ) -> None:
        super().__init__(coordinator)
        self._inverter = inverter
        self._sn = inverter["sn"]
        self._data_path = data_path
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = DEVICE_CLASS_MAP.get(device_class)
        self._attr_state_class = STATE_CLASS_MAP.get(state_class)
        self._attr_icon = icon

    @property
    def device_info(self):
        from .entity import SunsynkEntity
        version = self._inverter.get("version", {})
        from .const import DOMAIN
        return {
            "identifiers": {(DOMAIN, self._sn)},
            "name": self._inverter.get("alias", self._sn),
            "manufacturer": self._inverter.get("brand", "Sunsynk"),
            "model": f"{self._inverter.get('ratePower', 0) // 1000}kW Hybrid",
            "sw_version": version.get("softVer"),
        }

    @property
    def native_value(self) -> float | None:
        parts = self._data_path.split(".")
        data = self.coordinator.data
        for part in parts:
            if data is None:
                return None
            data = data.get(part) if isinstance(data, dict) else None
        if data is None:
            return None
        try:
            return float(data)
        except (ValueError, TypeError):
            return None
```

- [ ] **Step 3: Update __init__.py PLATFORMS**

Change `PLATFORMS = ["select", "number", "switch"]` to:

```python
PLATFORMS = ["select", "number", "switch", "sensor"]
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_sensor.py -v
```

- [ ] **Step 5: Commit**

```bash
git add custom_components/sunsynk_cloud/sensor.py custom_components/sunsynk_cloud/__init__.py tests/test_sensor.py
git commit -m "add realtime sensor entities for power flow and daily energy"
```

---

### Task 10: Timer Slot Entities

**Files:**
- Modify: `custom_components/sunsynk_cloud/number.py` — add timer number definitions
- Modify: `custom_components/sunsynk_cloud/switch.py` — add timer switch + day-of-week definitions
- Create: `custom_components/sunsynk_cloud/time.py`
- Create: `tests/test_time.py`
- Modify: `custom_components/sunsynk_cloud/__init__.py` — add `"time"` to PLATFORMS

- [ ] **Step 1: Write time entity tests**

```python
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
```

- [ ] **Step 2: Implement time.py**

```python
from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SunsynkSettingsCoordinator
from .entity import SunsynkEntity

TIMER_SLOTS = range(1, 7)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for sn, inv_data in data["coordinators"].items():
        for n in TIMER_SLOTS:
            entities.append(
                SunsynkTimeEntity(
                    coordinator=inv_data["settings"],
                    inverter=inv_data["inverter"],
                    key=f"timer_{n}_end_time",
                    field=f"sellTime{n}",
                )
            )
    async_add_entities(entities)


class SunsynkTimeEntity(SunsynkEntity, TimeEntity):
    def __init__(
        self,
        coordinator: SunsynkSettingsCoordinator,
        inverter: dict,
        key: str,
        field: str,
    ) -> None:
        super().__init__(coordinator, inverter)
        self._field = field
        self._attr_unique_id = f"{self._sn}_{key}"
        self._attr_translation_key = key
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> time | None:
        val = self.coordinator.data.get(self._field)
        if not val:
            return None
        try:
            h, m = val.split(":")
            return time(int(h), int(m))
        except (ValueError, AttributeError):
            return None

    async def async_set_value(self, value: time) -> None:
        time_str = f"{value.hour:02d}:{value.minute:02d}"
        await self.coordinator.async_write_settings({self._field: time_str})
```

- [ ] **Step 3: Add timer numbers and switches to existing definitions**

Append to `NUMBER_DEFINITIONS` in `number.py`:

```python
for _n in range(1, 7):
    NUMBER_DEFINITIONS.append(
        {"key": f"timer_{_n}_power", "field": f"sellTime{_n}Pac", "min_value": 0, "max_value": 10000, "step": 100, "unit": "W", "icon": "mdi:flash"}
    )
    NUMBER_DEFINITIONS.append(
        {"key": f"timer_{_n}_soc", "field": f"cap{_n}", "min_value": 0, "max_value": 100, "step": 1, "unit": "%", "icon": "mdi:battery-charging-outline"}
    )
```

Append to `SWITCH_DEFINITIONS` in `switch.py`:

```python
for _n in range(1, 7):
    SWITCH_DEFINITIONS.append(
        {"key": f"timer_{_n}_enable", "field": f"sellTime{_n}En", "on_value": "1", "off_value": "0", "icon": "mdi:timer"}
    )
    SWITCH_DEFINITIONS.append(
        {"key": f"timer_{_n}_grid_charge", "field": f"time{_n}on", "on_value": "true", "off_value": "false", "icon": "mdi:battery-charging"}
    )

_DAYS = [
    ("monday", "mondayOn"), ("tuesday", "tuesdayOn"),
    ("wednesday", "wednesdayOn"), ("thursday", "thursdayOn"),
    ("friday", "fridayOn"), ("saturday", "saturdayOn"),
    ("sunday", "sundayOn"),
]
for _day, _field in _DAYS:
    SWITCH_DEFINITIONS.append(
        {"key": f"schedule_{_day}", "field": _field, "on_value": "true", "off_value": "false", "icon": "mdi:calendar"}
    )
```

- [ ] **Step 4: Update __init__.py PLATFORMS**

```python
PLATFORMS = ["select", "number", "switch", "sensor", "time"]
```

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add custom_components/sunsynk_cloud/time.py custom_components/sunsynk_cloud/number.py custom_components/sunsynk_cloud/switch.py custom_components/sunsynk_cloud/__init__.py tests/test_time.py
git commit -m "add timer slot entities: time pickers, power/SOC numbers, enable/grid-charge switches, day-of-week toggles"
```

---

### Task 11: Phase 2 Integration Test

- [ ] **Step 1: Deploy to HA and verify all entities**

After deploying, check Developer Tools → States and confirm all ~58 entities exist:
- 12 sensors (power flow + daily energy)
- 2 selects (work mode, energy mode)
- 12 numbers (main settings)
- 12 timer numbers (6 power + 6 SOC)
- 4 main switches + 12 timer switches + 7 day-of-week switches = 23 switches
- 6 time entities

- [ ] **Step 2: Commit and tag Phase 2**

```bash
git add -A
git commit -m "phase 2 complete: realtime sensors and timer slot entities"
git tag v0.2.0
```

---

## Phase 3 — Custom Lovelace Card

> **Starting state:** Phases 1-2 complete. All 61 entities exist and work. The key thing for the card: entity IDs follow the pattern `{domain}.sunsynk_{inverter_sn}_{key}`, e.g.:
> - `sensor.sunsynk_2601120338_pv_power`
> - `select.sunsynk_2601120338_work_mode`
> - `number.sunsynk_2601120338_battery_shutdown_soc`
> - `switch.sunsynk_2601120338_solar_sell`
> - `time.sunsynk_2601120338_timer_1_end_time`
> - `switch.sunsynk_2601120338_schedule_monday`
>
> The card reads these entity states from `hass.states` and writes via `hass.callService()`. It does NOT talk to the API directly.
>
> **Files to read before starting:**
> - `custom_components/sunsynk_cloud/__init__.py` — you will add card static path registration
> - `docs/design.md` section 6 — card layout spec, configuration YAML format
>
> **End state:** Built `sunsynk-cloud-card.js` in `custom_components/sunsynk_cloud/card/`. Card renders power flow header, settings dropdowns/toggles/sliders, timer timeline with day-of-week row, battery and grid sections. All collapsible. Tagged `v0.3.0`.
>
> **Files created this phase:** `card/` directory (package.json, tsconfig.json, rollup.config.mjs, src/*.ts), `custom_components/sunsynk_cloud/card/sunsynk-cloud-card.js` (built output).
> **Files modified this phase:** `custom_components/sunsynk_cloud/__init__.py` (card static path registration).

### Task 12: Card Build Pipeline

**Files:**
- Create: `card/package.json`
- Create: `card/tsconfig.json`
- Create: `card/rollup.config.mjs`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "sunsynk-cloud-card",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "rollup -c",
    "watch": "rollup -c --watch"
  },
  "dependencies": {
    "lit": "^3.1.0"
  },
  "devDependencies": {
    "@rollup/plugin-node-resolve": "^15.2.0",
    "@rollup/plugin-typescript": "^11.1.0",
    "rollup": "^4.9.0",
    "rollup-plugin-terser": "^7.0.0",
    "typescript": "^5.3.0",
    "tslib": "^2.6.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2021",
    "module": "ESNext",
    "moduleResolution": "node",
    "lib": ["ES2021", "DOM", "DOM.Iterable"],
    "declaration": false,
    "strict": true,
    "noImplicitAny": true,
    "sourceMap": false,
    "outDir": "./dist",
    "rootDir": "./src",
    "experimentalDecorators": true,
    "useDefineForClassFields": false
  },
  "include": ["src/**/*.ts"]
}
```

- [ ] **Step 3: Create rollup.config.mjs**

```javascript
import resolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";
import { terser } from "rollup-plugin-terser";

export default {
  input: "src/sunsynk-cloud-card.ts",
  output: {
    file: "../custom_components/sunsynk_cloud/card/sunsynk-cloud-card.js",
    format: "es",
  },
  plugins: [resolve(), typescript(), terser()],
};
```

- [ ] **Step 4: Install and test build**

```bash
cd card && npm install && npm run build
```

Expected: creates `custom_components/sunsynk_cloud/card/sunsynk-cloud-card.js`

- [ ] **Step 5: Commit**

```bash
git add card/package.json card/tsconfig.json card/rollup.config.mjs
git commit -m "set up card build pipeline with rollup, typescript, and lit"
```

---

### Task 13: Card Scaffolding + Types

**Files:**
- Create: `card/src/types.ts`
- Create: `card/src/styles.ts`
- Create: `card/src/sunsynk-cloud-card.ts`

- [ ] **Step 1: Create types.ts**

```typescript
export interface SunsynkCardConfig {
  device: string;
  show_realtime?: boolean;
  show_timers?: boolean;
  show_battery?: boolean;
  show_grid?: boolean;
  compact?: boolean;
}

export interface TimerSlot {
  index: number;
  enabled: boolean;
  endTime: string;
  power: number;
  soc: number;
  gridCharge: boolean;
}

export interface HassEntity {
  state: string;
  attributes: Record<string, unknown>;
  entity_id: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: { entity_id: string }
  ): Promise<void>;
}
```

- [ ] **Step 2: Create styles.ts**

```typescript
import { css } from "lit";

export const cardStyles = css`
  :host {
    --primary-color: #4fc3f7;
    --success-color: #66bb6a;
    --warning-color: #ffa726;
    --error-color: #ef5350;
    --card-bg: var(--ha-card-background, #fff);
    --text-primary: var(--primary-text-color, #212121);
    --text-secondary: var(--secondary-text-color, #727272);
    --divider: var(--divider-color, #e0e0e0);
  }

  ha-card {
    padding: 16px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .header .title {
    font-size: 18px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .header .status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success-color);
  }

  .status-dot.offline {
    background: var(--error-color);
  }

  .power-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }

  .power-tile {
    text-align: center;
    padding: 12px 8px;
    border-radius: 8px;
    background: var(--card-bg);
    border: 1px solid var(--divider);
  }

  .power-tile .value {
    font-size: 20px;
    font-weight: 600;
  }

  .power-tile .label {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  .section {
    border-top: 1px solid var(--divider);
    padding-top: 12px;
    margin-top: 12px;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
  }

  .section-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
  }

  .section-content {
    padding-top: 12px;
  }

  .setting-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
  }

  .setting-row .label {
    font-size: 14px;
    color: var(--text-primary);
  }

  .timeline-bar {
    position: relative;
    height: 48px;
    background: var(--divider);
    border-radius: 6px;
    overflow: hidden;
    margin: 12px 0;
  }

  .timeline-slot {
    position: absolute;
    top: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    color: white;
    cursor: pointer;
    transition: opacity 0.2s;
    border-right: 1px solid rgba(255, 255, 255, 0.3);
  }

  .timeline-slot:hover {
    opacity: 0.85;
  }

  .timeline-slot.grid-charge {
    background: #1e88e5;
  }

  .timeline-slot.solar {
    background: #43a047;
  }

  .timeline-slot.disabled {
    background: #9e9e9e;
  }

  .timeline-labels {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: var(--text-secondary);
    padding: 0 2px;
  }

  .day-row {
    display: flex;
    gap: 6px;
    margin: 8px 0;
  }

  .day-toggle {
    width: 36px;
    height: 28px;
    border-radius: 4px;
    border: 1px solid var(--divider);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    cursor: pointer;
    user-select: none;
  }

  .day-toggle.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
  }

  .save-bar {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    margin-top: 12px;
  }

  .soc-badge {
    font-size: 24px;
    font-weight: 700;
  }
`;
```

- [ ] **Step 3: Create main card entry point sunsynk-cloud-card.ts**

```typescript
import { LitElement, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { cardStyles } from "./styles";
import type { SunsynkCardConfig, HomeAssistant, TimerSlot } from "./types";

@customElement("sunsynk-cloud-card")
export class SunsynkCloudCard extends LitElement {
  static styles = cardStyles;

  @property({ attribute: false }) hass!: HomeAssistant;
  @state() private _config!: SunsynkCardConfig;
  @state() private _expandedSections: Set<string> = new Set(["timers"]);

  setConfig(config: SunsynkCardConfig): void {
    if (!config.device) {
      throw new Error("Please define a device (inverter SN)");
    }
    this._config = {
      show_realtime: true,
      show_timers: true,
      show_battery: true,
      show_grid: true,
      compact: false,
      ...config,
    };
  }

  private _entityId(suffix: string): string {
    return `${suffix}.sunsynk_${this._config.device}_${suffix.split(".").pop()}`;
  }

  private _prefix(): string {
    return `sunsynk_${this._config.device}`;
  }

  private _getState(domain: string, key: string): string | undefined {
    const entityId = `${domain}.${this._prefix()}_${key}`;
    return this.hass?.states[entityId]?.state;
  }

  private _getNumericState(domain: string, key: string): number | undefined {
    const val = this._getState(domain, key);
    if (val === undefined || val === "unavailable" || val === "unknown") return undefined;
    return parseFloat(val);
  }

  private async _callService(
    domain: string,
    service: string,
    entityId: string,
    data?: Record<string, unknown>
  ): Promise<void> {
    await this.hass.callService(domain, service, data, {
      entity_id: entityId,
    });
  }

  private _toggleSection(section: string): void {
    const next = new Set(this._expandedSections);
    if (next.has(section)) {
      next.delete(section);
    } else {
      next.add(section);
    }
    this._expandedSections = next;
  }

  protected render() {
    if (!this._config || !this.hass) return nothing;

    return html`
      <ha-card>
        ${this._renderHeader()}
        ${this._config.show_realtime ? this._renderPowerTiles() : nothing}
        ${this._renderSettingsSection()}
        ${this._config.show_timers ? this._renderTimerSection() : nothing}
        ${this._config.show_battery ? this._renderBatterySection() : nothing}
        ${this._config.show_grid ? this._renderGridSection() : nothing}
      </ha-card>
    `;
  }

  private _renderHeader() {
    const soc = this._getNumericState("sensor", "battery_soc");
    return html`
      <div class="header">
        <span class="title">Sunsynk Inverter</span>
        <div class="status">
          <span class="soc-badge">${soc != null ? `${Math.round(soc)}%` : "--"}</span>
          <span>🔋</span>
        </div>
      </div>
    `;
  }

  private _renderPowerTiles() {
    const pv = this._getNumericState("sensor", "pv_power");
    const batt = this._getNumericState("sensor", "battery_power");
    const grid = this._getNumericState("sensor", "grid_power");
    const load = this._getNumericState("sensor", "load_power");

    return html`
      <div class="power-grid">
        <div class="power-tile">
          <div class="value" style="color: #f9a825">${pv ?? "--"}W</div>
          <div class="label">PV</div>
        </div>
        <div class="power-tile">
          <div class="value" style="color: ${(batt ?? 0) > 0 ? "#ef5350" : "#66bb6a"}">${batt ?? "--"}W</div>
          <div class="label">Battery</div>
        </div>
        <div class="power-tile">
          <div class="value" style="color: ${(grid ?? 0) < 0 ? "#66bb6a" : "#ef5350"}">${grid ?? "--"}W</div>
          <div class="label">Grid</div>
        </div>
        <div class="power-tile">
          <div class="value">${load ?? "--"}W</div>
          <div class="label">Load</div>
        </div>
      </div>
    `;
  }

  private _renderSettingsSection() {
    const workMode = this._getState("select", "work_mode");
    const energyMode = this._getState("select", "energy_mode");
    const solarSell = this._getState("switch", "solar_sell");

    return html`
      <div class="section">
        <div class="section-header" @click=${() => this._toggleSection("settings")}>
          <h3>Work Mode & General</h3>
          <span>${this._expandedSections.has("settings") ? "▾" : "▸"}</span>
        </div>
        ${this._expandedSections.has("settings") ? html`
          <div class="section-content">
            <div class="setting-row">
              <span class="label">Work Mode</span>
              <ha-select
                .value=${workMode}
                @selected=${(e: CustomEvent) => {
                  const entityId = `select.${this._prefix()}_work_mode`;
                  this._callService("select", "select_option", entityId, { option: (e.target as any).value });
                }}
              >
                <mwc-list-item value="Selling First">Selling First</mwc-list-item>
                <mwc-list-item value="Zero Export">Zero Export</mwc-list-item>
                <mwc-list-item value="Limited to Home">Limited to Home</mwc-list-item>
              </ha-select>
            </div>
            <div class="setting-row">
              <span class="label">Energy Mode</span>
              <ha-select
                .value=${energyMode}
                @selected=${(e: CustomEvent) => {
                  const entityId = `select.${this._prefix()}_energy_mode`;
                  this._callService("select", "select_option", entityId, { option: (e.target as any).value });
                }}
              >
                <mwc-list-item value="Battery First">Battery First</mwc-list-item>
                <mwc-list-item value="Load First">Load First</mwc-list-item>
              </ha-select>
            </div>
            <div class="setting-row">
              <span class="label">Solar Sell</span>
              <ha-switch
                .checked=${solarSell === "on"}
                @change=${(e: Event) => {
                  const entityId = `switch.${this._prefix()}_solar_sell`;
                  const service = (e.target as any).checked ? "turn_on" : "turn_off";
                  this._callService("switch", service, entityId);
                }}
              ></ha-switch>
            </div>
          </div>
        ` : nothing}
      </div>
    `;
  }

  private _renderTimerSection() {
    const slots: TimerSlot[] = [];
    for (let i = 1; i <= 6; i++) {
      slots.push({
        index: i,
        enabled: this._getState("switch", `timer_${i}_enable`) === "on",
        endTime: this._getState("time", `timer_${i}_end_time`) ?? "00:00",
        power: this._getNumericState("number", `timer_${i}_power`) ?? 0,
        soc: this._getNumericState("number", `timer_${i}_soc`) ?? 0,
        gridCharge: this._getState("switch", `timer_${i}_grid_charge`) === "on",
      });
    }

    const startTimes = ["00:00", ...slots.slice(0, 5).map((s) => s.endTime)];

    return html`
      <div class="section">
        <div class="section-header" @click=${() => this._toggleSection("timers")}>
          <h3>Timer Schedule</h3>
          <span>${this._expandedSections.has("timers") ? "▾" : "▸"}</span>
        </div>
        ${this._expandedSections.has("timers") ? html`
          <div class="section-content">
            <div class="timeline-bar">
              ${slots.map((slot, i) => {
                const start = this._timeToPercent(startTimes[i]);
                const end = this._timeToPercent(slot.endTime);
                const width = end - start;
                const cls = !slot.enabled ? "disabled" : slot.gridCharge ? "grid-charge" : "solar";
                return html`
                  <div
                    class="timeline-slot ${cls}"
                    style="left: ${start}%; width: ${width}%"
                    title="Slot ${slot.index}: ${startTimes[i]}-${slot.endTime} | ${slot.power}W | SOC ${slot.soc}%"
                  >
                    <span>${slot.soc}%</span>
                    <span>${slot.power}W</span>
                  </div>
                `;
              })}
            </div>
            <div class="timeline-labels">
              <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
            </div>
            ${this._renderDayRow()}
          </div>
        ` : nothing}
      </div>
    `;
  }

  private _renderDayRow() {
    const days = [
      { key: "monday", label: "Mo" },
      { key: "tuesday", label: "Tu" },
      { key: "wednesday", label: "We" },
      { key: "thursday", label: "Th" },
      { key: "friday", label: "Fr" },
      { key: "saturday", label: "Sa" },
      { key: "sunday", label: "Su" },
    ];

    return html`
      <div class="day-row">
        ${days.map((d) => {
          const active = this._getState("switch", `schedule_${d.key}`) === "on";
          return html`
            <div
              class="day-toggle ${active ? "active" : ""}"
              @click=${() => {
                const entityId = `switch.${this._prefix()}_schedule_${d.key}`;
                this._callService("switch", active ? "turn_off" : "turn_on", entityId);
              }}
            >${d.label}</div>
          `;
        })}
      </div>
    `;
  }

  private _renderBatterySection() {
    return html`
      <div class="section">
        <div class="section-header" @click=${() => this._toggleSection("battery")}>
          <h3>Battery</h3>
          <span>${this._expandedSections.has("battery") ? "▾" : "▸"}</span>
        </div>
        ${this._expandedSections.has("battery") ? html`
          <div class="section-content">
            ${this._renderSlider("Shutdown SOC", "number", "battery_shutdown_soc", "%", 0, 100)}
            ${this._renderSlider("Low Warning SOC", "number", "battery_low_soc", "%", 0, 100)}
            ${this._renderSlider("Restart SOC", "number", "battery_restart_soc", "%", 0, 100)}
            ${this._renderSlider("Max Charge Current", "number", "max_charge_current", "A", 0, 280)}
            ${this._renderSlider("Max Discharge Current", "number", "max_discharge_current", "A", 0, 280)}
          </div>
        ` : nothing}
      </div>
    `;
  }

  private _renderGridSection() {
    const gridCharge = this._getState("switch", "grid_charge");
    const peakShaving = this._getState("switch", "grid_peak_shaving");

    return html`
      <div class="section">
        <div class="section-header" @click=${() => this._toggleSection("grid")}>
          <h3>Grid</h3>
          <span>${this._expandedSections.has("grid") ? "▾" : "▸"}</span>
        </div>
        ${this._expandedSections.has("grid") ? html`
          <div class="section-content">
            <div class="setting-row">
              <span class="label">Grid Charge</span>
              <ha-switch
                .checked=${gridCharge === "on"}
                @change=${(e: Event) => {
                  const entityId = `switch.${this._prefix()}_grid_charge`;
                  this._callService("switch", (e.target as any).checked ? "turn_on" : "turn_off", entityId);
                }}
              ></ha-switch>
            </div>
            ${this._renderSlider("Grid Charge SOC", "number", "grid_charge_soc", "%", 10, 90)}
            ${this._renderSlider("Grid Charge Current", "number", "grid_charge_current", "A", 0, 275)}
            <div class="setting-row">
              <span class="label">Peak Shaving</span>
              <ha-switch
                .checked=${peakShaving === "on"}
                @change=${(e: Event) => {
                  const entityId = `switch.${this._prefix()}_grid_peak_shaving`;
                  this._callService("switch", (e.target as any).checked ? "turn_on" : "turn_off", entityId);
                }}
              ></ha-switch>
            </div>
            ${this._renderSlider("Peak Shaving Power", "number", "grid_peak_power", "W", 0, 15000)}
          </div>
        ` : nothing}
      </div>
    `;
  }

  private _renderSlider(label: string, domain: string, key: string, unit: string, min: number, max: number) {
    const val = this._getNumericState(domain, key);
    const entityId = `${domain}.${this._prefix()}_${key}`;

    return html`
      <div class="setting-row">
        <span class="label">${label}</span>
        <span>${val != null ? `${val}${unit}` : "--"}</span>
      </div>
      <ha-slider
        .min=${min}
        .max=${max}
        .value=${val ?? min}
        @change=${(e: Event) => {
          const newVal = (e.target as any).value;
          this._callService("number", "set_value", entityId, { value: newVal });
        }}
      ></ha-slider>
    `;
  }

  private _timeToPercent(time: string): number {
    const [h, m] = time.split(":").map(Number);
    return ((h * 60 + m) / 1440) * 100;
  }

  getCardSize(): number {
    return this._config?.compact ? 4 : 8;
  }

  static getConfigElement() {
    return document.createElement("sunsynk-cloud-card-editor");
  }

  static getStubConfig() {
    return { device: "" };
  }
}

(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: "sunsynk-cloud-card",
  name: "Sunsynk Cloud Card",
  description: "Control panel for Sunsynk/Deye inverters via cloud API",
});
```

- [ ] **Step 4: Build the card**

```bash
cd card && npm run build
```

Verify `custom_components/sunsynk_cloud/card/sunsynk-cloud-card.js` exists.

- [ ] **Step 5: Update __init__.py to register the card**

Add to `async_setup_entry` in `__init__.py`, before the platform setup:

```python
card_path = hass.config.path(
    "custom_components/sunsynk_cloud/card/sunsynk-cloud-card.js"
)
hass.http.register_static_path(
    "/sunsynk_cloud/sunsynk-cloud-card.js",
    card_path,
    cache_headers=True,
)
```

- [ ] **Step 6: Commit**

```bash
git add card/ custom_components/sunsynk_cloud/card/ custom_components/sunsynk_cloud/__init__.py
git commit -m "add custom Lovelace card with power flow display, settings controls, and timer timeline"
```

---

### Task 14: Phase 3 Card Testing

- [ ] **Step 1: Deploy and test card in HA**

Add to a Lovelace dashboard:
```yaml
type: custom:sunsynk-cloud-card
device: "2601120338"
```

Verify:
- Header shows SOC and power tiles
- Work mode dropdown changes the entity
- Timer timeline renders all 6 slots
- Battery sliders move and write values
- Grid section toggles work

- [ ] **Step 2: Tag Phase 3**

```bash
git add -A
git commit -m "phase 3 complete: custom Lovelace card with timer timeline and settings panels"
git tag v0.3.0
```

---

## Phase 4 — Polish & Release

> **Starting state:** Phases 1-3 complete. Integration works, card works, all entities exist. What's missing: retry logic on failed writes, re-auth trigger when credentials expire, README, and HACS release metadata.
>
> **Files to read before starting:**
> - `custom_components/sunsynk_cloud/api.py` — you will add exponential backoff to `post_settings` and `_request`
> - `custom_components/sunsynk_cloud/__init__.py` — verify `ConfigEntryAuthFailed` is raised on auth failure (should already be there from Phase 1, but confirm)
> - `docs/design.md` section 9 — Predbat integration examples for the README
> - `docs/design.md` section 10 — risk table for the README
>
> **End state:** Production-ready. README with install guide, entity docs, card config, Predbat examples. Writes retry 3x with backoff. Re-auth prompts on expired credentials. Tagged `v1.0.0`, pushed to GitHub.

### Task 15: Error Handling & Re-Auth

**Files:**
- Modify: `custom_components/sunsynk_cloud/api.py`
- Modify: `custom_components/sunsynk_cloud/__init__.py`

- [ ] **Step 1: Add exponential backoff to API client**

Add to `api.py`:

```python
import asyncio

MAX_RETRIES = 3
RETRY_DELAYS = [4, 8, 16]

async def _request_with_retry(self, method, path, **kwargs):
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return await self._request(method, path, **kwargs)
        except ApiError as err:
            last_error = err
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])
    raise last_error
```

Update `post_settings` to use `_request_with_retry` for write operations.

- [ ] **Step 2: Add re-auth trigger to __init__.py**

In `async_setup_entry`, wrap the authenticate call to trigger re-auth on failure:

```python
from homeassistant.exceptions import ConfigEntryAuthFailed

try:
    await api.authenticate(entry.data["username"], entry.data["password"])
except AuthError as err:
    await session.close()
    raise ConfigEntryAuthFailed("Login failed — check credentials") from err
```

- [ ] **Step 3: Commit**

```bash
git add custom_components/sunsynk_cloud/api.py custom_components/sunsynk_cloud/__init__.py
git commit -m "add retry with backoff for writes and re-auth on expired credentials"
```

---

### Task 16: README & HACS Release

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Include:
- Project name and one-line description
- Installation instructions (HACS custom repo + manual)
- Configuration screenshots or steps
- Entity list summary
- Card configuration YAML example
- Predbat integration examples
- Supported inverter types
- Contributing section
- License

- [ ] **Step 2: Final test pass**

```bash
python -m pytest tests/ -v
cd card && npm run build
```

All tests pass, card builds clean.

- [ ] **Step 3: Final commit and tag**

```bash
git add -A
git commit -m "add README, finalize for v1.0.0 release"
git tag v1.0.0
```

- [ ] **Step 4: Push to GitHub**

```bash
git push -u origin main --tags
```

---

## Summary

| Phase | Tasks | Entities Created | Key Deliverable |
|-------|-------|-----------------|-----------------|
| 1 | 1-8 | 18 (2 select, 12 number, 4 switch) | Working integration with writable settings |
| 2 | 9-11 | +43 (12 sensor, 12 timer number, 12 timer switch, 6 time, 7 day switches) | Full entity coverage + realtime |
| 3 | 12-14 | — | Custom Lovelace card with timer timeline |
| 4 | 15-16 | — | Error handling, README, HACS release |

**Total: ~61 entities per inverter, 16 tasks, 4 phases.**
