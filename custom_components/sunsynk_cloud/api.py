import asyncio
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

MAX_RETRIES = 3
RETRY_DELAYS = [4, 8, 16]

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
        return data.get("data", {}) or {}

    async def _request_with_retry(
        self, method: str, path: str, **kwargs
    ) -> dict[str, Any]:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return await self._request(method, path, **kwargs)
            except ApiError as err:
                last_error = err
                _LOGGER.warning(
                    "API request failed (attempt %d/%d): %s",
                    attempt + 1, MAX_RETRIES, err,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
        raise last_error

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
                await self._request_with_retry("post", url, json=group)
        return True
