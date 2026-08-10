"""API client for Hanchuess."""
import asyncio
import logging
import time
import aiohttp
import async_timeout

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .crypto import _encrypt_payload

_LOGGER = logging.getLogger(__name__)

TOKEN_REFRESH_DAYS = 25
TOKEN_REFRESH_SECONDS = TOKEN_REFRESH_DAYS * 24 * 3600


class ReauthRequired(Exception):
    """Raised when refresh_token returns 90076, requiring re-authentication."""


class HanchuessApiClient:
    """Hanchuess API client."""

    def __init__(self, hass, domain: str, token: str = None):
        self._hass = hass
        self._domain = domain.rstrip("/")
        self._token = token
        self._token_time = time.time() if token else 0
        self._refresh_lock = asyncio.Lock()
        self._reauth_triggered = False
        self._last_refresh_attempt = 0

    @property
    def token(self) -> str:
        return self._token

    def _headers(self, language: str = "en") -> dict:
        headers = {
            "Content-Type": "application/json",
            "appPlat": "ha",
        }
        if self._token:
            headers["access-token"] = self._token
        # Server locale handling: normalize zh variants, otherwise default to en.
        normalized = "en"
        if isinstance(language, str) and language.lower().startswith("zh"):
            normalized = "zh"
        headers["locale"] = normalized
        return headers

    async def _request(
        self,
        path: str,
        data: dict | str | bytes,
        language: str = "en",
        retries: int = 3,
        send_as_json: bool = True,
    ) -> dict:
        url = f"{self._domain}{path}"
        _LOGGER.debug("[HANCHUESS] request: %s token=%s", url, "yes" if self._token else "no")
        last_err = None
        for attempt in range(1, retries + 1):
            try:
                headers = self._headers(language)
                request_kwargs = {"json": data}
                if not send_as_json:
                    headers.pop("Content-Type", None)
                    request_kwargs = {"data": data}

                async with async_timeout.timeout(15):
                    session = async_get_clientsession(self._hass)
                    async with session.post(
                        url, headers=headers, **request_kwargs
                    ) as response:
                        result = await response.json(content_type=None)
                        _LOGGER.debug("[HANCHUESS] response: %s status=%s body=%s", path, response.status, str(result)[:500])
                        if response.status == 401:
                            return {"success": False, "code": 401}
                        if response.status == 200:
                            if result.get("code") == 401:
                                return {"success": False, "code": 401}
                            return result
                        _LOGGER.error("[HANCHUESS] unexpected status: %s %s", response.status, str(result)[:200])
            except TimeoutError:
                last_err = "timeout"
                _LOGGER.warning("[HANCHUESS] Request timeout (attempt %s/%s): %s", attempt, retries, url)
            except Exception as err:
                last_err = str(err)
                _LOGGER.warning("[HANCHUESS] Request error (attempt %s/%s): %s - %s", attempt, retries, url, err)

            if attempt < retries:
                await asyncio.sleep(2 * attempt)

        _LOGGER.error("[HANCHUESS] Request failed after %s attempts: %s (%s)", retries, url, last_err)
        return None

    async def async_login(self, account: str, password: str) -> str | None:
        result = await self._request(
            "/gateway/identify/auth/token",
            {"account": account, "pwd": password},
        )
        _LOGGER.info("[HANCHUESS] login: %s", "success" if result and result.get("success") else "failed")
        if result and result.get("success"):
            self._token = result.get("data")
            self._token_time = time.time()
            return self._token
        return None

    async def async_refresh_token(self, force: bool = False) -> str | None:
        """Refresh token with lock to prevent concurrent refresh calls."""
        async with self._refresh_lock:
            # Proactive: skip if not yet due (another coroutine may have refreshed)
            if not force and not self.should_refresh_token():
                return self._token
            # Reactive: skip if token was already refreshed/attempted recently
            if force and (time.time() - self._last_refresh_attempt) < 30:
                return self._token if not self.should_refresh_token() else None
            self._last_refresh_attempt = time.time()
            result = await self._request(
                "/gateway/identify/auth/token/refresh",
                {"token": self._token},
            )
            if result and result.get("success"):
                self._token = result.get("data")
                self._token_time = time.time()
                return self._token
            if result and result.get("code") == 100:
                _LOGGER.warning("[HANCHUESS] refresh_token failed: code=100, msg=%s", result.get("msg"))
                raise ReauthRequired()
            return None

    def should_refresh_token(self) -> bool:
        return (time.time() - self._token_time) >= TOKEN_REFRESH_SECONDS

    async def async_get_devices(self) -> list:
        result = await self._request(
            "/gateway/app/ha/getDeviceList", {}
        )
        if result and result.get("success"):
            devices = result.get("data", [])
            _LOGGER.info("[HANCHUESS] getDeviceList: %d devices", len(devices))
            return devices
        _LOGGER.info("[HANCHUESS] getDeviceList: 0 devices")
        return []

    async def async_get_station_detail(self, station_id: str, language: str = "en") -> dict:
        payload = _encrypt_payload({"stationId": station_id})
        result = await self._request(
            "/gateway/platform/station/detail",
            payload,
            language=language,
            send_as_json=False,
        )
        return result or {}

    async def async_get_battery_data(self, device_id: str, language: str = "en") -> dict:
        payload = _encrypt_payload({"deviceId": device_id})
        result = await self._request(
            "/gateway/platform/bmsInfo/queryBatteryDataDivisions",
            payload,
            language=language,
            send_as_json=False,
        )
        return result or {}

    async def async_get_device_status(self, sn: str, language: str = "en") -> dict | None:
        result = await self._request(
            "/gateway/app/ha/getDeviceStatus",
            {"sn": sn},
            language=language,
        )
        if result and result.get("code") == 401:
            return {"_token_expired": True}
        if result and result.get("success"):
            return result.get("data", {})
        return {}

    async def async_get_device_statistics(self, sn: str, language: str = "en") -> dict | None:
        result = await self._request(
            "/gateway/app/ha/getDeviceStatistics",
            {"sn": sn},
            language=language,
        )
        if result and result.get("code") == 401:
            return {"_token_expired": True}
        if result and result.get("success"):
            return result.get("data", {})
        return {}

    async def async_get_menu(self, sn: str, language: str = "en") -> dict:
        result = await self._request(
            "/gateway/app/ha/menu",
            {"sn": sn},
            language=language,
        )
        if result and result.get("code") == 200:
            return result
        return {}

    async def async_iot_get(self, sn: str, dev_type: str, keys: list) -> dict:
        result = await self._request(
            "/gateway/app/ha/iotGet",
            {"sn": sn, "devType": dev_type, "keys": keys},
        )
        if result and result.get("success"):
            return result.get("data", {})
        return {}

    async def async_fast_charge_discharge(self, sn: str, act: int, duration: int) -> dict:
        result = await self._request(
            "/gateway/app/ha/fastChargeDischarge",
            {"sn": sn, "act": act, "duration": duration},
        )
        _LOGGER.debug("[HANCHUESS] fastChargeDischarge result: %s", result)
        if not result:
            return {"success": False, "msg": "Request failed"}
        if result.get("code") == 401:
            return {"success": False, "msg": "token_expired"}
        if result.get("code") == 100:
            return {"success": False, "msg": result.get("msg", "Device error")}
        if result.get("success") or result.get("code") == 200:
            return {"success": True, "data": result.get("data", {})}
        return {"success": False, "msg": result.get("msg", "Unknown error")}

    async def async_device_control(self, sn: str, dev_type: str, value: dict) -> dict:
        result = await self._request(
            "/gateway/app/ha/iotSet",
            {"sn": sn, "devType": dev_type, "value": value},
        )
        if result and result.get("code") == 401:
            return {"success": False, "msg": "token_expired"}
        if result and result.get("success"):
            return {"success": True, "data": result.get("data", {})}
        return {"success": False, "msg": result.get("msg", "Unknown error") if result else "Request failed"}
