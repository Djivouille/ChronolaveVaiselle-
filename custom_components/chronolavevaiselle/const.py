import json
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

DOMAIN = "chronolavevaiselle"

_MANIFEST_PATH = Path(__file__).parent / "manifest.json"
with open(_MANIFEST_PATH, encoding="utf-8") as _f:
    INTEGRATION_VERSION: Final[str] = json.load(_f).get("version", "0.0.0")

URL_BASE: Final[str] = f"/{DOMAIN}"

JSMODULES: Final[list[dict[str, str]]] = [
    {
        "name": "Carte ChronolaveVaiselle",
        "filename": "chronolavevaiselle-card.js",
        "version": INTEGRATION_VERSION,
    },
]

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONF_DURATION = "duration"
CONF_CYCLE_SENSOR = "cycle_sensor"
CONF_PERSONS = "persons"
CONF_COOLDOWN = "cooldown"

DEFAULT_DURATION = 120
DEFAULT_NAME = "Lave-vaisselle"
DEFAULT_PERSONS = "Chloe, Axel, Joelle, Jv"
DEFAULT_COOLDOWN = 6

SERVICE_START_CYCLE = "start_cycle"
SERVICE_EMPTY = "empty"
ATTR_DURATION = "duration"
ATTR_PERSON = "person"

EVENT_CYCLE_FINISHED = f"{DOMAIN}_cycle_finished"
EVENT_CYCLE_ENDED = f"{DOMAIN}_cycle_ended"
EVENT_EMPTIED = f"{DOMAIN}_emptied"
EVENT_EMPTY_DENIED = f"{DOMAIN}_empty_denied"
