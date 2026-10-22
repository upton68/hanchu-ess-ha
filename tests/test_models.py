"""Tests for inverter model identification (models.py)."""
from types import SimpleNamespace

from custom_components.hanchuess.models import (
    DEFAULT_MODEL_NAME,
    INVERTER_MODELS,
    apply_model_power_limits,
    inverter_model_name,
    lookup_inverter_model,
)


def _limits(chg=5000, dschg=5000):
    return {
        "CHG_PWR_LMT": {"min": 0, "max": chg},
        "DSCHG_PWR_LMT": {"min": 0, "max": dschg},
        "CHG_BAT_SOC_LMT": {"min": 50, "max": 100},
    }


def test_table_covers_every_console_code():
    assert sorted(INVERTER_MODELS) == list(range(1, 33))


def test_lookup_accepts_string_and_int_codes():
    assert lookup_inverter_model("4").name == "HESS-HY-S-5.0K"
    assert lookup_inverter_model(4).name == "HESS-HY-S-5.0K"
    assert lookup_inverter_model(" 30 ").name == "HESS-HY-S-7.0K"


def test_lookup_unknown_or_bad_values_return_none():
    for value in (None, "", "abc", "0", "99", True, [], {}):
        assert lookup_inverter_model(value) is None


def test_codes_are_not_in_size_order():
    # 7/8/10 kW single-phase were appended as 30-32, so an ordinal guess fails.
    assert lookup_inverter_model(6).name == "HESS-HY-T-05K"
    assert [lookup_inverter_model(c).name for c in (30, 31, 32)] == [
        "HESS-HY-S-7.0K",
        "HESS-HY-S-8.0K",
        "HESS-HY-S-10.0K",
    ]


def test_single_phase_3_to_6k_battery_capped_at_5000():
    for code, ac in ((1, 3000), (2, 3680), (3, 4000), (4, 5000), (5, 6000)):
        model = lookup_inverter_model(code)
        assert model.ac_rating_w == ac
        assert model.battery_max_w == 5000


def test_larger_models_battery_max_equals_ac():
    for code in list(range(6, 28)) + [30, 31, 32]:
        model = INVERTER_MODELS[code]
        assert model.battery_max_w == model.ac_rating_w, model.name


def test_48v_models_have_no_battery_max():
    assert INVERTER_MODELS[28].battery_max_w is None
    assert INVERTER_MODELS[29].battery_max_w is None


def test_apply_limits_5k_matches_menu_and_reports_nothing():
    limits = _limits()
    changed = apply_model_power_limits(limits, lookup_inverter_model(4))
    assert changed == []
    assert limits["CHG_PWR_LMT"]["max"] == 5000
    assert limits["DSCHG_PWR_LMT"]["max"] == 5000


def test_apply_limits_10k_raises_menu_cap_and_reports_it():
    limits = _limits()
    changed = apply_model_power_limits(limits, lookup_inverter_model(32))
    assert limits["CHG_PWR_LMT"]["max"] == 10000
    assert limits["DSCHG_PWR_LMT"]["max"] == 10000
    assert changed == [
        ("CHG_PWR_LMT", 5000.0, 10000.0),
        ("DSCHG_PWR_LMT", 5000.0, 10000.0),
    ]
    # SOC limits are never touched
    assert limits["CHG_BAT_SOC_LMT"] == {"min": 50, "max": 100}


def test_apply_limits_6k_single_phase_stays_at_5000():
    limits = _limits(chg=6000, dschg=6000)
    apply_model_power_limits(limits, lookup_inverter_model(5))
    assert limits["CHG_PWR_LMT"]["max"] == 5000
    assert limits["DSCHG_PWR_LMT"]["max"] == 5000


def test_apply_limits_unknown_or_unstated_keeps_menu():
    for model in (None, INVERTER_MODELS[28]):
        limits = _limits(chg=4000, dschg=4500)
        assert apply_model_power_limits(limits, model) == []
        assert limits["CHG_PWR_LMT"]["max"] == 4000
        assert limits["DSCHG_PWR_LMT"]["max"] == 4500


def test_inverter_model_name_falls_back_safely():
    assert inverter_model_name(SimpleNamespace(data={})) == DEFAULT_MODEL_NAME
    entry = SimpleNamespace(runtime_data=SimpleNamespace(inverter_model=None))
    assert inverter_model_name(entry) == DEFAULT_MODEL_NAME
    entry.runtime_data.inverter_model = lookup_inverter_model(4)
    assert inverter_model_name(entry) == "HESS-HY-S-5.0K"


# --- Battery packs ---------------------------------------------------------

from custom_components.hanchuess.models import (  # noqa: E402
    BATTERY_MODELS,
    DEFAULT_BATTERY_MODEL_NAME,
    battery_model_name,
    lookup_battery_model,
)


def test_battery_lookup_uses_string_codes_with_variants():
    assert lookup_battery_model("3").name == "Home-ESS-LV-9.4K"
    assert lookup_battery_model("3_1").name == "Home-ESS-LV-9.4K-H"
    assert lookup_battery_model(" 8_2 ").name == "HOME-ESS-LV-5.12K-M"
    assert lookup_battery_model(1).name == "Home-ESS-LV-3.2K"


def test_battery_lookup_unknown_returns_none():
    for value in (None, "", "2", "3_9", True):
        assert lookup_battery_model(value) is None


def test_battery_heated_known_only_for_9_4k_pair():
    assert lookup_battery_model("3_1").heated is True
    assert lookup_battery_model("3").heated is False
    others = [m for code, m in BATTERY_MODELS.items() if code not in ("3", "3_1")]
    assert all(m.heated is None for m in others)


def test_battery_voltage_class_from_name():
    assert lookup_battery_model("6").high_voltage is True  # Home-ESS-HV-5.3K
    assert lookup_battery_model("7").high_voltage is True  # CESS-HV-9.4K
    assert lookup_battery_model("3_1").high_voltage is False


def test_battery_model_name_falls_back():
    assert battery_model_name({"devModel": "3_1"}) == "Home-ESS-LV-9.4K-H"
    assert battery_model_name({"devModel": "99"}) == DEFAULT_BATTERY_MODEL_NAME
    assert battery_model_name(None) == DEFAULT_BATTERY_MODEL_NAME


def test_battery_model_sensor_values_and_attributes():
    from custom_components.hanchuess.sensor import BatteryModelSensor

    coordinator = SimpleNamespace(
        data={
            "B1": {"devModel": "3_1", "softwareVer": "2.0.6|T37"},
            "B2": {"devModel": "42"},
            "B3": {},
        }
    )
    entry = SimpleNamespace(
        data={"sn": "SN1"},
        runtime_data=SimpleNamespace(inverter_device_id="dev1"),
    )
    s1 = BatteryModelSensor(coordinator, entry, "B1")
    assert s1.native_value == "Home-ESS-LV-9.4K-H"
    assert s1.extra_state_attributes == {
        "dev_model": "3_1",
        "software_version": "2.0.6|T37",
        "voltage_class": "LV",
        "heated": True,
    }
    assert s1.device_info["model"] == "Home-ESS-LV-9.4K-H"
    assert s1.unique_id == "B1_battery_model"
    assert BatteryModelSensor(coordinator, entry, "B2").native_value == "Unknown (42)"
    assert BatteryModelSensor(coordinator, entry, "B3").native_value is None
