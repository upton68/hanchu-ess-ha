"""API client for Hanchuess."""
import asyncio
import logging
import time
import aiohttp
import async_timeout

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .crypto import _encrypt_payload

MINUTE_CHART_MAX_COUNT = 1440


def _mark_token_expired(result: dict | None) -> dict | None:
    """Turn a 401 into the {"_token_expired": True} marker coordinators use."""
    if result and result.get("code") == 401:
        return {"_token_expired": True}
    return result

from homeassistant.util import dt as dt_util

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
        self._account: str | None = None
        self._password: str | None = None
        # Which minute-chart header set the cloud accepted (None = not yet known).
        self._chart_headers_idx: int | None = None

    @property
    def token(self) -> str:
        return self._token

    @property
    def has_credentials(self) -> bool:
        return bool(self._account and self._password)

    def set_credentials(self, account: str | None, password: str | None) -> None:
        """Hold the account credentials so a rejected refresh can log in again."""
        self._account = account or None
        self._password = password or None

    def set_token(self, token: str) -> None:
        """Adopt a freshly issued token and reset auth-failure state."""
        self._token = token
        self._token_time = time.time()
        self._reauth_triggered = False
        self._last_refresh_attempt = 0

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
        extra_headers: dict | None = None,
    ) -> dict:
        url = f"{self._domain}{path}"
        _LOGGER.debug("[HANCHUESS] request: %s token=%s", url, "yes" if self._token else "no")
        last_err = None
        for attempt in range(1, retries + 1):
            try:
                headers = self._headers(language)
                if extra_headers:
                    headers.update(extra_headers)
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
            self.set_credentials(account, password)
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
                if self.has_credentials:
                    # The cloud rejected the refresh but the stored credentials may
                    # still be valid: log in again instead of asking the user.
                    _LOGGER.info("[HANCHUESS] Token refresh rejected, logging in again")
                    token = await self.async_login(self._account, self._password)
                    if token:
                        self._reauth_triggered = False
                        return token
                    _LOGGER.warning("[HANCHUESS] Automatic re-login failed, reauth required")
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

    async def async_get_stations(self, language: str = "en") -> list[dict]:
        """Stations on the account (station/queryList, paged)."""
        stations: list[dict] = []
        page = 1
        while True:
            result = await self._request(
                "/gateway/platform/station/queryList",
                _encrypt_payload({"current": page, "size": 100}),
                language=language,
                send_as_json=False,
            )
            data = (result or {}).get("data") or {}
            stations.extend(data.get("records") or [])
            try:
                pages = int(data.get("pages") or 1)
            except (TypeError, ValueError):
                pages = 1
            if not result or not result.get("success") or page >= pages:
                return stations
            page += 1

    async def async_get_station_detail(self, station_id: str, language: str = "en") -> dict:
        """Return station detail including bmsList.

        Hanchu deprecated /platform/station/detail in Nov 2026 ("This API has
        been deprecated."). /platform/homePage/stationInfo returns the same
        data.bmsList shape, so try it first and keep the old endpoint as a
        fallback.
        """
        result = None
        for path in (
            "/gateway/platform/homePage/stationInfo",
            "/gateway/platform/station/detail",
        ):
            payload = _encrypt_payload({"stationId": station_id})
            result = await self._request(
                path,
                payload,
                language=language,
                send_as_json=False,
            )
            if result and result.get("code") == 401:
                return {"_token_expired": True}
            if result and result.get("success"):
                return result
            _LOGGER.debug(
                "[HANCHUESS] %s did not return station detail: %s",
                path,
                result.get("msg") if result else None,
            )
        # Preserve the previous contract: return the last response (or {}) so
        # callers' existing error handling is unchanged.
        return result or {}

    async def async_get_battery_data(self, device_id: str, language: str = "en") -> dict:
        payload = _encrypt_payload({"deviceId": device_id})
        result = await self._request(
            "/gateway/platform/bmsInfo/queryBatteryDataDivisions",
            payload,
            language=language,
            send_as_json=False,
        )
        return _mark_token_expired(result) or {}

    async def async_get_battery_minute_chart(
        self, device_id: str, start_ms: int, end_ms: int, language: str = "en"
    ) -> dict:
        """A battery's minute samples between two times (bmsInfo/powerMinuteChart).

        Each sample carries vPack, iPack and dataTimeTs, among others. At most
        1440 samples come back per call. The range should run to the end of a
        local day, as the web console sends it.

        The cloud refuses this call (code 100) without the console's time zone
        headers, and may also want the console's appPlat. The header sets are
        tried in turn and the one that works is remembered.
        """
        payload = _encrypt_payload({
            "sn": device_id,
            "devType": "1",
            "maxCount": MINUTE_CHART_MAX_COUNT,
            "dataTimeTsStart": int(start_ms),
            "dataTimeTsEnd": int(end_ms),
        })
        variants = self._minute_chart_header_sets()
        order = list(range(len(variants)))
        known = getattr(self, "_chart_headers_idx", None)
        if known is not None:
            order.remove(known)
            order.insert(0, known)
        result = None
        for idx in order:
            result = await self._request(
                "/gateway/platform/bmsInfo/powerMinuteChart",
                payload,
                language=language,
                send_as_json=False,
                extra_headers=variants[idx],
            )
            if result and result.get("code") == 200:
                if known != idx:
                    _LOGGER.debug("[HANCHUESS] minute chart accepted header set %s", idx)
                self._chart_headers_idx = idx
                break
            if not result or result.get("code") == 401:
                break
        return _mark_token_expired(result) or {}

    def _minute_chart_header_sets(self) -> list[dict]:
        """Header sets for the minute chart, mirroring the web console."""
        hass = getattr(self, "_hass", None)
        tz_name = getattr(getattr(hass, "config", None), "time_zone", None)
        if not isinstance(tz_name, str) or not tz_name:
            tz_name = "UTC"
        try:
            offset = dt_util.now(dt_util.get_time_zone(tz_name)).utcoffset()
            minutes = int(offset.total_seconds() // 60) if offset else 0
        except Exception:  # noqa: BLE001 - unknown zone: fall back to UTC
            minutes = 0
        if minutes == 0:
            selected = "GMT"
        else:
            sign = "+" if minutes > 0 else "-"
            selected = f"GMT{sign}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"
        tz_headers = {"timezone": tz_name, "timeselected": selected}
        return [tz_headers, {**tz_headers, "appPlat": "iess"}]

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
