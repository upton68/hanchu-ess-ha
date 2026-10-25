"""Constants for Hanchuess integration."""
import os

DOMAIN = "hanchuess"
PLATFORMS = ["sensor", "number", "switch", "select", "time", "button"]
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
DEFAULT_REALTIME_INTERVAL = 60        # seconds
DEFAULT_STATISTICS_INTERVAL = 300     # seconds
DEFAULT_BATTERY_INTERVAL = 600        # seconds
DEFAULT_FAST_CHARGE_DURATION = 60     # minutes
