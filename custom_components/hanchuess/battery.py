"""Helpers for Hanchuess battery discovery."""


def extract_battery_serials(station_detail: dict) -> list[str]:
    """Return battery serials from a station detail payload."""
    serials = []
    for item in station_detail.get("data", {}).get("bmsList", []):
        sn = item.get("sn")
        if sn:
            serials.append(sn)
    return serials


def merge_battery_serials(existing_serials: list[str], station_detail: dict) -> list[str]:
    """Merge stored battery serials with the latest station detail payload."""
    merged = []
    seen = set()
    for serial in [*existing_serials, *extract_battery_serials(station_detail)]:
        if serial and serial not in seen:
            seen.add(serial)
            merged.append(serial)
    return merged


# --- Battery-only stations (Hanchu batteries with a third-party inverter) ------

HANCHU_PCS_BRAND = "hanchuess"
HANCHU_PCS_BRAND_CODE = "1"


def _station_data(station_detail: dict | None) -> dict:
    return (station_detail or {}).get("data") or {}


def is_hanchu_inverter(pcs: dict) -> bool:
    """True for a Hanchu inverter in a station's pcsList.

    Third-party inverters (e.g. LuxPower) can appear in pcsList as placeholders
    with an empty brand and a different brand code, so "any inverter listed"
    is not enough.
    """
    brand = str(pcs.get("pcsBrand") or "").strip().lower()
    code = str(pcs.get("pcsBrandCode") or "").strip()
    return brand == HANCHU_PCS_BRAND or code == HANCHU_PCS_BRAND_CODE


def has_hanchu_inverter(station_detail: dict | None) -> bool:
    return any(is_hanchu_inverter(p) for p in _station_data(station_detail).get("pcsList") or [])


def battery_only_serials(station_detail: dict | None) -> list[str]:
    """Battery serials if the station has batteries but no Hanchu inverter."""
    if not station_detail or has_hanchu_inverter(station_detail):
        return []
    return extract_battery_serials(station_detail)


def battery_dev_ids(station_detail: dict | None) -> dict[str, str]:
    """Map battery sn -> devId from a station's bmsList.

    The battery detail call takes a device ID. For most batteries devId equals
    sn, but it may not for every battery (e.g. warranty replacements).
    """
    ids = {}
    for item in _station_data(station_detail).get("bmsList") or []:
        sn = item.get("sn")
        dev_id = item.get("devId")
        if sn and dev_id:
            ids[sn] = dev_id
    return ids


def station_battery_values(station_detail: dict | None) -> dict[str, dict]:
    """Per-battery values the station list carries (SOC, SOH, model, online)."""
    values = {}
    for item in _station_data(station_detail).get("bmsList") or []:
        sn = item.get("sn")
        if not sn:
            continue
        values[sn] = {
            k: item[k]
            for k in ("socPack", "sohPack", "devModel", "onlineStatus", "softwareVer")
            if item.get(k) is not None
        }
    return values


def _short(value) -> str:
    text = str(value or "")
    return f"{text[:5]}…" if len(text) > 5 else text


def station_summary(station_detail: dict | None) -> dict:
    """A redacted outline of a station for logs and diagnostics.

    No owner, email, address, coordinates or station ID; serials shortened.
    """
    data = _station_data(station_detail)
    return {
        "inverters": [
            {
                "hanchu": is_hanchu_inverter(p),
                "brand": p.get("pcsBrand") or "",
                "brand_code": p.get("pcsBrandCode"),
                "dev_type": p.get("devType"),
                "status": p.get("devStatus"),
                "online": p.get("onlineStatus"),
            }
            for p in data.get("pcsList") or []
        ],
        "batteries": [
            {
                "sn": _short(b.get("sn")),
                "dev_id_differs": bool(b.get("devId")) and b.get("devId") != b.get("sn"),
                "logger": _short(b.get("dtuSn")),
                "adr": b.get("adr"),
                "dev_model": b.get("devModel"),
                "online": b.get("onlineStatus"),
                "soc": b.get("socPack"),
            }
            for b in data.get("bmsList") or []
        ],
    }
