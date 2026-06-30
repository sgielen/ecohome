import hashlib
import json
from pathlib import Path
from typing import Any

import httpx


_CLOUDSERVICE_BASE_URL = "https://ehome.ne01.com/cloudservice/api/app"
_CRM_BASE_URL = "https://ehome.ne01.com/crmservice/api/app"
_CREDENTIALS_FILE = Path.home() / ".ecohome" / "credentials.json"

_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "app-id-type": "0",
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "Html5Plus/1.0 (Immersed/20) uni-app"
    ),
    "time-zone": "Europe/Berlin",
    "Accept-Language": "nl-NL,nl;q=0.9",
}


def _load_credentials() -> dict[str, Any]:
    if not _CREDENTIALS_FILE.exists():
        return {}
    return json.loads(_CREDENTIALS_FILE.read_text())


def _save_credentials(creds: dict[str, Any]) -> None:
    _CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CREDENTIALS_FILE.write_text(json.dumps(creds, indent=2))
    _CREDENTIALS_FILE.chmod(0o600)


class SessionExpiredError(RuntimeError):
    pass


def _raise_on_error(data: dict[str, Any], endpoint: str) -> None:
    if "errorCode" in data:  # crmservice: camelCase, int 200 for success
        if data["errorCode"] != 200:
            raise RuntimeError(f"{endpoint} failed: {data['errorCode']} {data.get('errorMsg', 'Unknown error')}")
    elif "error_code" in data:  # cloudservice: snake_case, string "0" for success
        if data["error_code"] != "0":
            raise RuntimeError(f"{endpoint} failed: {data['error_code']} {data.get('error_msg', 'Unknown error')}")
    elif "sub_code" in data:  # gateway/auth error, e.g. sub_code="-100" means session expired
        if data["sub_code"] == "-100":
            raise SessionExpiredError(f"{endpoint}: session expired")
        raise RuntimeError(f"{endpoint} failed: sub_code={data['sub_code']} {data.get('sub_msg', 'Unknown error')}")
    else:
        raise RuntimeError(f"{endpoint} failed: unrecognized response format: {data}")


class EcoHomeClient:
    def __init__(
        self,
        *,
        token: str | None = None,
        cookie: dict[str, str] | None = None,
        user_id: str | None = None,
        username: str | None = None,
    ):
        self._token = token
        self._cookie: dict[str, str] = cookie or {}
        self._user_id = user_id
        self._username = username

    @classmethod
    def login(
        cls,
        username: str,
        password: str,
        save_credentials: bool = True,
        force_relogin: bool = False,
    ) -> "EcoHomeClient":
        """Return an authenticated client, reusing stored credentials when available."""
        creds: dict[str, Any] = _load_credentials() if save_credentials else {}
        if not force_relogin and username in creds:
            stored = creds[username]
            client = cls(
                token=stored["x_token"],
                cookie=stored["cookie"],
                user_id=stored["user_id"],
                username=username,
            )
            if client.is_logged_in():
                return client

        password_md5 = hashlib.md5(password.encode()).hexdigest()

        with httpx.Client() as http:
            response = http.post(
                f"{_CLOUDSERVICE_BASE_URL}/user/login.json",
                params={"lang": "nl_NL"},
                headers=_HEADERS,
                json={"user_name": username, "password": password_md5, "type": 2},
            )
        response.raise_for_status()

        data = response.json()
        _raise_on_error(data, "login")

        result = data["object_result"]
        user_id = str(result["user_id"])
        x_token = result["x-token"]
        cookie = dict(response.cookies)

        if save_credentials:
            creds[username] = {
                "user_id": user_id,
                "x_token": x_token,
                "cookie": cookie,
            }
            _save_credentials(creds)

        return cls(
            token=x_token,
            cookie=cookie,
            user_id=user_id,
            username=username,
        )

    def is_logged_in(self) -> bool:
        """Do an API request to see if the user is logged in."""
        with httpx.Client(cookies=self._cookie) as http:
            response = http.get(
                f"{_CLOUDSERVICE_BASE_URL}/user/getUserInfo.json",
                params={"lang": "nl_NL"},
                headers=self._auth_headers(),
            )
        try:
            response.raise_for_status()
            _raise_on_error(response.json(), "getUserInfo")
            return True
        except (httpx.HTTPStatusError, RuntimeError):
            return False

    def logout(self) -> None:
        """Log out and remove stored credentials for this user."""
        with httpx.Client(cookies=self._cookie) as http:
            response = http.post(
                f"{_CLOUDSERVICE_BASE_URL}/user/logout.json",
                params={"lang": "nl_NL"},
                headers=self._auth_headers(),
                json={"from_user": self._user_id},
            )
        response.raise_for_status()

        if self._username:
            creds = _load_credentials()
            creds.pop(self._username, None)
            _save_credentials(creds)

        self._token = None
        self._cookie = {}
        self._user_id = None
        self._username = None

    def _auth_headers(self) -> dict[str, str]:
        if self._token is None:
            raise RuntimeError("Not authenticated")
        return {**_HEADERS, "x-token": self._token}

    def _http(self) -> httpx.Client:
        return httpx.Client(cookies=self._cookie)

    def list_devices(self, page_size: int = 1000) -> list[dict[str, Any]]:
        with self._http() as http:
            response = http.post(
                f"{_CLOUDSERVICE_BASE_URL}/device/deviceList.json",
                params={"lang": "nl_NL"},
                headers=self._auth_headers(),
                json={"page_index": "1", "page_size": str(page_size)},
            )
        response.raise_for_status()
        data = response.json()
        _raise_on_error(data, "deviceList")
        return data["object_result"]

    def get_device_base_info(self, device_code: str) -> dict[str, Any]:
        with self._http() as http:
            response = http.post(
                f"{_CLOUDSERVICE_BASE_URL}/deviceInfo/getDeviceBaseInfo.json",
                params={"lang": "nl_NL"},
                headers=self._auth_headers(),
                json={"device_code": device_code},
            )
        response.raise_for_status()
        data = response.json()
        _raise_on_error(data, "getDeviceBaseInfo")
        return data["object_result"]

    def get_device_detail(self, device_code: str) -> dict[str, Any]:
        with self._http() as http:
            response = http.post(
                f"{_CRM_BASE_URL}/deviceInfo/getDeviceDetailV3",
                params={"lang": "nl_NL"},
                headers=self._auth_headers(),
                json={"deviceCode": device_code},
            )
        response.raise_for_status()
        data = response.json()
        _raise_on_error(data, "getDeviceDetailV3")
        return data["objectResult"]

    def get_param_list(self, device_code: str, param_type: int) -> list[dict[str, Any]]:
        """Return paramListV3 for the given type: 0=sensors, 1=operational, 2=settings."""
        with self._http() as http:
            response = http.post(
                f"{_CRM_BASE_URL}/deviceInfo/paramListV3",
                params={"lang": "nl_NL"},
                headers=self._auth_headers(),
                json={"deviceCode": device_code, "type": param_type, "isAutoRefresh": False},
            )
        response.raise_for_status()
        data = response.json()
        _raise_on_error(data, "paramListV3")
        return data["objectResult"]

    def update_switch_state(self, device_code: str, address: str, value: bool, dry_run: bool = False) -> None:
        url = f"{_CLOUDSERVICE_BASE_URL}/deviceInfo/updateSwitchSate.json"
        body = {"device_code": device_code, "address": address, "value": value}
        if dry_run:
            print(f"[dry-run] POST {url}?lang=nl_NL")
            print(json.dumps(body, indent=2))
            return
        with self._http() as http:
            response = http.post(url, params={"lang": "nl_NL"}, headers=self._auth_headers(), json=body)
        response.raise_for_status()
        data = response.json()
        _raise_on_error(data, "updateSwitchState")

    def set_value(self, device_code: str, address: str, value: int, dry_run: bool = False) -> None:
        url = f"{_CLOUDSERVICE_BASE_URL}/deviceInfo/controlOfValue.json"
        body = {"device_code": device_code, "address": address, "value": value}
        if dry_run:
            print(f"[dry-run] POST {url}?lang=nl_NL")
            print(json.dumps(body, indent=2))
            return
        with self._http() as http:
            response = http.post(url, params={"lang": "nl_NL"}, headers=self._auth_headers(), json=body)
        response.raise_for_status()
        data = response.json()
        _raise_on_error(data, "controlOfValue")
