import unittest
from unittest.mock import patch

from ecohome.client import AsyncEcoHomeClient, AuthenticationFailedError, _api_language


class _Response:
    def __init__(self, data: dict):
        self._data = data
        self.cookies = {}

    def json(self) -> dict:
        return self._data

    def raise_for_status(self) -> None:
        pass


class _HttpClient:
    """Fake httpx.AsyncClient that records each request with the client's and request's settings merged."""

    def __init__(self, requests: list, login_response: dict, **client_kwargs) -> None:
        self._requests = requests
        self._login_response = login_response
        self._client_kwargs = client_kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def _record(self, url: str, kwargs: dict) -> None:
        params = {**self._client_kwargs.get("params", {}), **kwargs.get("params", {})}
        headers = {**self._client_kwargs.get("headers", {}), **kwargs.get("headers", {})}
        self._requests.append((url, params, headers))

    async def get(self, url: str, **kwargs) -> _Response:
        self._record(url, kwargs)
        return _Response({"error_code": "0"})

    async def post(self, url: str, **kwargs) -> _Response:
        self._record(url, kwargs)
        if url.endswith("/user/login.json"):
            return _Response(self._login_response)
        if url.endswith(("/device/deviceList.json", "/device/getMyAcceptDeviceShareDataList.json")):
            return _Response({"error_code": "0", "object_result": []})
        if url.endswith("/deviceInfo/getDeviceBaseInfo.json"):
            return _Response({"error_code": "0", "object_result": {}})
        if url.endswith(("/deviceInfo/getDeviceDetailV3", "/deviceInfo/paramListV3")):
            return _Response({"errorCode": 200, "objectResult": []})
        return _Response({"error_code": "0"})


_LOGIN_OK = {"error_code": "0", "error_msg": "", "object_result": {"user_id": 1, "x-token": "token"}}


class LanguageTest(unittest.IsolatedAsyncioTestCase):
    def _patch_http(self, requests: list, login_response: dict = _LOGIN_OK):
        return patch(
            "ecohome.client.httpx.AsyncClient",
            side_effect=lambda **kwargs: _HttpClient(requests, login_response, **kwargs),
        )

    async def _requests_for_language(self, **login_kwargs) -> list:
        requests: list = []
        with self._patch_http(requests):
            client = await AsyncEcoHomeClient.login("user", "password", save_credentials=False, **login_kwargs)
            await client.is_logged_in()
            await client.list_all_devices()
            await client.get_device_base_info("device")
            await client.get_device_detail("device")
            await client.get_param_list("device", 0)
            await client.update_switch_state("device", "address", True)
            await client.set_value("device", "address", 20)
            await client.logout()
        return requests

    def _assert_requests(self, requests: list, lang: str, accept_language: str) -> None:
        login, *others = requests
        self.assertTrue(login[0].endswith("/user/login.json"))
        self.assertEqual(login[1], {"lang": "en_US"})
        self.assertEqual(login[2]["Accept-Language"], "en-US,en;q=0.9")

        self.assertEqual(len(others), 9)
        for url, params, headers in others:
            with self.subTest(url=url):
                self.assertEqual(params, {"lang": lang})
                self.assertEqual(headers["Accept-Language"], accept_language)
                self.assertEqual(headers["x-token"], "token")

    async def test_defaults_to_dutch(self) -> None:
        requests = await self._requests_for_language()
        self._assert_requests(requests, "nl_NL", "nl-NL,nl;q=0.9")

    async def test_language_can_be_overridden(self) -> None:
        requests = await self._requests_for_language(language="en-GB")
        self._assert_requests(requests, "en_US", "en-US,en;q=0.9")

    async def test_wrong_password_is_recognized_in_any_language(self) -> None:
        requests: list = []
        wrong_password = {"error_code": "-1", "error_msg": "Error username or password"}
        with self._patch_http(requests, wrong_password):
            with self.assertRaises(AuthenticationFailedError):
                await AsyncEcoHomeClient.login("user", "password", save_credentials=False, language="fr_FR")

    def test_api_language(self) -> None:
        cases = {
            "nl_NL": "nl_NL",
            "en_US": "en_US",
            "en": "en_US",
            "en-GB": "en_US",
            "EN_us": "en_US",
            "fr": "fr_FR",
            "pt-BR": "pt_PT",
            "zh-Hant": "zh_CN",
            "ja_JP": "nl_NL",
            "": "nl_NL",
        }
        for language, expected in cases.items():
            with self.subTest(language=language):
                self.assertEqual(_api_language(language), expected)


if __name__ == "__main__":
    unittest.main()
