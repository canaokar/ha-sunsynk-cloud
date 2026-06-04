"""
Sunsynk API Authentication Example

Demonstrates the RSA-encrypted login flow for api.sunsynk.net.
Use this as a reference for integration - handles the full auth handshake.
"""

import base64
import hashlib
import json
import ssl
import subprocess
import tempfile
import time
import urllib.request
import os

BASE_URL = "https://api.sunsynk.net"
SOURCE = "sunsynk"


def get_public_key():
    nonce = str(int(time.time() * 1000))
    sign = hashlib.md5(f"nonce={nonce}&source={SOURCE}POWER_VIEW".encode()).hexdigest()
    url = f"{BASE_URL}/anonymous/publicKey?nonce={nonce}&source={SOURCE}&sign={sign}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://www.sunsynk.net",
        "Referer": "https://www.sunsynk.net/",
    })
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, context=ctx)
    data = json.loads(resp.read())
    if not data.get("success"):
        raise RuntimeError(f"Failed to get public key: {data}")
    return data["data"]


def encrypt_password(password: str, pubkey_b64: str) -> str:
    pubkey_der = base64.b64decode(pubkey_b64)
    with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as f:
        f.write(pubkey_der)
        der_path = f.name
    pem_path = der_path + ".pem"
    try:
        subprocess.run(
            ["openssl", "rsa", "-pubin", "-inform", "DER", "-in", der_path, "-outform", "PEM", "-out", pem_path],
            check=True, capture_output=True,
        )
        result = subprocess.run(
            ["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", pem_path, "-pkeyopt", "rsa_padding_mode:pkcs1"],
            input=password.encode(), capture_output=True,
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["openssl", "rsautl", "-encrypt", "-pubin", "-inkey", pem_path, "-pkcs"],
                input=password.encode(), capture_output=True,
            )
        if result.returncode != 0:
            raise RuntimeError("openssl encryption failed")
        return base64.b64encode(result.stdout).decode()
    finally:
        os.unlink(der_path)
        os.unlink(pem_path)


def authenticate(username: str, password: str) -> dict:
    pubkey_b64 = get_public_key()
    encrypted_pw = encrypt_password(password, pubkey_b64)

    nonce = str(int(time.time() * 1000))
    pubkey_prefix = pubkey_b64[:10]
    sign = hashlib.md5(f"nonce={nonce}&source={SOURCE}{pubkey_prefix}".encode()).hexdigest()

    body = json.dumps({
        "sign": sign,
        "nonce": nonce,
        "username": username,
        "password": encrypted_pw,
        "grant_type": "password",
        "client_id": "csp-web",
        "source": SOURCE,
    }).encode()

    req = urllib.request.Request(
        f"{BASE_URL}/oauth/token/new",
        data=body,
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.sunsynk.net",
            "Referer": "https://www.sunsynk.net/",
        },
    )
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, context=ctx)
    data = json.loads(resp.read())
    if not data.get("success"):
        raise RuntimeError(f"Authentication failed: {data}")
    return data["data"]


def api_get(path: str, token: str, params: dict = None) -> dict:
    url = f"{BASE_URL}{path}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url += f"?{qs}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0",
    })
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, context=ctx)
    return json.loads(resp.read())


def api_post(path: str, token: str, data: dict) -> dict:
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    })
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, context=ctx)
    return json.loads(resp.read())


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python auth_example.py <username> <password>")
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]
    print("Authenticating...")
    tokens = authenticate(username, password)
    access_token = tokens["access_token"]
    print(f"Token obtained (expires in {tokens['expires_in']}s)")

    print("\nFetching plants...")
    plants = api_get("/api/v1/plants", access_token, {"page": "1", "limit": "10"})
    for plant in plants["data"]["infos"]:
        print(f"  Plant: {plant['name']} (ID: {plant['id']}, PAC: {plant['pac']}W)")

        inverters = api_get(f"/api/v1/plant/{plant['id']}/inverters", access_token, {"page": "1", "limit": "10"})
        for inv in inverters["data"]["infos"]:
            sn = inv["sn"]
            print(f"    Inverter: {sn} (Status: {inv['status']}, PAC: {inv['pac']}W)")

            flow = api_get(f"/api/v1/inverter/{sn}/flow", access_token)
            d = flow["data"]
            print(f"      PV: {d['pvPower']}W | Battery: {d['battPower']}W (SOC: {d['soc']}%) | Grid: {d['gridOrMeterPower']}W | Load: {d['loadOrEpsPower']}W")

            print(f"\n    Reading settings for {sn}...")
            settings = api_get(f"/api/v1/common/setting/{sn}/read", access_token)
            s = settings["data"]
            print(f"      Work Mode: {s.get('sysWorkMode')} | Energy Mode: {s.get('energyMode')} | Peak&Valley: {s.get('peakAndVallery')}")
            print(f"      Solar Sell: {s.get('solarSell')} | Max Sell: {s.get('solarMaxSellPower')}W | Zero Export: {s.get('zeroExportPower')}W")
            print(f"      Battery Cap: {s.get('batteryCap')}Ah | Shutdown SOC: {s.get('batteryShutdownCap')}% | Low SOC: {s.get('batteryLowCap')}%")
            for i in range(1, 7):
                en = s.get(f"sellTime{i}En", "0")
                time_val = s.get(f"sellTime{i}", "?")
                pac = s.get(f"sellTime{i}Pac", "?")
                cap = s.get(f"cap{i}", "?")
                grid_chg = s.get(f"time{i}on", "?")
                print(f"      Slot {i}: {time_val} | {pac}W | SOC:{cap}% | GridChg:{grid_chg} | En:{en}")
