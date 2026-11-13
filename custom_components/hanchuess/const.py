"""Constants for Hanchuess integration."""
import os

DOMAIN = "hanchuess"
PLATFORMS = ["sensor", "number", "switch", "select", "time", "button"]
# Hanchu batteries with a third-party inverter: battery sensors only.
BATTERY_ONLY_PLATFORMS = ["sensor"]
MODE_BATTERY_ONLY = "battery_only"
BASE_URL = os.environ.get("HANCHUESS_URL", "https://iess3.hanchuess.com")
WEB_CONSOLE_URL = "https://iess3.hanchuess.com/login"

# AES-CBC key and IV used by the Hanchu gateway's encrypted payloads.
AES_IV = b"9z64Qr8mZH7Pg8d1"
AES_SECRET_KEY = b"9z64Qr8mZH7Pg8d1"

# Options flow keys + defaults
CONF_REALTIME_INTERVAL = "realtime_interval"
CONF_STATISTICS_INTERVAL = "statistics_interval"
CONF_BATTERY_INTERVAL = "battery_interval"
CONF_FAST_CHARGE_DURATION = "fast_charge_duration"
CONF_SCHEDULE_INTERVAL = "schedule_interval"
DEFAULT_REALTIME_INTERVAL = 60        # seconds
DEFAULT_STATISTICS_INTERVAL = 300     # seconds
DEFAULT_BATTERY_INTERVAL = 600        # seconds
# Battery-only stations: the batteries are the only data, so poll faster.
DEFAULT_BATTERY_ONLY_INTERVAL = 60    # seconds
MIN_BATTERY_ONLY_INTERVAL = 60        # seconds
DEFAULT_FAST_CHARGE_DURATION = 60     # minutes
DEFAULT_SCHEDULE_INTERVAL = 300       # seconds
MIN_SCHEDULE_INTERVAL = 60            # seconds

# Inverter settings polled for the Inverter Status sensor (work mode, the SOC
# limits that stop a scheduled charge/discharge, and the six slots).
SCHEDULE_KEYS = [
    "WORK_MODE_CMB",
    "DTU_AC_CHG_SOC_LMT",
    "DSCHG_BAT_SOC_LMT",
    "TCT_START_1", "TCT_END_1",
    "TCT_START_2", "TCT_END_2",
    "TCT_START_3", "TCT_END_3",
    "TDT_START_1", "TDT_END_1",
    "TDT_START_2", "TDT_END_2",
    "TDT_START_3", "TDT_END_3",
]
