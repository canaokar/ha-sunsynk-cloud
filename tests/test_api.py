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
