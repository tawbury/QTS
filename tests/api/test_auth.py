import requests
import pytest

from ._env import (
    get_kis_base_url,
    get_kis_app_key,
    get_kis_app_secret,
)

pytestmark = pytest.mark.api_exploration


def test_kis_auth_token():
    base_url = get_kis_base_url()
    app_key = get_kis_app_key()
    app_secret = get_kis_app_secret()

    assert base_url, "Missing base_url"
    assert app_key, "Missing app_key"
    assert app_secret, "Missing app_secret"

    url = f"{base_url}/oauth2/tokenP"

    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }

    resp = requests.post(url, json=payload, timeout=10)

    print("STATUS:", resp.status_code)
    print("BODY:", resp.text)

    assert resp.status_code in (200, 400, 401)
