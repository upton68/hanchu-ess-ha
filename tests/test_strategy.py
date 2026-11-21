"""Merge and decode rules for the Weather Optimize / Octopus records (#72)."""
import copy

from custom_components.hanchuess.strategy import (
    PRIORITY_KEY,
    WEATHER_BANDS,
    changes_applied,
    decode_flag,
    decode_hhmm,
    decode_number,
    decode_option,
    encode_hhmm,
    merge_record,
    record_value,
    save_succeeded,
    slots_key,
    soc_key,
    strategy_record,
    OCTOPUS_TYPES,
)

SN = "SN1"


def weather_record():
    return {
        "id": 27482,
        "sn": SN,
        "weatherOpen": "1",
        "weatherChargeTimeStart": "23:30",
        "weatherChargeTimeEnd": "05:30",
        PRIORITY_KEY: "2",
        "someFutureField": {"keep": True},
        "weathers": [
            {"code": "100", "cloud": "", "soc": "40"},
            {"code": "101", "cloud": "11-25", "soc": "50"},
            {"code": "101", "cloud": "26-50", "soc": "60"},
            {"code": "999", "cloud": "", "soc": "70", "label": "New category"},
        ],
    }


def octopus_record():
    return {
        "id": 31000,
        "sn": SN,
        "octopusOpen": "1",
        "octopusType": "1",
        "octopusPriceEnable": "1",
        "octopusDischargeEnable": "0",
        "octopusPrice": "12.5",
        "octopusDischargePrice": "30",
        PRIORITY_KEY: "2",
        "belongingCountryCode": "GB",
        "postalCode": "AB1 2CD",
        "timezone": "Europe/London",
        "octopuses": [
            {"timeStr": "00:00-08:00", "num": "4"},
            {"timeStr": "12:00-19:00", "num": "2"},
        ],
    }


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

def test_strategy_record_reads_data():
    assert strategy_record({"code": 200, "success": True, "data": {"id": 1}}) == {"id": 1}


def test_strategy_record_none_saved_yet_is_empty():
    assert strategy_record({"code": 200, "success": True, "data": None}) == {}


def test_strategy_record_failures_are_none():
    assert strategy_record({}) is None
    assert strategy_record(None) is None
    assert strategy_record({"code": 100, "success": False, "msg": "x"}) is None
    assert strategy_record({"_token_expired": True}) is None
    assert strategy_record({"code": 200, "data": ["not", "a", "record"]}) is None


def test_save_succeeded():
    assert save_succeeded({"code": 200})
    assert save_succeeded({"success": True})
    assert not save_succeeded({"code": 100, "success": False})
    assert not save_succeeded(None)
    assert not save_succeeded({})


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------

def test_merge_round_trips_everything_not_staged():
    record = weather_record()
    original = copy.deepcopy(record)
    payload = merge_record(record, {"weatherOpen": "0"}, SN)

    assert record == original  # input untouched
    assert payload["weatherOpen"] == "0"
    assert payload["id"] == 27482  # id of the record just read
    assert payload["confirm"] == "0"
    assert payload["sn"] == SN
    assert payload["someFutureField"] == {"keep": True}
    assert payload["weathers"] == original["weathers"]  # incl. unknown code 999
    for key in ("weatherChargeTimeStart", "weatherChargeTimeEnd", PRIORITY_KEY):
        assert payload[key] == original[key]


def test_merge_soc_changes_only_that_band_and_keeps_string_format():
    payload = merge_record(weather_record(), {soc_key("few_clouds"): 85}, SN)
    by_cloud = {(w["code"], w["cloud"]): w["soc"] for w in payload["weathers"]}
    assert by_cloud[("101", "11-25")] == "85"
    assert by_cloud[("100", "")] == "40"
    assert by_cloud[("101", "26-50")] == "60"
    assert by_cloud[("999", "")] == "70"
    assert len(payload["weathers"]) == 4


def test_merge_soc_matches_numeric_codes_and_missing_cloud():
    record = {"weathers": [{"code": 305, "soc": "20"}]}
    payload = merge_record(record, {soc_key("light_rain"): 30}, SN)
    assert payload["weathers"] == [{"code": 305, "soc": "30"}]


def test_merge_soc_adds_a_missing_band():
    record = {"weathers": [{"code": 100, "cloud": "", "soc": "40"}]}
    payload = merge_record(record, {soc_key("heavy_snow"): 90}, SN)
    assert payload["weathers"][1] == {"code": 400, "cloud": "", "soc": "90"}


def test_merge_into_empty_record():
    payload = merge_record({}, {"weatherOpen": "1", soc_key("sunny"): 50}, SN)
    assert payload == {
        "weatherOpen": "1",
        "weathers": [{"code": "100", "cloud": "", "soc": "50"}],
        "sn": SN,
        "confirm": "0",
    }


def test_price_mode_slot_counts_are_kept():
    """Changing a price (Price mode) leaves the Point-mode slot counts alone."""
    record = octopus_record()
    payload = merge_record(record, {"octopusPrice": 9.99}, SN)
    assert payload["octopusPrice"] == "9.99"
    assert payload["octopuses"] == record["octopuses"]
    assert payload["octopusPriceEnable"] == "1"
    assert payload["octopusDischargeEnable"] == "0"


def test_point_mode_prices_are_kept():
    """Changing slot counts (Point mode) leaves the Price-mode thresholds alone."""
    record = {**octopus_record(), "octopusType": "2"}
    payload = merge_record(record, {slots_key("12:00-19:00"): 6}, SN)
    assert payload["octopuses"] == [
        {"timeStr": "00:00-08:00", "num": "4"},
        {"timeStr": "12:00-19:00", "num": "6"},
    ]
    assert payload["octopusPrice"] == "12.5"
    assert payload["octopusDischargePrice"] == "30"
    assert payload["octopusType"] == "2"


def test_numeric_fields_keep_numeric_format():
    record = {"octopusPrice": 12, "octopuses": [{"timeStr": "00:00-08:00", "num": 4}]}
    payload = merge_record(
        record, {"octopusPrice": 15.25, slots_key("00:00-08:00"): 7.0}, SN
    )
    assert payload["octopusPrice"] == 15.25
    assert payload["octopuses"][0]["num"] == 7
    payload = merge_record(record, {"octopusPrice": 15.0}, SN)
    assert payload["octopusPrice"] == 15


def test_whole_price_written_without_decimals_in_string_field():
    payload = merge_record(octopus_record(), {"octopusDischargePrice": 25.0}, SN)
    assert payload["octopusDischargePrice"] == "25"


def test_missing_window_is_added():
    payload = merge_record({"octopuses": []}, {slots_key("00:00-08:00"): 3}, SN)
    assert payload["octopuses"] == [{"timeStr": "00:00-08:00", "num": 3}]


def test_changes_applied():
    record = octopus_record()
    staged = {"octopusPrice": 9.99, PRIORITY_KEY: "1"}
    assert not changes_applied(record, staged, SN)
    saved = {**merge_record(record, staged, SN), "id": 31001}
    saved.pop("confirm")
    assert changes_applied(saved, staged, SN)
    assert not changes_applied(None, staged, SN)


# ---------------------------------------------------------------------------
# Reading values for entities
# ---------------------------------------------------------------------------

def test_record_value_for_fields_bands_and_windows():
    weather = weather_record()
    octopus = octopus_record()
    assert record_value(weather, "weatherOpen") == "1"
    assert record_value(weather, soc_key("partly_cloudy")) == "60"
    assert record_value(weather, soc_key("heavy_rain")) is None
    assert record_value(octopus, slots_key("00:00-08:00")) == "4"
    assert record_value(None, "weatherOpen") is None
    assert record_value(None, slots_key("00:00-08:00")) is None


def test_missing_octopus_window_reads_as_zero():
    """After a Price-mode save in the app the record has no octopuses[]."""
    record = {k: v for k, v in octopus_record().items() if k != "octopuses"}
    assert record_value(record, slots_key("00:00-08:00")) == 0
    assert record_value(record, slots_key("12:00-19:00")) == 0
    only_morning = {"octopuses": [{"timeStr": "00:00-08:00", "num": "4"}]}
    assert record_value(only_morning, slots_key("00:00-08:00")) == "4"
    assert record_value(only_morning, slots_key("12:00-19:00")) == 0


def test_setting_a_missing_window_keeps_the_existing_one():
    record = {"id": 1, "octopuses": [{"timeStr": "00:00-08:00", "num": "4"}]}
    payload = merge_record(record, {slots_key("12:00-19:00"): 3}, SN)
    assert payload["octopuses"] == [
        {"timeStr": "00:00-08:00", "num": "4"},
        {"timeStr": "12:00-19:00", "num": 3},
    ]


def test_weather_bands_are_unique():
    assert len({(b.code, b.cloud) for b in WEATHER_BANDS}) == 11
    assert len({b.key for b in WEATHER_BANDS}) == 11


def test_decoders():
    assert decode_flag("1") is True
    assert decode_flag(0) is False
    assert decode_flag(None) is None
    assert decode_number("12.5") == 12.5
    assert decode_number("x") is None
    assert decode_hhmm("05:30") == (5, 30)
    assert decode_hhmm("24:00") == (0, 0)
    assert decode_hhmm("25:00") is None
    assert decode_hhmm(None) is None
    assert encode_hhmm(5, 3) == "05:03"
    assert decode_option("2", OCTOPUS_TYPES) == "Point settings"
    assert decode_option(1, OCTOPUS_TYPES) == "Price settings"
    assert decode_option("9", OCTOPUS_TYPES) is None


def test_has_settings():
    from custom_components.hanchuess.strategy import has_settings

    assert has_settings({"id": 27482})
    assert has_settings({"id": "27482"})
    assert not has_settings({})
    assert not has_settings({"id": None, "weatherOpen": "1"})
    assert not has_settings({"id": ""})
    assert not has_settings(None)
