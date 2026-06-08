"""Constants for Hanchuess integration."""
import os

DOMAIN = "hanchuess"
PLATFORMS = ["sensor", "number", "switch", "select"]
BASE_URL = os.environ.get("HANCHUESS_URL", "https://iess3.hanchuess.com")
